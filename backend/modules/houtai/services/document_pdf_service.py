"""从 form_data 生成 PDF 文件"""
from pathlib import Path
from typing import Any, Optional
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def _flatten_form_data(obj: Any, prefix: str = "") -> list[tuple[str, str]]:
    """将 form_data 展平为 (key, value) 列表用于 PDF 展示"""
    result = []
    if obj is None:
        return result
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}{k}" if prefix else k
            if isinstance(v, (dict, list)):
                result.extend(_flatten_form_data(v, f"{key}."))
            elif v is not None and v != "":
                result.append((key, str(v)))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            result.extend(_flatten_form_data(item, f"{prefix}[{i}]."))
    return result


def generate_document_pdf(
    doc_name: str,
    document_type: str,
    form_data: Optional[dict],
    output_path: str,
) -> str:
    """
    根据 form_data 生成 PDF 并保存到 output_path。
    返回保存后的完整文件路径。
    """
    if not form_data:
        raise ValueError("form_data 不能为空，请先填写表单")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="DocTitle",
        parent=styles["Heading1"],
        fontSize=16,
    )
    content = []

    content.append(Paragraph(doc_name or document_type, title_style))
    content.append(Spacer(1, 12))

    items = _flatten_form_data(form_data)
    for key, value in items:
        key_display = key.replace("_", " ").title()
        para = Paragraph(
            f"<b>{key_display}:</b> {value.replace('<', '&lt;').replace('>', '&gt;')}",
            styles["Normal"],
        )
        content.append(para)
        content.append(Spacer(1, 6))

    doc.build(content)
    return str(path)
