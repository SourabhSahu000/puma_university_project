import io
import os
from datetime import datetime
import qrcode
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Image as RLImage, Spacer, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def generate_student_marksheet_pdf(student: dict, summary: dict, base_url: str = "") -> io.BytesIO:
    """
    Generates an official, high-resolution University Grade Sheet / Marksheet PDF
    with embedded verification QR code and university branding.
    Returns a BytesIO stream.
    """
    buffer = io.BytesIO()

    # Standard A4 is 595.27 x 841.89 points
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "UnivTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e3a8a")  # Deep Royal Navy
    )

    subtitle_style = ParagraphStyle(
        "UnivSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569")
    )

    doc_type_style = ParagraphStyle(
        "DocType",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#991b1b")  # Crimson accent
    )

    info_label_style = ParagraphStyle(
        "InfoLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )

    info_val_style = ParagraphStyle(
        "InfoVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#1e293b")
    )

    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=table_cell_style,
        alignment=TA_CENTER
    )

    table_cell_bold_center = ParagraphStyle(
        "TableCellBoldCenter",
        parent=table_cell_style,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER
    )

    elements = []

    # 1. UNIVERSITY HEADER WITH LOGO
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(BASE_DIR, "static", "logo.png")
    logo_element = None
    if os.path.exists(logo_path):
        try:
            logo_element = RLImage(logo_path, width=54, height=54)
        except Exception:
            logo_element = None

    header_text_cells = [
        Paragraph("PUMA UNIVERSITY", title_style),
        Paragraph("Accredited Grade 'A++' by NAAC | Approved by UGC & AICTE", subtitle_style),
        Paragraph("Knowledge Park, Academic City - 411045", subtitle_style),
        Spacer(1, 3),
        Paragraph("OFFICIAL GRADE SHEET & STATEMENT OF MARKS", doc_type_style)
    ]

    if logo_element:
        header_table = Table([[logo_element, header_text_cells]], colWidths=[65, 470])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ]))
        elements.append(header_table)
    else:
        for p in header_text_cells:
            elements.append(p)

    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=8))

    # 2. STUDENT CANDIDATE INFORMATION BOX
    student_name = str(student.get("name") or "N/A").upper()
    enrollment = str(student.get("enrollment") or "N/A")
    course_name = str(student.get("course_name") or "N/A")
    dept_name = str(student.get("department_name") or "N/A")
    sem_name = str(student.get("semester_name") or "Semester 1")
    exam_session = str(student.get("session") or "Academic Session 2025-2026")
    serial_no = f"PU/RES/{int(student.get('id') or 1):04d}/{enrollment}"
    current_date = datetime.now().strftime("%B %d, %Y")

    student_info_data = [
        [
            Paragraph("<b>Student Name:</b>", info_label_style),
            Paragraph(f"<b>{student_name}</b>", info_val_style),
            Paragraph("<b>Enrollment No:</b>", info_label_style),
            Paragraph(f"<b>{enrollment}</b>", info_val_style),
        ],
        [
            Paragraph("<b>Program / Course:</b>", info_label_style),
            Paragraph(course_name, info_val_style),
            Paragraph("<b>Department:</b>", info_label_style),
            Paragraph(dept_name, info_val_style),
        ],
        [
            Paragraph("<b>Semester / Term:</b>", info_label_style),
            Paragraph(str(sem_name), info_val_style),
            Paragraph("<b>Academic Session:</b>", info_label_style),
            Paragraph(exam_session, info_val_style),
        ],
        [
            Paragraph("<b>Serial Number:</b>", info_label_style),
            Paragraph(serial_no, info_val_style),
            Paragraph("<b>Issue Date:</b>", info_label_style),
            Paragraph(current_date, info_val_style),
        ]
    ]

    info_table = Table(student_info_data, colWidths=[95, 175, 100, 165])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # 3. SUBJECT-WISE MARKS TABLE
    subject_table_data = [
        [
            Paragraph("<b>#</b>", table_header_style),
            Paragraph("<b>Subject Code</b>", table_header_style),
            Paragraph("<b>Subject Title</b>", table_header_style),
            Paragraph("<b>Credits</b>", table_header_style),
            Paragraph("<b>Max</b>", table_header_style),
            Paragraph("<b>Min</b>", table_header_style),
            Paragraph("<b>Marks</b>", table_header_style),
            Paragraph("<b>Grade</b>", table_header_style),
            Paragraph("<b>GP</b>", table_header_style),
            Paragraph("<b>CP</b>", table_header_style),
            Paragraph("<b>Status</b>", table_header_style),
        ]
    ]

    subjects = summary.get("subjects", [])
    row_count = 0
    for idx, sub in enumerate(subjects, 1):
        row_count += 1
        is_even = (row_count % 2 == 0)
        status_color = "#16a34a" if sub["status"] == "PASS" else "#dc2626"
        status_para = Paragraph(f"<font color='{status_color}'><b>{sub['status']}</b></font>", table_cell_center)
        
        code_str = str(sub.get("subject_code") or f"SUB{idx:02d}")
        name_str = str(sub.get("subject_name") or "Subject")
        subject_table_data.append([
            Paragraph(str(idx), table_cell_center),
            Paragraph(code_str, table_cell_center),
            Paragraph(name_str, table_cell_style),
            Paragraph(str(int(sub.get("credits") or 4)), table_cell_center),
            Paragraph(str(int(sub.get("max_marks") or 100)), table_cell_center),
            Paragraph(str(int(sub.get("pass_marks") or 40)), table_cell_center),
            Paragraph(f"<b>{int(sub.get('marks_obtained') or 0)}</b>", table_cell_bold_center),
            Paragraph(f"<b>{str(sub.get('grade') or 'F')}</b>", table_cell_bold_center),
            Paragraph(str(sub.get("grade_points") or 0), table_cell_center),
            Paragraph(str(round(sub.get("credit_points") or 0, 1)), table_cell_center),
            status_para
        ])

    col_widths = [22, 68, 175, 40, 36, 36, 42, 36, 26, 26, 40]
    sub_table = Table(subject_table_data, colWidths=col_widths)

    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]

    for i in range(1, len(subject_table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f8fafc")))
        else:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))

    sub_table.setStyle(TableStyle(t_style))
    elements.append(sub_table)
    elements.append(Spacer(1, 8))

    # 4. RESULT SUMMARY BOX
    total_obtained = summary.get("total_marks_obtained", 0)
    total_max = summary.get("total_max_marks", 100)
    percentage = summary.get("percentage", 0.0)
    sgpa = summary.get("sgpa", 0.0)
    total_credits = summary.get("total_credits", 0)
    overall_status = summary.get("overall_status", "N/A")
    division = summary.get("division", "N/A")

    status_color = "#15803d" if overall_status == "PASS" else "#b91c1c"

    summary_data = [
        [
            Paragraph("<b>Total Credits:</b>", info_label_style),
            Paragraph(f"<b>{total_credits}</b>", info_val_style),
            Paragraph("<b>Marks Obtained:</b>", info_label_style),
            Paragraph(f"<b>{int(total_obtained)} / {int(total_max)}</b>", info_val_style),
            Paragraph("<b>Percentage:</b>", info_label_style),
            Paragraph(f"<b>{percentage}%</b>", info_val_style),
        ],
        [
            Paragraph("<b>Semester SGPA:</b>", info_label_style),
            Paragraph(f"<font color='#1e3a8a' size='10'><b>{sgpa} / 10.0</b></font>", info_val_style),
            Paragraph("<b>Result Status:</b>", info_label_style),
            Paragraph(f"<font color='{status_color}' size='9.5'><b>{overall_status}</b></font>", info_val_style),
            Paragraph("<b>Division:</b>", info_label_style),
            Paragraph(f"<b>{division}</b>", info_val_style),
        ]
    ]

    summary_table = Table(summary_data, colWidths=[85, 75, 95, 85, 85, 110])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8))

    # 5. GRADING SCALE LEGEND
    legend_style = ParagraphStyle(
        "Legend",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569")
    )
    legend_text = (
        "<b>Grading Scale:</b> O (Outstanding, 90-100%, GP:10) | "
        "A+ (Excellent, 80-89%, GP:9) | A (Very Good, 70-79%, GP:8) | "
        "B+ (Good, 60-69%, GP:7) | B (Above Avg, 50-59%, GP:6) | "
        "C (Pass, 40-49%, GP:5) | F (Fail, &lt;40%, GP:0)"
    )
    elements.append(Paragraph(legend_text, legend_style))
    elements.append(Spacer(1, 10))

    # 6. QR CODE AND SIGNATURE SECTION (BOTTOM)
    # Generate QR Code image in memory
    verify_url = f"{base_url.rstrip('/')}/verify/{enrollment}" if base_url else f"https://puma-university.edu/verify/{enrollment}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, "PNG")
    qr_buffer.seek(0)
    qr_element = RLImage(qr_buffer, width=54, height=54)

    footer_left = [
        qr_element,
        Spacer(1, 2),
        Paragraph("<font size='6.5' color='#64748b'>Scan to Verify Result Online</font>", subtitle_style)
    ]

    footer_middle = [
        Spacer(1, 12),
        Paragraph("<b>[ OFFICIAL DIGITAL SEAL ]</b>", ParagraphStyle("Seal", parent=subtitle_style, fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#0284c7"))),
        Paragraph("<font size='7' color='#64748b'>PUMA UNIVERSITY EXAMINATIONS BOARD</font>", subtitle_style),
        Paragraph("<font size='6.5' color='#94a3b8'>Computer Generated Authentic Transcript</font>", subtitle_style)
    ]

    footer_right = [
        Spacer(1, 20),
        Paragraph("____________________________", ParagraphStyle("Line", parent=subtitle_style, alignment=TA_CENTER)),
        Paragraph("<b>Controller of Examinations</b>", ParagraphStyle("Sign", parent=subtitle_style, fontName="Helvetica-Bold", fontSize=8.5, alignment=TA_CENTER)),
        Paragraph("<font size='7' color='#64748b'>Puma University Authority</font>", subtitle_style)
    ]

    footer_table = Table([[footer_left, footer_middle, footer_right]], colWidths=[130, 240, 165])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(KeepTogether([footer_table]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
