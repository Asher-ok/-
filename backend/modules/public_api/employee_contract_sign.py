"""公开员工合同签字 API（无需登录）"""
import base64
import re
import mimetypes
from pathlib import Path
from datetime import datetime
import json
import pytz

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.utils.file_utils import get_file_path, build_content_disposition, to_ascii_filename
from shared.models import Employee, EmployeeDocument, EmployeeContractSignRequest, User
from shared.models.update_notification import touch_business_unread


router = APIRouter(prefix="/api/public/employee-contracts", tags=["公开-员工合同签字"])


class EmployeeContractSignSubmitBody(BaseModel):
    signature_data: str
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    page: int | None = None


def _parse_data_url(data_url: str) -> tuple[str, bytes]:
    match = re.match(r"^data:(.+?);base64,(.+)$", data_url)
    if not match:
        raise ValueError("Invalid signature data format")
    mime = match.group(1)
    data = base64.b64decode(match.group(2))
    return mime, data


def _normalize_lang(value: str | None, accept: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw and accept:
        raw = str(accept).split(",", 1)[0].strip().lower()
    if raw in ("zh", "zh-cn", "zh_hans", "cn", "chinese", "中文", "简体中文"):
        return "zh"
    if raw in ("en", "en-us", "en-gb", "english", "英文"):
        return "en"
    if raw.startswith("zh"):
        return "zh"
    if raw.startswith("en"):
        return "en"
    return "zh"


def _ui_texts(lang: str) -> dict:
    if lang == "en":
        return {
            "title": "Contract Signing",
            "sign": "Sign",
            "submit": "Submit",
            "confirm": "Confirm",
            "preview": "Preview",
            "done": "Done",
        }
    return {
        "title": "合同签字",
        "sign": "签字",
        "submit": "提交",
        "confirm": "确认",
        "preview": "预览",
        "done": "完成",
    }


def _t(lang: str, zh: str, en: str) -> str:
    return en if lang == "en" else zh


def _get_active_request_or_400(req: EmployeeContractSignRequest, lang: str) -> None:
    if req.status == "completed":
        raise HTTPException(status_code=400, detail=_t(lang, "该合同已提交，无法重复签字", "This contract has been submitted and cannot be signed again"))
    if req.status == "expired":
        raise HTTPException(status_code=400, detail=_t(lang, "签字链接已失效", "Signing link is invalid"))
    if req.expires_at and req.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail=_t(lang, "签字链接已过期", "Signing link has expired"))


def _file_response_inline(file_path: Path, display_name: str) -> FileResponse:
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "application/octet-stream"
    if file_path.suffix.lower() == ".pdf":
        mime_type = "application/pdf"
    ascii_filename = to_ascii_filename(display_name or file_path.name)
    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=ascii_filename,
        headers={
            "Content-Disposition": build_content_disposition(display_name or file_path.name, "inline"),
            "X-Frame-Options": "ALLOWALL",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


def _external_origin(request: Request) -> str:
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    forwarded_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}".rstrip("/")
    return str(request.base_url).rstrip("/")


def _absolute_url(request: Request, path: str) -> str:
    clean_path = "/" + path.lstrip("/")
    return f"{_external_origin(request)}{clean_path}"



@router.get("/sign/{token}")
async def get_contract_sign_info(
    token: str,
    request: Request,
    lang: str | None = None,
    db: Session = Depends(get_db),
):
    resolved_lang = _normalize_lang(lang, request.headers.get("accept-language"))
    req = db.query(EmployeeContractSignRequest).filter(EmployeeContractSignRequest.token == token).first()
    if not req:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "签字链接无效或已失效", "Invalid or expired signing link"))
    _get_active_request_or_400(req, resolved_lang)

    employee = db.query(Employee).filter(Employee.id == req.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "员工不存在", "Employee not found"))

    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == req.contract_id,
        EmployeeDocument.employee_id == req.employee_id,
        EmployeeDocument.document_type == "contract",
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同不存在", "Contract not found"))
    if not doc.file_url:
        raise HTTPException(status_code=400, detail=_t(resolved_lang, "合同文件未就绪", "Contract file is not ready"))

    preview_path = f"/api/public/employee-contracts/sign/{token}/preview"
    return {
        "lang": resolved_lang,
        "i18n": _ui_texts(resolved_lang),
        "employee_name": employee.name,
        "contract_id": doc.id,
        "contract_name": doc.name,
        "preview_url": preview_path,
        "preview_full_url": _absolute_url(request, preview_path),
        "expires_at": req.expires_at.isoformat() if req.expires_at else None,
        "employee_signed_at": doc.employee_signed_at.isoformat() if doc.employee_signed_at else None,
    }


@router.get("/sign/{token}/preview")
async def preview_contract_to_sign(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    resolved_lang = _normalize_lang(None, request.headers.get("accept-language"))
    req = db.query(EmployeeContractSignRequest).filter(EmployeeContractSignRequest.token == token).first()
    if not req:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "签字链接无效或已失效", "Invalid or expired signing link"))
    _get_active_request_or_400(req, resolved_lang)

    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == req.contract_id,
        EmployeeDocument.employee_id == req.employee_id,
        EmployeeDocument.document_type == "contract",
    ).first()
    if not doc or not doc.file_url:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同不存在", "Contract not found"))

    file_path = get_file_path(doc.file_url)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "文件不存在", "File not found"))

    if file_path.suffix.lower() in [".doc", ".docx"]:
        try:
            from modules.app.api.employees import _convert_docx_to_pdf_in_place

            pdf_path = _convert_docx_to_pdf_in_place(file_path)
            if not pdf_path or not pdf_path.exists():
                raise RuntimeError("未找到转换后的PDF文件")
            file_path = pdf_path
            doc.file_url = str(pdf_path)
            doc.file_type = "pdf"
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=_t(resolved_lang, f"docx转PDF失败: {e}", f"Failed to convert docx to PDF: {e}"))

    display_name = doc.name or file_path.name
    if file_path.suffix and not display_name.lower().endswith(file_path.suffix.lower()):
        display_name = f"{display_name}{file_path.suffix}"
    return _file_response_inline(file_path, display_name)


@router.post("/sign/{token}")
async def submit_contract_signature(
    token: str,
    body: EmployeeContractSignSubmitBody,
    request: Request,
    lang: str | None = None,
    db: Session = Depends(get_db),
):
    resolved_lang = _normalize_lang(lang, request.headers.get("accept-language"))
    req = db.query(EmployeeContractSignRequest).filter(EmployeeContractSignRequest.token == token).first()
    if not req:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "签字链接无效或已失效", "Invalid or expired signing link"))
    _get_active_request_or_400(req, resolved_lang)

    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == req.contract_id,
        EmployeeDocument.employee_id == req.employee_id,
        EmployeeDocument.document_type == "contract",
    ).first()
    if not doc or not doc.file_url:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同不存在", "Contract not found"))

    try:
        mime, signature_blob = _parse_data_url(body.signature_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_path = get_file_path(doc.file_url)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同文件不存在", "Contract file not found"))

    doc.employee_signature_blob = signature_blob
    doc.employee_signature_mime = mime or "image/png"
    doc.employee_signed_at = datetime.utcnow()
    if body.x is not None:
        doc.employee_signature_x = body.x
    if body.y is not None:
        doc.employee_signature_y = body.y
    if body.width is not None:
        doc.employee_signature_width = body.width
    if body.height is not None:
        doc.employee_signature_height = body.height
    if body.page is not None:
        doc.employee_signature_page = body.page

    contract_path = file_path
    if contract_path.suffix.lower() in [".doc", ".docx"]:
        from modules.houtai.api.employees import _convert_docx_to_pdf_in_place

        pdf_path = _convert_docx_to_pdf_in_place(contract_path)
        if not pdf_path or not pdf_path.exists():
            raise HTTPException(status_code=500, detail="docx转PDF失败：转换后的文件不存在")
        contract_path = pdf_path
        doc.file_url = str(pdf_path)
        doc.file_type = "pdf"

    if contract_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail=_t(resolved_lang, "暂不支持该文件类型的签字", "Signing is not supported for this file type"))

    # 抓取澳洲时间并格式化为 YYYY/MM/DD
    try:
        sydney_tz = pytz.timezone('Australia/Sydney')
        now_sydney = datetime.now(sydney_tz)
        date_text = now_sydney.strftime("%Y/%m/%d")
    except Exception:
        date_text = datetime.now().strftime("%Y/%m/%d")

    from modules.houtai.api.employees import _embed_signature_to_pdf

    embed_success = _embed_signature_to_pdf(
        contract_path,
        signature_blob,
        "employee",
        x=doc.employee_signature_x,
        y=doc.employee_signature_y,
        width=doc.employee_signature_width,
        height=doc.employee_signature_height,
        page_index=doc.employee_signature_page or 0,
        date_text=date_text,
    )
    if embed_success is False:
        raise HTTPException(status_code=500, detail=_t(resolved_lang, "签字嵌入失败", "Failed to embed signature"))

    req.status = "signed"
    req.signed_at = datetime.utcnow()
    db.commit()

    try:
        admin_users = db.query(User).filter(or_(User.is_active == True, User.is_active.is_(None))).all()
        for u in admin_users:
            touch_business_unread(
                db,
                business_code="employee",
                receiver_user_id=str(u.id),
                data_id=str(req.employee_id),
                scope_id=str(req.employee_id),
            )
        db.commit()
    except Exception:
        db.rollback()

    return {
        "lang": resolved_lang,
        "i18n": _ui_texts(resolved_lang),
        "message": _t(resolved_lang, "签字已完成", "Signing completed"),
        "employee_signed_at": doc.employee_signed_at.isoformat() if doc.employee_signed_at else None,
        "contract_id": doc.id,
    }
