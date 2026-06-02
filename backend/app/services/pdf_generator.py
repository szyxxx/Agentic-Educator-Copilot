import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime

def generate_analytics_pdf(analytics_data: dict, rps_data: dict = None) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading1_style = styles["Heading1"]
    heading2_style = styles["Heading2"]
    normal_style = styles["Normal"]
    
    # Custom styles
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        textColor=colors.gray,
        spaceAfter=20,
    )

    story = []

    # Title
    course_name = analytics_data.get("course_overview", {}).get("course", "Unknown Course")
    semester = analytics_data.get("course_overview", {}).get("semester", "")
    
    story.append(Paragraph("Laporan Analitik Kelas", title_style))
    story.append(Paragraph(f"{course_name} • {semester}", subtitle_style))
    story.append(Paragraph(f"Tanggal Cetak: {datetime.now().strftime('%d %B %Y')}", normal_style))
    story.append(Spacer(1, 20))

    # 1. Performance Overview
    story.append(Paragraph("Ringkasan Performa", heading1_style))
    overview_data = [
        ["Total Mahasiswa", "Rata-rata Nilai", "Tingkat Kelulusan", "Remedial"],
    ]
    overview_vals = [
        str(analytics_data.get("course_overview", {}).get("total_students", 0)),
        str(analytics_data.get("course_overview", {}).get("avg_score", 0)),
        f"{analytics_data.get('course_overview', {}).get('pass_rate', 0)}%",
        str(analytics_data.get("course_overview", {}).get("remedial_students", 0)),
    ]
    overview_data.append(overview_vals)

    overview_table = Table(overview_data, colWidths=[120, 120, 120, 120])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.teal),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 20))

    # 2. RPS Progress
    if rps_data:
        story.append(Paragraph("Status Rencana Pembelajaran Semester (RPS)", heading1_style))
        rps_summary_data = [
            ["Status RPS", "Compliance Score", "Total CPMK"],
            [
                "Sesuai" if rps_data.get("status") == "validated" else "Perlu Review",
                f"{int(rps_data.get('summary', [{}])[0].get('value', '0').replace('%',''))}%",
                str(len(rps_data.get("cpmk_list", [])))
            ]
        ]
        
        rps_table = Table(rps_summary_data, colWidths=[160, 160, 160])
        rps_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(rps_table)
        story.append(Spacer(1, 20))

    # 3. CPMK Progress
    cpmk_progress = analytics_data.get("cpmk_progress", [])
    if cpmk_progress:
        story.append(Paragraph("Pencapaian CPMK", heading1_style))
        cpmk_data = [["ID CPMK", "Judul", "Progress", "Status"]]
        for cpmk in cpmk_progress:
            cpmk_data.append([
                cpmk.get("id", ""),
                Paragraph(cpmk.get("title", ""), normal_style),
                f"{cpmk.get('progress', 0)}%",
                cpmk.get("status", "")
            ])
            
        cpmk_table = Table(cpmk_data, colWidths=[80, 240, 80, 80])
        cpmk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(cpmk_table)
        story.append(Spacer(1, 20))

    # 4. Grading Distribution
    per_student = analytics_data.get("per_student", [])
    if per_student:
        story.append(Paragraph("Rekapitulasi Nilai Mahasiswa", heading1_style))
        student_data = [["NIM", "Nama", "Rata-rata Nilai", "Status"]]
        
        for student in per_student:
            student_data.append([
                student.get("nim", ""),
                Paragraph(student.get("name", ""), normal_style),
                f"{student.get('avg_score', 0):.1f}",
                "Lulus" if student.get("status") == "pass" else "Remedial"
            ])
            
        student_table = Table(student_data, colWidths=[100, 220, 80, 80], repeatRows=1)
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(student_table)

    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
