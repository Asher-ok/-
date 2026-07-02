"""公开文档签字 API（无需登录）"""
import base64
import re
import shutil
import mimetypes
import json
import pytz
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.config import settings
from core.utils.file_utils import get_file_path, build_content_disposition, to_ascii_filename
from shared.models import Customer, CustomerDocument, DocumentSignRequest, Employee, EmployeeDocument, EmployeeContractSignRequest, User
from shared.models.update_notification import touch_business_unread
from shared.models.customer import CUSTOMER_STATUS_ARCHIVED, CUSTOMER_STATUS_PENDING_ARCHIVE, CUSTOMER_STATUS_UNARCHIVED
from shared.models.customer_document import STATUS_SIGNED


router = APIRouter(prefix="/api/public/documents", tags=["公开-文档签字"])


class SignSubmitBody(BaseModel):
    signature_data: str  # data:image/png;base64,xxx
    latitude: float | None = None
    longitude: float | None = None
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
            "title": "Document Signing",
            "sign": "Sign",
            "submit": "Submit",
            "confirm": "Confirm",
            "preview": "Preview",
            "done": "Done",
        }
    return {
        "title": "文档签字",
        "sign": "签字",
        "submit": "提交",
        "confirm": "确认",
        "preview": "预览",
        "done": "完成",
    }


def _t(lang: str, zh: str, en: str) -> str:
    return en if lang == "en" else zh


def _validate_request_for_read(status: str, expires_at: datetime | None, lang: str) -> None:
    if status == "expired":
        raise HTTPException(status_code=400, detail=_t(lang, "签字链接已失效", "Signing link is invalid"))
    if status in ("signed", "completed"):
        return
    if expires_at and expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail=_t(lang, "签字链接已过期", "Signing link has expired"))


def _validate_request_for_write(status: str, expires_at: datetime | None, lang: str) -> None:
    if status == "completed":
        raise HTTPException(status_code=400, detail=_t(lang, "该文档已完成签字", "This document has been completed"))
    if status == "expired":
        raise HTTPException(status_code=400, detail=_t(lang, "签字链接已失效", "Signing link is invalid"))
    if expires_at and expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail=_t(lang, "签字链接已过期", "Signing link has expired"))


def _validate_contract_request_for_write(status: str, expires_at: datetime | None, lang: str) -> None:
    if status == "completed":
        raise HTTPException(status_code=400, detail=_t(lang, "该合同已提交，无法重复签字", "This contract has been submitted and cannot be signed again"))
    if status == "expired":
        raise HTTPException(status_code=400, detail=_t(lang, "签字链接已失效", "Signing link is invalid"))
    if expires_at and expires_at < datetime.utcnow():
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

def _draft_contract_pdf_path(contract_pdf_path: Path, token: str) -> Path:
    safe_token = re.sub(r"[^a-zA-Z0-9_-]+", "", token or "")
    safe_token = safe_token or "draft"
    return contract_pdf_path.with_name(f"{contract_pdf_path.stem}__draft__{safe_token}.pdf")

def _is_draft_mode(request: Request) -> bool:
    raw = (request.query_params.get("draft") or "").strip().lower()
    return raw in ("1", "true", "yes", "y")

def _draft_preview_path(token: str) -> str:
    return f"/api/public/documents/sign/{token}/preview?draft=1"


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
async def get_sign_document_info(
    token: str,
    request: Request,
    lang: str | None = None,
    db: Session = Depends(get_db),
):
    """获取待签字文档信息（公开，无需登录）"""
    resolved_lang = _normalize_lang(lang, request.headers.get("accept-language"))
    req = db.query(DocumentSignRequest).filter(DocumentSignRequest.token == token).first()
    if req:
        _validate_request_for_read(req.status, req.expires_at, resolved_lang)
        doc = db.query(CustomerDocument).filter(CustomerDocument.id == req.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail=_t(resolved_lang, "文档不存在", "Document not found"))
        if not (doc.signed_file_url or doc.file_url):
            raise HTTPException(status_code=400, detail=_t(resolved_lang, "文档文件未就绪", "Document file is not ready"))
        preview_path = f"/api/public/documents/sign/{token}/preview"
        return {
            "lang": resolved_lang,
            "i18n": _ui_texts(resolved_lang),
            "document_name": doc.name,
            "document_type": doc.document_type,
            "preview_url": preview_path,
            "preview_full_url": _absolute_url(request, preview_path),
            "expires_at": req.expires_at.isoformat() if req.expires_at else None,
            "status": req.status,
            "signed_at": doc.signed_at.isoformat() if doc.signed_at else None,
        }

    contract_req = db.query(EmployeeContractSignRequest).filter(EmployeeContractSignRequest.token == token).first()
    if not contract_req:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "签字链接无效或已失效", "Invalid or expired signing link"))
    _validate_request_for_read(contract_req.status, contract_req.expires_at, resolved_lang)

    employee = db.query(Employee).filter(Employee.id == contract_req.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "员工不存在", "Employee not found"))

    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == contract_req.contract_id,
        EmployeeDocument.employee_id == contract_req.employee_id,
        EmployeeDocument.document_type == "contract",
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同不存在", "Contract not found"))
    if not doc.file_url:
        raise HTTPException(status_code=400, detail=_t(resolved_lang, "合同文件未就绪", "Contract file is not ready"))
    preview_path = f"/api/public/documents/sign/{token}/preview"
    return {
        "lang": resolved_lang,
        "i18n": _ui_texts(resolved_lang),
        "document_name": doc.name,
        "document_type": "contract",
        "preview_url": preview_path,
        "preview_full_url": _absolute_url(request, preview_path),
        "expires_at": contract_req.expires_at.isoformat() if contract_req.expires_at else None,
        "status": contract_req.status,
        "employee_name": employee.name,
        "employee_signed_at": doc.employee_signed_at.isoformat() if doc.employee_signed_at else None,
    }


@router.get("/sign/{token}/preview")
async def preview_sign_document(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """预览待签字文档（公开）"""
    resolved_lang = _normalize_lang(None, request.headers.get("accept-language"))
    draft_mode = _is_draft_mode(request)
    req = db.query(DocumentSignRequest).filter(DocumentSignRequest.token == token).first()
    if req:
        _validate_request_for_read(req.status, req.expires_at, resolved_lang)
        doc = db.query(CustomerDocument).filter(CustomerDocument.id == req.document_id).first()
        if not doc or not (doc.signed_file_url or doc.file_url):
            raise HTTPException(status_code=404, detail=_t(resolved_lang, "文档不存在", "Document not found"))
        file_path = None
        for candidate in (doc.signed_file_url, doc.file_url):
            if not candidate:
                continue
            candidate_path = get_file_path(candidate)
            if candidate_path and candidate_path.exists():
                file_path = candidate_path
                break
        if not file_path:
            path_value = doc.signed_file_url or doc.file_url
            file_path = get_file_path(path_value) if path_value else None
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail=_t(resolved_lang, "文件不存在", "File not found"))
        if file_path.suffix.lower() in [".doc", ".docx"]:
            try:
                from modules.houtai.api.employees import _convert_docx_to_pdf_in_place
                file_path = _convert_docx_to_pdf_in_place(file_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=_t(resolved_lang, f"docx转PDF失败: {e}", f"Failed to convert docx to PDF: {e}"))
        if draft_mode and file_path.suffix.lower() == ".pdf":
            draft_path = _draft_contract_pdf_path(file_path, token)
            if draft_path.exists():
                file_path = draft_path
        display_name = doc.name or file_path.name
        if file_path.suffix and not display_name.lower().endswith(file_path.suffix.lower()):
            display_name = f"{display_name}{file_path.suffix}"
        return _file_response_inline(file_path, display_name)

    contract_req = db.query(EmployeeContractSignRequest).filter(EmployeeContractSignRequest.token == token).first()
    if not contract_req:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "签字链接无效或已失效", "Invalid or expired signing link"))
    _validate_request_for_read(contract_req.status, contract_req.expires_at, resolved_lang)

    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == contract_req.contract_id,
        EmployeeDocument.employee_id == contract_req.employee_id,
        EmployeeDocument.document_type == "contract",
    ).first()
    if not doc or not doc.file_url:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同不存在", "Contract not found"))
    file_path = get_file_path(doc.file_url)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "文件不存在", "File not found"))
    if file_path.suffix.lower() in [".doc", ".docx"]:
        try:
            from modules.houtai.api.employees import _convert_docx_to_pdf_in_place
            pdf_path = _convert_docx_to_pdf_in_place(file_path)
            if not pdf_path or not pdf_path.exists():
                raise RuntimeError("未找到转换后的PDF文件")
            file_path = pdf_path
            doc.file_url = str(pdf_path)
            doc.file_type = "pdf"
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=_t(resolved_lang, f"docx转PDF失败: {e}", f"Failed to convert docx to PDF: {e}"))
    if draft_mode and file_path.suffix.lower() == ".pdf":
        draft_path = _draft_contract_pdf_path(file_path, token)
        if draft_path.exists():
            file_path = draft_path
    display_name = doc.name or file_path.name
    if file_path.suffix and not display_name.lower().endswith(file_path.suffix.lower()):
        display_name = f"{display_name}{file_path.suffix}"
    return _file_response_inline(file_path, display_name)


@router.post("/sign/{token}")
async def submit_document_signature(
    token: str,
    body: SignSubmitBody,
    request: Request,
    lang: str | None = None,
    db: Session = Depends(get_db),
):
    """提交签字（公开，无需登录）"""
    resolved_lang = _normalize_lang(lang, request.headers.get("accept-language"))
    req = db.query(DocumentSignRequest).filter(DocumentSignRequest.token == token).first()
    try:
        signature_mime, signature_blob = _parse_data_url(body.signature_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if req:
        _validate_request_for_write(req.status, req.expires_at, resolved_lang)
        doc = db.query(CustomerDocument).filter(CustomerDocument.id == req.document_id).first()
        if not doc or not doc.file_url:
            raise HTTPException(status_code=404, detail=_t(resolved_lang, "文档不存在", "Document not found"))
        source_field = "file_url"
        base_value = doc.file_url
        if getattr(doc, "signed_file_url", None):
            signed_path = get_file_path(doc.signed_file_url)
            if signed_path and signed_path.exists():
                base_value = doc.signed_file_url
                source_field = "signed_file_url"
        file_path = get_file_path(base_value)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail=_t(resolved_lang, "文档文件不存在", "Document file not found"))
        if file_path.suffix.lower() in [".doc", ".docx"]:
            from modules.houtai.api.employees import _convert_docx_to_pdf_in_place
            pdf_path = _convert_docx_to_pdf_in_place(file_path)
            if not pdf_path or not pdf_path.exists():
                raise HTTPException(status_code=500, detail=_t(resolved_lang, "docx转PDF失败", "Failed to convert docx to PDF"))
            file_path = pdf_path
            if source_field == "signed_file_url":
                doc.signed_file_url = str(pdf_path)
            else:
                doc.file_url = str(pdf_path)
                doc.file_type = "pdf"
            db.commit()
        if file_path.suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail=_t(resolved_lang, "暂不支持该文件类型的签字", "Signing is not supported for this file type"))
        if body.x is None or body.y is None or body.width is None or body.height is None:
            raise HTTPException(status_code=400, detail=_t(resolved_lang, "签字位置缺失，请先框选签字位置", "Missing signature position. Please select a position first."))
        # 抓取澳洲时间并格式化为 YYYY/MM/DD
        try:
            sydney_tz = pytz.timezone('Australia/Sydney')
            now_sydney = datetime.now(sydney_tz)
            date_text = now_sydney.strftime("%Y/%m/%d")
        except Exception:
            date_text = datetime.now().strftime("%Y/%m/%d")

        from modules.houtai.api.employees import _embed_signature_to_pdf
        draft_path = _draft_contract_pdf_path(file_path, token)
        try:
            if draft_path.exists():
                draft_path.unlink(missing_ok=True)
        except Exception:
            pass
        shutil.copy2(str(file_path), str(draft_path))
        success = _embed_signature_to_pdf(
            draft_path,
            signature_blob,
            "client",
            x=body.x,
            y=body.y,
            width=body.width,
            height=body.height,
            page_index=body.page or 0,
            date_text=date_text,
        )
        if not success:
            draft_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=_t(resolved_lang, "签字嵌入失败", "Failed to embed signature"))

        preview_path = _draft_preview_path(token)
        return {
            "lang": resolved_lang,
            "i18n": _ui_texts(resolved_lang),
            "message": _t(resolved_lang, "签名已保存为预览，请确认提交完成签字", "Signature saved for preview. Please confirm to complete signing."),
            "preview_url": preview_path,
            "preview_full_url": _absolute_url(request, preview_path),
            "status": req.status,
        }

    contract_req = db.query(EmployeeContractSignRequest).filter(EmployeeContractSignRequest.token == token).first()
    if not contract_req:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "签字链接无效或已失效", "Invalid or expired signing link"))
    _validate_contract_request_for_write(contract_req.status, contract_req.expires_at, resolved_lang)

    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == contract_req.contract_id,
        EmployeeDocument.employee_id == contract_req.employee_id,
        EmployeeDocument.document_type == "contract",
    ).first()
    if not doc or not doc.file_url:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同不存在", "Contract not found"))
    file_path = get_file_path(doc.file_url)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同文件不存在", "Contract file not found"))

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

    if body.x is None or body.y is None or body.width is None or body.height is None:
        raise HTTPException(status_code=400, detail=_t(resolved_lang, "签字位置缺失，请先框选签字位置", "Missing signature position. Please select a position first."))

    # 抓取澳洲时间并格式化为 YYYY/MM/DD
    try:
        sydney_tz = pytz.timezone('Australia/Sydney')
        now_sydney = datetime.now(sydney_tz)
        date_text = now_sydney.strftime("%Y/%m/%d")
    except Exception:
        date_text = datetime.now().strftime("%Y/%m/%d")

    from modules.houtai.api.employees import _embed_signature_to_pdf
    draft_path = _draft_contract_pdf_path(contract_path, token)
    try:
        if draft_path.exists():
            draft_path.unlink(missing_ok=True)
    except Exception:
        pass
    shutil.copy2(str(contract_path), str(draft_path))
    embed_success = _embed_signature_to_pdf(
        draft_path,
        signature_blob,
        "employee",
        x=body.x,
        y=body.y,
        width=body.width,
        height=body.height,
        page_index=body.page or 0,
        date_text=date_text,
    )
    if embed_success is False:
        draft_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=_t(resolved_lang, "签字嵌入失败", "Failed to embed signature"))

    preview_path = _draft_preview_path(token)
    return {
        "lang": resolved_lang,
        "i18n": _ui_texts(resolved_lang),
        "message": _t(resolved_lang, "签名已保存为预览，请确认提交完成签字", "Signature saved for preview. Please confirm to complete signing."),
        "preview_url": preview_path,
        "preview_full_url": _absolute_url(request, preview_path),
        "status": contract_req.status,
    }


@router.post("/sign/{token}/confirm")
async def confirm_document_signature(
    token: str,
    request: Request,
    lang: str | None = None,
    db: Session = Depends(get_db),
):
    """确认提交（只有确认提交才算签字完成）"""
    resolved_lang = _normalize_lang(lang, request.headers.get("accept-language"))
    req = db.query(DocumentSignRequest).filter(DocumentSignRequest.token == token).first()
    if req:
        if req.status == "completed":
            return {"lang": resolved_lang, "i18n": _ui_texts(resolved_lang), "message": _t(resolved_lang, "提交成功", "Submitted successfully"), "status": req.status}
        _validate_request_for_write(req.status, req.expires_at, resolved_lang)
        doc = db.query(CustomerDocument).filter(CustomerDocument.id == req.document_id).first()
        if not doc or not doc.file_url:
            raise HTTPException(status_code=404, detail=_t(resolved_lang, "文档不存在", "Document not found"))
        source_field = "file_url"
        base_value = doc.file_url
        if getattr(doc, "signed_file_url", None):
            signed_path = get_file_path(doc.signed_file_url)
            if signed_path and signed_path.exists():
                base_value = doc.signed_file_url
                source_field = "signed_file_url"
        file_path = get_file_path(base_value)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail=_t(resolved_lang, "文档文件不存在", "Document file not found"))
        if file_path.suffix.lower() in [".doc", ".docx"]:
            from modules.houtai.api.employees import _convert_docx_to_pdf_in_place
            pdf_path = _convert_docx_to_pdf_in_place(file_path)
            if not pdf_path or not pdf_path.exists():
                raise HTTPException(status_code=500, detail=_t(resolved_lang, "docx转PDF失败", "Failed to convert docx to PDF"))
            file_path = pdf_path
            if source_field == "signed_file_url":
                doc.signed_file_url = str(pdf_path)
            else:
                doc.file_url = str(pdf_path)
                doc.file_type = "pdf"

        if file_path.suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail=_t(resolved_lang, "暂不支持该文件类型的签字", "Signing is not supported for this file type"))

        draft_path = _draft_contract_pdf_path(file_path, token)
        if not draft_path.exists():
            raise HTTPException(status_code=400, detail=_t(resolved_lang, "请先保存签名预览", "Please save signature preview first"))

        from core.utils.file_utils import ensure_upload_dir
        ensure_upload_dir()
        out_folder = Path(settings.upload_dir) / "customers" / req.customer_id / "documents"
        out_folder.mkdir(parents=True, exist_ok=True)
        out_filename = f"signed_{Path(file_path).stem}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        out_path = out_folder / out_filename
        shutil.copy2(str(draft_path), str(out_path))

        doc.signed_file_url = str(out_path.absolute())
        doc.status = STATUS_SIGNED
        doc.signed_at = datetime.utcnow()
        req.status = "completed"
        req.signed_at = datetime.utcnow()
        if doc.document_type == "service_agreement":
            customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
            if customer and getattr(customer, "customer_status", None) != CUSTOMER_STATUS_ARCHIVED:
                current_status = getattr(customer, "customer_status", None)
                if current_status in (None, "", CUSTOMER_STATUS_UNARCHIVED):
                    customer.customer_status = CUSTOMER_STATUS_PENDING_ARCHIVE
                elif current_status != CUSTOMER_STATUS_PENDING_ARCHIVE:
                    customer.customer_status = CUSTOMER_STATUS_PENDING_ARCHIVE
        db.commit()

        try:
            draft_path.unlink(missing_ok=True)
        except Exception:
            pass

        try:
            pending_customer_id = None
            customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
            if customer and str(getattr(customer, "customer_status", "") or "") == CUSTOMER_STATUS_PENDING_ARCHIVE:
                pending_customer_id = str(req.customer_id)
            admin_users = db.query(User).filter(or_(User.is_active == True, User.is_active.is_(None))).all()
            for u in admin_users:
                if pending_customer_id:
                    touch_business_unread(
                        db,
                        business_code="customer_pending",
                        receiver_user_id=str(u.id),
                        data_id=pending_customer_id,
                        scope_id=CUSTOMER_STATUS_PENDING_ARCHIVE,
                    )
                else:
                    touch_business_unread(
                        db,
                        business_code="customer",
                        receiver_user_id=str(u.id),
                        data_id=str(req.customer_id),
                    )
            db.commit()
        except Exception:
            db.rollback()

        return {"lang": resolved_lang, "i18n": _ui_texts(resolved_lang), "message": _t(resolved_lang, "提交成功", "Submitted successfully"), "status": req.status}

    contract_req = db.query(EmployeeContractSignRequest).filter(EmployeeContractSignRequest.token == token).first()
    if not contract_req:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "签字链接无效或已失效", "Invalid or expired signing link"))

    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == contract_req.contract_id,
        EmployeeDocument.employee_id == contract_req.employee_id,
        EmployeeDocument.document_type == "contract",
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同不存在", "Contract not found"))

    if contract_req.status == "completed" and doc.employee_signed_at:
        return {"lang": resolved_lang, "i18n": _ui_texts(resolved_lang), "message": _t(resolved_lang, "提交成功", "Submitted successfully"), "employee_signed_at": doc.employee_signed_at.isoformat()}
    _validate_contract_request_for_write(contract_req.status, contract_req.expires_at, resolved_lang)

    contract_path = get_file_path(doc.file_url) if getattr(doc, "file_url", None) else None
    if not contract_path or not contract_path.exists():
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同文件不存在", "Contract file not found"))
    if contract_path.suffix.lower() in [".doc", ".docx"]:
        from modules.houtai.api.employees import _convert_docx_to_pdf_in_place
        pdf_path = _convert_docx_to_pdf_in_place(contract_path)
        if not pdf_path or not pdf_path.exists():
            raise HTTPException(status_code=500, detail=_t(resolved_lang, "docx转PDF失败", "Failed to convert docx to PDF"))
        contract_path = pdf_path
        doc.file_url = str(pdf_path)
        doc.file_type = "pdf"

    if contract_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail=_t(resolved_lang, "暂不支持该文件类型的签字", "Signing is not supported for this file type"))

    draft_path = _draft_contract_pdf_path(contract_path, token)
    if not draft_path.exists():
        raise HTTPException(status_code=400, detail=_t(resolved_lang, "请先保存签名预览", "Please save signature preview first"))
    from core.utils.file_utils import ensure_upload_dir, save_upload_file
    ensure_upload_dir()
    signed_bytes = draft_path.read_bytes()
    out_filename = f"signed_{Path(contract_path).stem}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    out_file_url = await save_upload_file(signed_bytes, out_filename, subfolder="employee_contracts")
    doc.file_url = out_file_url
    doc.file_type = "pdf"
    try:
        if doc.name and doc.name.lower().endswith((".doc", ".docx")):
            doc.name = f"{Path(doc.name).stem}.pdf"
    except Exception:
        pass
    try:
        draft_path.unlink(missing_ok=True)
    except Exception:
        pass

    if not doc.employee_signed_at:
        doc.employee_signed_at = datetime.utcnow()
    contract_req.status = "completed"
    contract_req.signed_at = datetime.utcnow()
    db.commit()

    try:
        admin_users = db.query(User).filter(or_(User.is_active == True, User.is_active.is_(None))).all()
        for u in admin_users:
            touch_business_unread(
                db,
                business_code="employee",
                receiver_user_id=str(u.id),
                data_id=str(contract_req.employee_id),
                scope_id=str(contract_req.employee_id),
            )
        db.commit()
    except Exception:
        db.rollback()

    return {"lang": resolved_lang, "i18n": _ui_texts(resolved_lang), "message": _t(resolved_lang, "提交成功", "Submitted successfully"), "employee_signed_at": doc.employee_signed_at.isoformat() if doc.employee_signed_at else None, "status": contract_req.status}


@router.post("/sign/{token}/discard")
async def discard_document_signature(
    token: str,
    request: Request,
    lang: str | None = None,
    db: Session = Depends(get_db),
):
    resolved_lang = _normalize_lang(lang, request.headers.get("accept-language"))
    req = db.query(DocumentSignRequest).filter(DocumentSignRequest.token == token).first()
    if req:
        doc = db.query(CustomerDocument).filter(CustomerDocument.id == req.document_id).first()
        if not doc or not doc.file_url:
            raise HTTPException(status_code=404, detail=_t(resolved_lang, "文档不存在", "Document not found"))
        source_field = "file_url"
        base_value = doc.file_url
        if getattr(doc, "signed_file_url", None):
            signed_path = get_file_path(doc.signed_file_url)
            if signed_path and signed_path.exists():
                base_value = doc.signed_file_url
                source_field = "signed_file_url"
        file_path = get_file_path(base_value)
        if file_path and file_path.exists() and file_path.suffix.lower() in [".doc", ".docx"]:
            try:
                from modules.houtai.api.employees import _convert_docx_to_pdf_in_place
                pdf_path = _convert_docx_to_pdf_in_place(file_path)
                if pdf_path and pdf_path.exists():
                    file_path = pdf_path
                    if source_field == "signed_file_url":
                        doc.signed_file_url = str(pdf_path)
                    else:
                        doc.file_url = str(pdf_path)
                        doc.file_type = "pdf"
                    db.commit()
            except Exception:
                pass
        if file_path and file_path.exists() and file_path.suffix.lower() == ".pdf":
            draft_path = _draft_contract_pdf_path(file_path, token)
            try:
                draft_path.unlink(missing_ok=True)
            except Exception:
                pass
        return {"lang": resolved_lang, "i18n": _ui_texts(resolved_lang), "message": _t(resolved_lang, "已取消预览签名", "Preview signature discarded")}


    contract_req = db.query(EmployeeContractSignRequest).filter(EmployeeContractSignRequest.token == token).first()
    if not contract_req:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "签字链接无效或已失效", "Invalid or expired signing link"))
    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == contract_req.contract_id,
        EmployeeDocument.employee_id == contract_req.employee_id,
        EmployeeDocument.document_type == "contract",
    ).first()
    if not doc or not doc.file_url:
        raise HTTPException(status_code=404, detail=_t(resolved_lang, "合同不存在", "Contract not found"))
    file_path = get_file_path(doc.file_url)
    if file_path and file_path.exists() and file_path.suffix.lower() in [".doc", ".docx"]:
        try:
            from modules.houtai.api.employees import _convert_docx_to_pdf_in_place
            pdf_path = _convert_docx_to_pdf_in_place(file_path)
            if pdf_path and pdf_path.exists():
                file_path = pdf_path
                doc.file_url = str(pdf_path)
                doc.file_type = "pdf"
                db.commit()
        except Exception:
            pass
    if file_path and file_path.exists() and file_path.suffix.lower() == ".pdf":
        draft_path = _draft_contract_pdf_path(file_path, token)
        try:
            draft_path.unlink(missing_ok=True)
        except Exception:
            pass
    return {"lang": resolved_lang, "i18n": _ui_texts(resolved_lang), "message": _t(resolved_lang, "已取消预览签名", "Preview signature discarded")}
