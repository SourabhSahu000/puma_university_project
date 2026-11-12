# PUMA UNIVERSITY - STUDENT & EXAMINATION RESULT MANAGEMENT SYSTEM

A production-grade, full-featured University Examination Portal, Tabulation Register, and Student Academic Management System built with a modern Python 3.14 + Flask 3.1 backend, interactive Chart.js analytics, responsive UI (Tailwind CSS & Bootstrap 5.3), and high-resolution ReportLab PDF marksheet generation with digital QR code verification.

---

## 🌟 Key Features

### 1. 🛡️ Role-Based Authentication & Portals
- **Admin Portal**: Executive examination board dashboard with real-time KPI metrics, university grade distribution, department strength charts, and full curriculum CRUD operations.
- **Student Portal**: Personalized student dashboard where candidates log in with their Roll / Enrollment Number, view semester grade summaries, SGPA & credit breakdowns, subject-wise progress bars, and print or download official marksheets.

### 2. 📚 Academic Hierarchy (Full CRUD)
- **Departments**: Add, edit, delete, and view departments with active course counts.
- **Courses / Degrees**: Manage degree programs (e.g. BCA, MCA, B.Tech) linked to departments with configurable duration.
- **Semesters**: Organize courses into academic terms with dynamic cascading dropdowns.
- **Subjects & Credits**: Configure course units with credit hours, maximum marks, passing marks, and subject codes.
- **Students Roster**: Candidate registration with auto-generated passwords, course/semester assignment, and instant search & filtering.

### 3. ✍️ Evaluation & Results Engine
- **Marks Evaluation**: Add or update marks with built-in validation (range checks, negative value rejection, duplicate entry upserts).
- **10-Point UGC Grading Scale**: Automatically computes:
  - Letter Grades: `O` (Outstanding), `A+` (Excellent), `A` (Very Good), `B+` (Good), `B` (Above Average), `C` (Pass), `F` (Fail/Backlog)
  - Grade Points (0–10)
  - Credit Points = $\text{Credits} \times \text{Grade Point}$
  - **SGPA** = $\frac{\sum \text{Credit Points}}{\sum \text{Credits}}$
  - Academic Division (First Class with Distinction, First Class, Second Class, Pass, Backlog)
- **Tabulation Register / Results Ledger**: Filter results by course and semester, search candidate records, and export tabulation data to CSV.

### 4. 📄 High-Resolution Official Marksheet (PDF & Web)
- High-fidelity PDF generated in-memory via ReportLab.
- Features official university crest header, candidate particulars, subject breakdown table, summary statistics, grading scale legend, digital seal, and signature blocks.
- **Embedded Dynamic QR Code**: Scanning the QR code directs directly to the public online verification URL (`/verify/<enrollment>`).
- In-browser interactive preview with print-optimized stylesheets (`@media print`).

### 5. 🔍 Public Verification Portal
- `/verify/<enrollment>`: Verifies official marksheet authenticity online for prospective employers and institutions.

---

## 🚀 Quick Start

### 1. Launch the Server
```bash
python app.py
```
Open your browser at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 2. Default Login Credentials

| Role | Username / Enrollment | Password | Access |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full Administrative & Examination Control |
| **Student (Sunita)** | `25COA4MCA0187` | `student123` | Personal Academic Transcript & Marksheet |
| **Student (Nandini)** | `25COA2MCA0023` | `student123` | Personal Academic Transcript & Marksheet |

*Note: The login screen also includes convenient 1-click demo login buttons to auto-fill credentials.*

---

## 🛠️ Modern Tech Stack
- **Backend**: Python 3.14, Flask 3.1.3, Werkzeug, SQLite (WAL mode, Foreign Keys, Unique Indexes)
- **Document & QR Generation**: ReportLab 4.4, Pillow, qrcode
- **Frontend**: Tailwind CSS, Bootstrap 5.3, FontAwesome 6, Chart.js 4.4, SweetAlert2
- **Data Export**: CSV Stream & In-memory PDF streaming

