"""
Academic grading and calculation utilities for PUMA University.
Follows standard University / UGC 10-point grading scale.
"""

def get_grade_and_points(marks: float, max_marks: float = 100) -> tuple[str, int, str]:
    """
    Returns (grade_letter, grade_points, remarks) based on percentage.
    """
    if max_marks <= 0:
        return ("F", 0, "Fail")
    
    percentage = (marks / max_marks) * 100.0

    if percentage >= 90:
        return ("O", 10, "Outstanding")
    elif percentage >= 80:
        return ("A+", 9, "Excellent")
    elif percentage >= 70:
        return ("A", 8, "Very Good")
    elif percentage >= 60:
        return ("B+", 7, "Good")
    elif percentage >= 50:
        return ("B", 6, "Above Average")
    elif percentage >= 40:
        return ("C", 5, "Pass")
    else:
        return ("F", 0, "Fail")


def get_division(percentage: float, has_fail: bool = False) -> str:
    """
    Determine academic division/honors.
    """
    if has_fail:
        return "Fail / Backlog"
    if percentage >= 75:
        return "First Class with Distinction"
    elif percentage >= 60:
        return "First Class"
    elif percentage >= 50:
        return "Second Class"
    elif percentage >= 40:
        return "Pass Class"
    else:
        return "Fail"


def calculate_student_results(records: list[dict]) -> dict:
    """
    Calculates summary metrics from a list of subject result records for a student.
    Each record dict must have:
      - subject_name
      - max_marks
      - marks
      - credits
      - pass_marks (optional, defaults to 40% of max_marks)
    """
    total_marks_obtained = 0
    total_max_marks = 0
    total_credits = 0
    weighted_grade_points = 0
    has_backlog = False
    passed_subjects = 0
    failed_subjects = 0
    detailed_subjects = []

    for r in records:
        marks = float(r.get("marks", 0))
        max_m = float(r.get("max_marks", 100))
        credits = float(r.get("credits", 4))
        pass_m = float(r.get("pass_marks", max_m * 0.4))

        grade, gp, remark = get_grade_and_points(marks, max_m)
        credit_points = credits * gp
        is_pass = marks >= pass_m

        if not is_pass:
            has_backlog = True
            failed_subjects += 1
        else:
            passed_subjects += 1

        total_marks_obtained += marks
        total_max_marks += max_m
        total_credits += credits
        weighted_grade_points += credit_points

        detailed_subjects.append({
            "subject_name": r.get("subject_name"),
            "subject_code": r.get("subject_code", "N/A"),
            "credits": credits,
            "max_marks": int(max_m),
            "pass_marks": int(pass_m),
            "marks_obtained": marks,
            "grade": grade,
            "grade_points": gp,
            "credit_points": credit_points,
            "status": "PASS" if is_pass else "FAIL",
            "remarks": remark
        })

    percentage = (total_marks_obtained / total_max_marks * 100.0) if total_max_marks > 0 else 0.0
    sgpa = (weighted_grade_points / total_credits) if total_credits > 0 else 0.0
    overall_status = "FAIL" if has_backlog else ("PASS" if total_max_marks > 0 else "N/A")
    division = get_division(percentage, has_fail=has_backlog)

    return {
        "subjects": detailed_subjects,
        "total_marks_obtained": total_marks_obtained,
        "total_max_marks": total_max_marks,
        "total_credits": total_credits,
        "weighted_grade_points": weighted_grade_points,
        "percentage": round(percentage, 2),
        "sgpa": round(sgpa, 2),
        "cgpa": round(sgpa, 2),  # Default to SGPA for single semester
        "overall_status": overall_status,
        "division": division,
        "passed_subjects": passed_subjects,
        "failed_subjects": failed_subjects,
        "total_subjects": len(records)
    }

