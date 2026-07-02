from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from typing import Any, Dict, List


def _get_type_label(question_type: str) -> str:
    mapping = {
        "single_choice": "单选",
        "multiple_choice": "多选",
        "text": "文本",
        "number": "数字",
        "date": "日期"
    }
    return mapping.get(question_type, question_type or "")


def _build_option_lines(question: Any, answers: Dict[str, Any]) -> List[str]:
    value = answers.get(question.id) if answers else None
    selected = set()
    if question.type == "multiple_choice":
        if isinstance(value, list):
            selected = {str(item) for item in value}
        elif value is not None:
            selected = {str(value)}
    elif question.type == "single_choice":
        if value is not None:
            selected = {str(value)}

    lines = []
    options = question.options or []
    for option in options:
        option_id = option.get("id") if option else None
        option_text = option.get("text") if option else ""
        marker = "[√]" if str(option_id) in selected or str(option_text) in selected else "[ ]"
        lines.append(f"{marker} {option_text}")
    return lines


def generate_questionnaire_response_pdf(response: Any, output_path: str) -> None:
    """生成问卷提交记录 PDF（中文）"""
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    base_style = ParagraphStyle(
        "ChineseBase",
        parent=styles["Normal"],
        fontName="STSong-Light",
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        alignment=TA_LEFT
    )
    title_style = ParagraphStyle(
        "Title",
        parent=base_style,
        fontSize=18,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=16,
        alignment=TA_CENTER
    )
    label_style = ParagraphStyle(
        "Label",
        parent=base_style
    )
    section_style = ParagraphStyle(
        "Section",
        parent=base_style,
        fontSize=14,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=8
    )

    story.append(Paragraph("问卷提交记录", title_style))

    info_rows = [
        [Paragraph("问卷", label_style),
         Paragraph(response.questionnaire.title if response.questionnaire else "", label_style)],
        [Paragraph("客户", label_style),
         Paragraph(response.customer.name if response.customer else "", label_style)],
        [Paragraph("员工", label_style),
         Paragraph(response.employee.name if response.employee else "", label_style)],
        [Paragraph("任务", label_style),
         Paragraph(response.task.title if response.task else "", label_style)],
        [Paragraph("提交时间", label_style),
         Paragraph(str(response.submitted_at) if response.submitted_at else "", label_style)],
    ]

    info_table = Table(info_rows, colWidths=[45 * mm, 130 * mm])
    info_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("回答", section_style))
    story.append(Spacer(1, 8))

    answers = response.answers or {}
    questions = response.questionnaire.questions if response.questionnaire else []
    for index, question in enumerate(questions, start=1):
        q_title = f"Q{index}. {question.title}"
        type_label = _get_type_label(question.type)
        required_label = "必填" if question.required else "非必填"
        story.append(Paragraph(q_title, base_style))
        story.append(Paragraph(f"类型：{type_label}（{required_label}）", base_style))

        if question.type in ("single_choice", "multiple_choice"):
            option_lines = _build_option_lines(question, answers)
            for line in option_lines:
                story.append(Paragraph(line, base_style))
        else:
            value = answers.get(question.id) if answers else None
            answer_text = str(value) if value is not None else "—"
            story.append(Paragraph(f"回答：{answer_text}", base_style))

        story.append(Spacer(1, 8))

    doc.build(story)
