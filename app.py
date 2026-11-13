"""
PUMA UNIVERSITY - STUDENT RESULT & EXAMINATION MANAGEMENT SYSTEM
Modernized, production-grade Flask 3.1 application.
"""

import os
import io
import csv
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file, Response
)
import qrcode
from PIL import Image as PILImage
import urllib.parse

import database
from utils.pdf_generator import generate_student_marksheet_pdf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "puma_university_super_secret_production_key_2026")
app.url_map.strict_slashes = False
app.config["SESSION_COOKIE_NAME"] = "puma_session_v3"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

class VercelPathMiddleware:
    """
    Normalizes WSGI environment for Vercel Serverless Functions.
    Vercel rewrites incoming requests to /api/index?__vercel_path=$1.
    This middleware:
      1. Extracts __vercel_path from QUERY_STRING to restore PATH_INFO
      2. Removes __vercel_path from QUERY_STRING so application request.args are pristine
      3. Resets SCRIPT_NAME to '' so url_for builds clean, canonical application URLs
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)

        target_path = None
        if "__vercel_path" in parsed:
            raw_vals = parsed.pop("__vercel_path")
            raw_path = raw_vals[0] if raw_vals else ""
            if raw_path:
                target_path = raw_path if raw_path.startswith("/") else "/" + raw_path
            else:
                target_path = "/"

            # Clean internal routing param from query string
            filtered_query = [(k, v) for k, vs in parsed.items() for v in vs]
            environ["QUERY_STRING"] = urllib.parse.urlencode(filtered_query)

        if not target_path:
            path_info = environ.get("PATH_INFO", "")
            if path_info in ("/api/index", "/api/index/", ""):
                target_path = "/"
            elif path_info.startswith("/api/index/"):
                sub = path_info[len("/api/index"):]
                target_path = sub if sub else "/"
            else:
                target_path = path_info

        environ["PATH_INFO"] = target_path
        environ["SCRIPT_NAME"] = ""

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Initialize database schema and migrations
database.init_db()

@app.context_processor
def inject_global_vars():
    from datetime import datetime
    now = datetime.now()
    return {
        "current_date": now.strftime("%B %d, %Y"),
        "current_year": now.year,
        "academic_session": f"{now.year - 1}-{now.year}" if now.month < 7 else f"{now.year}-{now.year + 1}"
    }

# ----------------- AUTHENTICATION HELPERS -----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session or session.get("role") != "admin":
            flash("Admin authentication required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session or session.get("role") != "student":
            flash("Student authentication required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- PUBLIC & AUTH ROUTES -----------------
def handle_login_request():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "admin").strip().lower()

        if not username or not password:
            flash("Username / Enrollment and Password are required.", "danger")
            return render_template("login.html")

        success, user, message = database.authenticate_user(username, password, role)

        if success:
            session["user"] = user
            session["role"] = role
            session["user_name"] = user.get("name", username)
            flash(f"Welcome back, {session['user_name']}!", "success")
            if role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))
        else:
            flash(message, "danger")
            return render_template("login.html")

    # GET request: always render clean login page with zero redirect
    return render_template("login.html")

@app.route("/", methods=["GET", "POST"])
@app.route("/api/index", methods=["GET", "POST"])
@app.route("/api/index/", methods=["GET", "POST"])
def home():
    return handle_login_request()

@app.route("/login", methods=["GET", "POST"])
def login():
    return handle_login_request()

@app.route("/logout")
def logout():
    user_name = session.get("user_name", "User")
    session.clear()
    flash(f"Signed out successfully. Goodbye, {user_name}!", "info")
    return redirect(url_for("home"))

# ----------------- ADMIN DASHBOARD -----------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = database.get_dashboard_analytics()
    ledger = database.get_all_results_ledger()
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        ledger=ledger[:10]  # Show recent 10 records on main dashboard
    )

# ----------------- DEPARTMENTS -----------------
@app.route("/departments")
@admin_required
def departments_page():
    departments = database.get_departments()
    return render_template("departments.html", departments=departments)

@app.route("/departments/add", methods=["POST"])
@app.route("/add_department", methods=["POST"])
@admin_required
def add_department():
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    if name:
        try:
            database.add_department(name, code)
            flash(f"Department '{name}' added successfully.", "success")
        except Exception as e:
            flash(f"Could not add department: {e}", "danger")
    else:
        flash("Department name is required.", "danger")
    return redirect(url_for("departments_page"))

@app.route("/departments/edit/<int:dept_id>", methods=["POST"])
@admin_required
def edit_department(dept_id):
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    if name:
        try:
            database.update_department(dept_id, name, code)
            flash(f"Department updated to '{name}'.", "success")
        except Exception as e:
            flash(f"Error updating department: {e}", "danger")
    return redirect(url_for("departments_page"))

@app.route("/departments/delete/<int:dept_id>", methods=["POST"])
@admin_required
def delete_department(dept_id):
    try:
        database.delete_department(dept_id)
        flash("Department and associated curricula deleted successfully.", "info")
    except Exception as e:
        flash(f"Failed to delete department: {e}", "danger")
    return redirect(url_for("departments_page"))

# ----------------- COURSES -----------------
@app.route("/courses")
@admin_required
def courses_page():
    courses = database.get_courses()
    departments = database.get_departments()
    return render_template("courses.html", courses=courses, departments=departments)

@app.route("/courses/add", methods=["POST"])
@app.route("/add_course", methods=["POST"])
@admin_required
def add_course():
    name = request.form.get("name", "").strip()
    dept_id = request.form.get("department_id")
    code = request.form.get("code", "").strip()
    duration = request.form.get("duration_years", 3)

    if name and dept_id:
        try:
            database.add_course(name, int(dept_id), code, int(duration))
            flash(f"Degree program '{name}' created successfully.", "success")
        except Exception as e:
            flash(f"Error adding course: {e}", "danger")
    else:
        flash("Course name and department are required.", "danger")
    return redirect(url_for("courses_page"))

@app.route("/courses/edit/<int:course_id>", methods=["POST"])
@admin_required
def edit_course(course_id):
    name = request.form.get("name", "").strip()
    dept_id = request.form.get("department_id")
    code = request.form.get("code", "").strip()
    duration = request.form.get("duration_years", 3)

    if name and dept_id:
        try:
            database.update_course(course_id, name, int(dept_id), code, int(duration))
            flash(f"Course '{name}' updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating course: {e}", "danger")
    return redirect(url_for("courses_page"))

@app.route("/courses/delete/<int:course_id>", methods=["POST"])
@admin_required
def delete_course(course_id):
    try:
        database.delete_course(course_id)
        flash("Course deleted successfully.", "info")
    except Exception as e:
        flash(f"Error deleting course: {e}", "danger")
    return redirect(url_for("courses_page"))

# ----------------- SEMESTERS -----------------
@app.route("/semesters")
@admin_required
def semesters_page():
    semesters = database.get_semesters()
    courses = database.get_courses()
    return render_template("semesters.html", semesters=semesters, courses=courses)

@app.route("/semesters/add", methods=["POST"])
@app.route("/add_semester", methods=["POST"])
@admin_required
def add_semester():
    name = request.form.get("name", "").strip()
    course_id = request.form.get("course_id")

    if name and course_id:
        try:
            database.add_semester(name, int(course_id))
            flash(f"Semester '{name}' added successfully.", "success")
        except Exception as e:
            flash(f"Error adding semester: {e}", "danger")
    else:
        flash("Semester name and course are required.", "danger")
    return redirect(url_for("semesters_page"))

@app.route("/semesters/edit/<int:sem_id>", methods=["POST"])
@admin_required
def edit_semester(sem_id):
    name = request.form.get("name", "").strip()
    course_id = request.form.get("course_id")
    if name and course_id:
        try:
            database.update_semester(sem_id, name, int(course_id))
            flash(f"Semester '{name}' updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating semester: {e}", "danger")
    return redirect(url_for("semesters_page"))

@app.route("/semesters/delete/<int:sem_id>", methods=["POST"])
@admin_required
def delete_semester(sem_id):
    try:
        database.delete_semester(sem_id)
        flash("Semester deleted successfully.", "info")
    except Exception as e:
        flash(f"Error deleting semester: {e}", "danger")
    return redirect(url_for("semesters_page"))

# ----------------- SUBJECTS -----------------
@app.route("/subjects")
@admin_required
def subjects_page():
    subjects = database.get_subjects()
    semesters = database.get_semesters()
    courses = database.get_courses()
    return render_template("subjects.html", subjects=subjects, semesters=semesters, courses=courses)

@app.route("/subjects/add", methods=["POST"])
@app.route("/add_subject", methods=["POST"])
@admin_required
def add_subject():
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    semester_id = request.form.get("semester_id")
    max_marks = request.form.get("max_marks", 100)
    pass_marks = request.form.get("pass_marks", 40)
    credits = request.form.get("credits", 4)

    if name and semester_id:
        try:
            database.add_subject(name, code, int(max_marks), int(pass_marks), int(credits), int(semester_id))
            flash(f"Subject '{name}' configured with {credits} credits.", "success")
        except Exception as e:
            flash(f"Error adding subject: {e}", "danger")
    else:
        flash("Subject title and semester are required.", "danger")
    return redirect(url_for("subjects_page"))

@app.route("/subjects/edit/<int:sub_id>", methods=["POST"])
@admin_required
def edit_subject(sub_id):
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    semester_id = request.form.get("semester_id")
    max_marks = request.form.get("max_marks", 100)
    pass_marks = request.form.get("pass_marks", 40)
    credits = request.form.get("credits", 4)

    if name and semester_id:
        try:
            database.update_subject(sub_id, name, code, int(max_marks), int(pass_marks), int(credits), int(semester_id))
            flash(f"Subject '{name}' updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating subject: {e}", "danger")
    return redirect(url_for("subjects_page"))

@app.route("/subjects/delete/<int:sub_id>", methods=["POST"])
@admin_required
def delete_subject(sub_id):
    try:
        database.delete_subject(sub_id)
        flash("Subject deleted successfully.", "info")
    except Exception as e:
        flash(f"Error deleting subject: {e}", "danger")
    return redirect(url_for("subjects_page"))

# ----------------- STUDENTS -----------------
@app.route("/students")
@admin_required
def students_page():
    students = database.get_students()
    courses = database.get_courses()
    semesters = database.get_semesters()
    return render_template("students.html", students=students, courses=courses, semesters=semesters)

@app.route("/students/add", methods=["POST"])
@app.route("/add_student", methods=["POST"])
@admin_required
def add_student():
    enrollment = request.form.get("enrollment", "").strip()
    name = request.form.get("name", "").strip()
    course_id = request.form.get("course_id")
    semester_id = request.form.get("semester_id")
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "student123").strip()

    if enrollment and name and course_id and semester_id:
        try:
            database.add_student(enrollment, name, int(course_id), int(semester_id), email, phone, password)
            flash(f"Student '{name}' ({enrollment}) registered successfully.", "success")
        except Exception as e:
            flash(f"Error enrolling student (check duplicate enrollment): {e}", "danger")
    else:
        flash("Enrollment number, Name, Course, and Semester are required.", "danger")
    return redirect(url_for("students_page"))

@app.route("/students/edit/<int:student_id>", methods=["POST"])
@admin_required
def edit_student(student_id):
    enrollment = request.form.get("enrollment", "").strip()
    name = request.form.get("name", "").strip()
    course_id = request.form.get("course_id")
    semester_id = request.form.get("semester_id")
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if enrollment and name and course_id and semester_id:
        try:
            database.update_student(student_id, enrollment, name, int(course_id), int(semester_id), email, phone)
            flash(f"Student '{name}' profile updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating student: {e}", "danger")
    return redirect(url_for("students_page"))

@app.route("/students/delete/<int:student_id>", methods=["POST"])
@admin_required
def delete_student(student_id):
    try:
        database.delete_student(student_id)
        flash("Student record and marks removed.", "info")
    except Exception as e:
        flash(f"Error deleting student: {e}", "danger")
    return redirect(url_for("students_page"))

# ----------------- MARKS & RESULTS -----------------
@app.route("/marks")
@admin_required
def marks_page():
    students = database.get_students()
    subjects = database.get_subjects()
    
    # Fetch flat list of recorded marks for display
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.student_id, r.subject_id, r.marks,
               stu.name as student_name, stu.enrollment,
               sub.name as subject_name, sub.code as subject_code,
               sub.max_marks, sub.pass_marks, sub.credits
        FROM results r
        JOIN students stu ON r.student_id = stu.id
        JOIN subjects sub ON r.subject_id = sub.id
        ORDER BY r.created_at DESC, stu.name ASC
    """)
    raw_marks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Calculate grade letter for each row
    from utils.calculations import get_grade_and_points
    for m in raw_marks:
        g, gp, _ = get_grade_and_points(m["marks"], m["max_marks"])
        m["grade"] = g
        m["grade_points"] = gp

    return render_template(
        "add_marks.html",
        students=students,
        subjects=subjects,
        marks_list=raw_marks
    )

@app.route("/marks/add", methods=["POST"])
@app.route("/add_marks", methods=["POST"])
@admin_required
def add_marks():
    student_id = request.form.get("student_id")
    subject_id = request.form.get("subject_id")
    marks = request.form.get("marks")

    if student_id and subject_id and marks is not None:
        try:
            m_val = int(marks)
            if m_val < 0:
                flash("Marks cannot be negative.", "danger")
                return redirect(url_for("marks_page"))

            sub = database.get_subject(int(subject_id))
            if sub and m_val > sub.get("max_marks", 100):
                flash(f"Marks ({m_val}) cannot exceed maximum allowed marks ({sub['max_marks']}).", "danger")
                return redirect(url_for("marks_page"))

            database.add_or_update_mark(int(student_id), int(subject_id), m_val)
            flash("Subject marks recorded successfully and SGPA updated.", "success")
        except Exception as e:
            flash(f"Failed to record marks: {e}", "danger")
    else:
        flash("Student, subject, and marks are required.", "danger")

    return redirect(url_for("marks_page"))

@app.route("/marks/delete", methods=["POST"])
@admin_required
def delete_marks():
    student_id = request.form.get("student_id")
    subject_id = request.form.get("subject_id")
    if student_id and subject_id:
        try:
            database.delete_mark(int(student_id), int(subject_id))
            flash("Marks entry removed.", "info")
        except Exception as e:
            flash(f"Error removing marks: {e}", "danger")
    return redirect(url_for("marks_page"))

# ----------------- RESULTS LEDGER -----------------
@app.route("/results")
@admin_required
def results_ledger():
    course_id = request.args.get("course_id", type=int)
    semester_id = request.args.get("semester_id", type=int)
    search = request.args.get("search", "").strip()

    courses = database.get_courses()
    semesters = database.get_semesters(course_id=course_id) if course_id else database.get_semesters()
    ledger = database.get_all_results_ledger(course_id=course_id, semester_id=semester_id, search=search)

    return render_template(
        "view_result.html",
        ledger=ledger,
        courses=courses,
        semesters=semesters,
        selected_course_id=course_id,
        selected_semester_id=semester_id,
        search_query=search
    )

@app.route("/results/export-csv")
@admin_required
def export_results_csv():
    course_id = request.args.get("course_id", type=int)
    ledger = database.get_all_results_ledger(course_id=course_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Enrollment", "Student Name", "Course", "Semester", "Department",
        "Total Credits", "Marks Obtained", "Max Marks", "Percentage", "SGPA", "Status", "Division"
    ])

    for item in ledger:
        stu = item["student"]
        res = item["summary"]
        writer.writerow([
            stu["enrollment"], stu["name"], stu["course_name"], stu["semester_name"], stu["department_name"],
            res["total_credits"], res["total_marks_obtained"], res["total_max_marks"],
            f"{res['percentage']}%", res["sgpa"], res["overall_status"], res["division"]
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=puma_university_tabulation_register.csv"}
    )

# ----------------- STUDENT PORTAL -----------------
@app.route("/student/dashboard")
@app.route("/student/result")
@app.route("/student")
@student_required
def student_dashboard():
    user = session.get("user", {})
    student_id = user.get("id")

    student, summary = database.get_student_academic_summary(student_id)
    if not student:
        session.clear()
        flash("Student profile record not found. Please log in again.", "danger")
        return redirect(url_for("home"))

    return render_template(
        "student_dashboard.html",
        student=student,
        summary=summary
    )

# ----------------- MARKSHEET & VERIFICATION -----------------
def _resolve_student_record(identifier):
    student = None
    if str(identifier).isdigit():
        student = database.get_student(int(identifier))
    if not student:
        student = database.get_student_by_enrollment(str(identifier))
    return student

@app.route("/marksheet/<identifier>")
@app.route("/marksheet/<identifier>/pdf")
def marksheet_pdf(identifier):
    stu = _resolve_student_record(identifier)
    if not stu:
        return "Student Not Found", 404

    student, summary = database.get_student_academic_summary(stu["id"])
    if not student:
        return "Student Not Found", 404

    base_url = request.host_url.rstrip("/")
    pdf_buffer = generate_student_marksheet_pdf(student, summary, base_url=base_url)

    file_name = f"Marksheet_{student['enrollment']}_{student['name'].replace(' ', '_')}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=file_name
    )

@app.route("/marksheet/preview/<identifier>")
def marksheet_preview(identifier):
    stu = _resolve_student_record(identifier)
    if not stu:
        flash("Student record not found.", "danger")
        return redirect(url_for("home"))

    student, summary = database.get_student_academic_summary(stu["id"])
    if not student:
        flash("Student record not found.", "danger")
        return redirect(url_for("home"))

    return render_template(
        "marksheet_preview.html",
        student=student,
        summary=summary
    )

@app.route("/verify/<enrollment>")
def verify_transcript(enrollment):
    stu = database.get_student_by_enrollment(enrollment)
    if stu:
        student, summary = database.get_student_academic_summary(stu["id"])
    else:
        student, summary = None, None

    return render_template(
        "verify_result.html",
        student=student,
        summary=summary,
        requested_enrollment=enrollment
    )

@app.route("/api/qr/<enrollment>")
def generate_qr_api(enrollment):
    verify_url = f"{request.host_url.rstrip('/')}/verify/{enrollment}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=5,
        border=1,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

# ----------------- REST APIS (CASCADING & AJAX) -----------------
@app.route("/api/departments")
def api_departments():
    return jsonify(database.get_departments())

@app.route("/api/courses")
def api_courses():
    dept_id = request.args.get("department_id", type=int)
    return jsonify(database.get_courses(department_id=dept_id))

@app.route("/api/semesters")
def api_semesters():
    course_id = request.args.get("course_id", type=int)
    return jsonify(database.get_semesters(course_id=course_id))

@app.route("/api/subjects")
def api_subjects():
    semester_id = request.args.get("semester_id", type=int)
    course_id = request.args.get("course_id", type=int)
    return jsonify(database.get_subjects(semester_id=semester_id, course_id=course_id))

@app.route("/api/students")
def api_students():
    course_id = request.args.get("course_id", type=int)
    semester_id = request.args.get("semester_id", type=int)
    search = request.args.get("search")
    return jsonify(database.get_students(course_id=course_id, semester_id=semester_id, search=search))

@app.route("/api/analytics")
@admin_required
def api_analytics():
    return jsonify(database.get_dashboard_analytics())

from flask import send_from_directory

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# ----------------- ERROR HANDLERS -----------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return f"<h3>500 Internal Server Error: {e}</h3>", 500

if __name__ == "__main__":
    print("=" * 60)
    print(" PUMA UNIVERSITY - RESULT MANAGEMENT PORTAL")
    print(" Server running on: http://127.0.0.1:5000")
    print(" Admin Credentials: username='admin', password='admin123'")
    print(" Student Creds:     enrollment='25COA4MCA0187', password='student123'")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
