"""
官网模块 API 路由
"""
import logging

from fastapi import APIRouter, HTTPException

from core.config import settings
from core.utils.email import send_contact_email
from ..schemas.contact import ContactForm

router = APIRouter(prefix="/api/guanwang", tags=["官网"])
logger = logging.getLogger(__name__)


@router.get("")
async def guanwang_home():
    """官网API占位"""
    return {"message": "官网后端API（待开发）"}


@router.post("/contact")
async def submit_contact(form: ContactForm):
    """官网联系表单提交"""
    subject = f"官网表单留言 - {form.name}"
    html_body = f"""
    <h2>官网表单留言</h2>
    <p><strong>姓名：</strong>{form.name}</p>
    <p><strong>电话：</strong>{form.phone}</p>
    <p><strong>邮箱：</strong>{form.email}</p>
    <p><strong>区域：</strong>{form.suburb}</p>
    <p><strong>留言：</strong>{form.message}</p>
    """
    plain_body = (
        f"官网表单留言\n"
        f"姓名：{form.name}\n"
        f"电话：{form.phone}\n"
        f"邮箱：{form.email}\n"
        f"区域：{form.suburb}\n"
        f"留言：{form.message}\n"
    )

    try:
        to_emails = [e.strip() for e in (settings.contact_to_emails or "").split(",") if e.strip()]
        cc_emails = [e.strip() for e in (settings.contact_cc_emails or "").split(",") if e.strip()]
        recipients = to_emails + [e for e in cc_emails if e not in to_emails]
        if not recipients:
            recipients = ["enquiry@empowerhub.com.au"]
        send_contact_email(
            subject=subject,
            html_body=html_body,
            plain_body=plain_body,
            to_emails=recipients,
        )
    except Exception as exc:
        logger.exception("邮件发送失败")
        raise HTTPException(status_code=500, detail=f"邮件发送失败：{exc}") from exc

    return {"message": "提交成功"}
