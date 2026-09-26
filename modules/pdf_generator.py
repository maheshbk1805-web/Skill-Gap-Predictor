"""
PDF Report Generator Module
Project ID: P19 - Skill-Gap Predictor for Students (Career Navigation AI)
GITAM University, Bengaluru Campus
Developers: Vinay Kumar S, Yashwanth K, Mahesh B K
Mentor: Dr. N. Gayathri (M29)

Generates professional downloadable Progress Report PDF documents with ReportLab,
ensuring perfect row/column cell alignment, text wrapping, and clean typography.
"""

import io
from datetime import datetime
from typing import Dict, List, Any

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError:
    SimpleDocTemplate = None


def generate_pdf_report(
    student_name: str,
    target_role: str,
    target_company: str,
    domain: str,
    ats_score: float,
    readiness_score: float,
    confidence_score: float,
    resume_strength: str,
    matched_skills: List[str],
    missing_skills: List[str],
    recommendations: List[str],
    roadmap_phases: List[Dict[str, Any]],
) -> bytes:
    """Generate a clean, perfectly aligned Progress Report PDF."""

    if SimpleDocTemplate is None:
        return b"%PDF-1.4 Mock PDF Output (ReportLab not installed)"

    buffer = io.BytesIO()

    # Ensure numeric values are clean and readable in the PDF
    try:
        ats_score = float(ats_score)
    except (TypeError, ValueError):
        ats_score = 0.0

    try:
        readiness_score = float(readiness_score)
    except (TypeError, ValueError):
        readiness_score = 0.0

    try:
        confidence_score = float(confidence_score)
    except (TypeError, ValueError):
        confidence_score = 0.0

    # Printable area: 612 - 80 = 532 pt
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=35,
        bottomMargin=35,
    )

    styles = getSampleStyleSheet()

    # Typography styles with explicit leading to prevent overlap
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1,
    )

    badge_style = ParagraphStyle(
        "ReportBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2563EB"),
        alignment=1,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )

    h1_style = ParagraphStyle(
        "ReportH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=5,
    )

    # Table cell paragraph styles
    th_center = ParagraphStyle(
        "THCenter",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )

    td_left = ParagraphStyle(
        "TDLeft",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        alignment=0,
    )

    td_center = ParagraphStyle(
        "TDCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        alignment=1,
    )

    score_val_center = ParagraphStyle(
        "ScoreVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1,
    )

    bullet_style = ParagraphStyle(
        "RecBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=2,
    )

    story = []

    # -------------------------------------------------------------
    # 1. HEADER BANNER
    # -------------------------------------------------------------
    story.append(
        Paragraph(
            "STUDENT CAREER NAVIGATION & SKILL ANALYSIS REPORT",
            badge_style
        )
    )
    story.append(Spacer(1, 2))

    story.append(
        Paragraph(
            "Skill-Gap Predictor & Career Navigator",
            title_style
        )
    )
    story.append(Spacer(1, 2))

    story.append(
        Paragraph(
            "Individual Placement Competency & ATS Analytics Report",
            subtitle_style
        )
    )
    story.append(Spacer(1, 6))

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2563EB"),
            spaceAfter=8
        )
    )

    # -------------------------------------------------------------
    # 2. CANDIDATE METADATA
    # -------------------------------------------------------------
    meta_data = [
        [
            Paragraph(
                f"<b>Student Name:</b> {student_name}",
                td_left
            ),
            Paragraph(
                f"<b>Evaluation Date:</b> "
                f"{datetime.now().strftime('%d-%b-%Y %H:%M')}",
                td_left
            )
        ],
        [
            Paragraph(
                f"<b>Target Role:</b> {target_role}",
                td_left
            ),
            Paragraph(
                f"<b>Target Company:</b> {target_company}",
                td_left
            )
        ],
        [
            Paragraph(
                f"<b>Detected Domain:</b> {domain}",
                td_left
            ),
            Paragraph(
                f"<b>Resume Strength:</b> "
                f"<b>{resume_strength}</b>",
                td_left
            )
        ]
    ]

    meta_table = Table(
        meta_data,
        colWidths=[266, 266]
    )

    meta_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, -1),
            colors.HexColor("#F8FAFC")
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "LEFT"
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            5
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            5
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#CBD5E1")
        ),
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#E2E8F0")
        ),
    ]))

    story.append(meta_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 3. PERFORMANCE EVALUATION SCORES
    # -------------------------------------------------------------
    story.append(
        Paragraph(
            "1. Performance Evaluation Scores",
            h1_style
        )
    )

    score_data = [
        [
            Paragraph(
                "ATS Compatibility Score",
                th_center
            ),
            Paragraph(
                "Job Readiness Score",
                th_center
            ),
            Paragraph(
                "AI Prediction Confidence",
                th_center
            )
        ],
        [
            Paragraph(
                f"{ats_score:.1f} / 100",
                score_val_center
            ),
            Paragraph(
                f"{readiness_score:.1f}%",
                score_val_center
            ),
            Paragraph(
                f"{confidence_score:.1f}%",
                score_val_center
            )
        ]
    ]

    score_table = Table(
        score_data,
        colWidths=[177, 177, 178]
    )

    score_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#2563EB")
        ),
        (
            "BACKGROUND",
            (0, 1),
            (-1, 1),
            colors.HexColor("#EFF6FF")
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "CENTER"
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            6
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            6
        ),
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#93C5FD")
        ),
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#BFDBFE")
        ),
    ]))

    story.append(score_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 4. SKILL GAP BREAKDOWN
    # -------------------------------------------------------------
    story.append(
        Paragraph(
            "2. Skill Gap Identification",
            h1_style
        )
    )

    matched_text = (
        ", ".join(str(skill) for skill in matched_skills)
        if matched_skills
        else "No direct matches detected."
    )

    missing_text = (
        ", ".join(str(skill) for skill in missing_skills)
        if missing_skills
        else "All core required skills are present in resume."
    )

    skill_rows = [
        [
            Paragraph(
                "<b>Matched Skills</b> "
                "(Demonstrated in Student Profile)",
                td_left
            )
        ],
        [
            Paragraph(
                f"<font color='#047857'>{matched_text}</font>",
                td_left
            )
        ],
        [
            Paragraph(
                "<b>Missing Skills</b> "
                "(Priority Skill Gaps for Selected Role)",
                td_left
            )
        ],
        [
            Paragraph(
                f"<font color='#B91C1C'>{missing_text}</font>",
                td_left
            )
        ]
    ]

    skill_table = Table(
        skill_rows,
        colWidths=[532]
    )

    skill_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (0, 0),
            colors.HexColor("#ECFDF5")
        ),
        (
            "BACKGROUND",
            (0, 1),
            (0, 1),
            colors.white
        ),
        (
            "BACKGROUND",
            (0, 2),
            (0, 2),
            colors.HexColor("#FEF2F2")
        ),
        (
            "BACKGROUND",
            (0, 3),
            (0, 3),
            colors.white
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "LEFT"
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            5
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            5
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#CBD5E1")
        ),
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#E2E8F0")
        ),
    ]))

    story.append(skill_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 5. STRATEGIC RECOMMENDATIONS
    # -------------------------------------------------------------
    story.append(
        Paragraph(
            "3. Actionable Preparation Recommendations",
            h1_style
        )
    )

    if recommendations:
        for idx, rec in enumerate(recommendations[:3], start=1):
            story.append(
                Paragraph(
                    f"• <b>{idx}.</b> {rec}",
                    bullet_style
                )
            )
    else:
        story.append(
            Paragraph(
                "No additional recommendations were generated.",
                bullet_style
            )
        )

    story.append(Spacer(1, 6))

    # -------------------------------------------------------------
    # 6. MILESTONE LEARNING ROADMAP
    # -------------------------------------------------------------
    story.append(
        Paragraph(
            "4. Milestone Learning Roadmap",
            h1_style
        )
    )

    roadmap_rows = [
        [
            Paragraph("Phase", th_center),
            Paragraph("Duration", th_center),
            Paragraph(
                "Core Objectives & Action Items",
                th_center
            )
        ]
    ]

    if roadmap_phases:
        for phase in roadmap_phases:
            if not isinstance(phase, dict):
                continue

            action_items = phase.get("action_items", [])

            if not isinstance(action_items, list):
                action_items = [str(action_items)]

            action_summary = " &bull; ".join(
                str(item) for item in action_items if item
            )

            phase_name = str(
                phase.get("phase", "")
            )

            duration = str(
                phase.get("duration", "")
            )

            objective = str(
                phase.get("objective", "")
            )

            roadmap_rows.append([
                Paragraph(
                    f"<b>{phase_name}</b>",
                    td_left
                ),
                Paragraph(
                    duration,
                    td_center
                ),
                Paragraph(
                    f"<b>{objective}</b>"
                    + (
                        f"<br/>{action_summary}"
                        if action_summary
                        else ""
                    ),
                    td_left
                )
            ])
    else:
        roadmap_rows.append([
            Paragraph(
                "No roadmap generated",
                td_left
            ),
            Paragraph(
                "-",
                td_center
            ),
            Paragraph(
                "No learning roadmap was returned for the selected role.",
                td_left
            )
        ])

    roadmap_table = Table(
        roadmap_rows,
        colWidths=[140, 82, 310]
    )

    roadmap_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#334155")
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP"
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            5
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            5
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            6
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            6
        ),
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#CBD5E1")
        ),
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#E2E8F0")
        ),
    ]))

    story.append(roadmap_table)

    # -------------------------------------------------------------
    # 7. FOOTER
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=colors.HexColor("#94A3B8"),
            spaceAfter=6
        )
    )

    footer_text = (
        "Generated by Skill-Gap Predictor & Career Navigator | "
        "Comprehensive Student Placement & Competency Report"
    )

    story.append(
        Paragraph(
            footer_text,
            ParagraphStyle(
                "FooterP",
                parent=subtitle_style,
                fontSize=7.5
            )
        )
    )

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()