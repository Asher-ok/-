"""客户文档 CRUD API"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid
import mimetypes
import shutil

from core.database import get_db
from core.config import settings
from core.utils.file_utils import (
    save_upload_file,
    get_file_path,
    ensure_upload_dir,
    build_content_disposition,
    to_ascii_filename,
)
from shared.models import Customer, CustomerDocument, DocumentSignRequest
from shared.models.customer_document import DOCUMENT_TYPES, STATUS_DRAFT, STATUS_PENDING_SIGN
from shared.models import User
from shared.models.update_notification import touch_business_unread
from ..schemas.customer_document import (
    CustomerDocumentCreate,
    CustomerDocumentUpdate,
    CustomerDocumentResponse,
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/houtai/customers", tags=["管理-客户文档"])

def _resolve_soffice_executable() -> str | None:
    try:
        from modules.houtai.api.employees import _resolve_soffice_executable as _resolve
        return _resolve()
    except Exception:
        return None


def _convert_office_file_to_pdf(source: Path, out_dir: Path) -> Path | None:
    soffice = _resolve_soffice_executable()
    if not soffice:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    soffice_dir = str(Path(soffice).resolve().parent)
    import subprocess

    cmd = [
        soffice,
        "--headless",
        "--nologo",
        "--nolockcheck",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(source),
    ]
    proc = subprocess.run(cmd, cwd=soffice_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        return None
    expected = out_dir / f"{source.stem}.pdf"
    if expected.exists():
        return expected
    candidates = list(out_dir.glob(f"{source.stem}.*"))
    for c in candidates:
        if c.suffix.lower() == ".pdf":
            return c
    return None


def _parse_form_data(raw: str) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return None


@router.get("/{customer_id}/documents", response_model=List[CustomerDocumentResponse])
async def list_customer_documents(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取客户文档列表"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    docs = db.query(CustomerDocument).filter(CustomerDocument.customer_id == customer_id).all()
    return [
        CustomerDocumentResponse(
            id=d.id,
            customer_id=d.customer_id,
            document_type=d.document_type,
            name=d.name,
            file_type=d.file_type,
            file_url=d.file_url,
            form_data=_parse_form_data(d.form_data),
            status=d.status,
            signed_at=d.signed_at,
            signed_file_url=d.signed_file_url,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in docs
    ]


@router.post("/{customer_id}/documents", response_model=CustomerDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_document(
    customer_id: str,
    data: CustomerDocumentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建客户文档"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    if data.document_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="无效的文档类型")
    doc = CustomerDocument(
        customer_id=customer_id,
        document_type=data.document_type,
        name=data.name,
        file_type=data.file_type,
        form_data=json.dumps(data.form_data, ensure_ascii=False) if data.form_data else None,
        status=STATUS_DRAFT,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return CustomerDocumentResponse(
        id=doc.id,
        customer_id=doc.customer_id,
        document_type=doc.document_type,
        name=doc.name,
        file_type=doc.file_type,
        file_url=doc.file_url,
        form_data=_parse_form_data(doc.form_data),
        status=doc.status,
        signed_at=doc.signed_at,
        signed_file_url=doc.signed_file_url,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/{customer_id}/documents/{doc_id}", response_model=CustomerDocumentResponse)
async def get_customer_document(
    customer_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取客户文档详情"""
    doc = db.query(CustomerDocument).filter(
        CustomerDocument.id == doc_id,
        CustomerDocument.customer_id == customer_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return CustomerDocumentResponse(
        id=doc.id,
        customer_id=doc.customer_id,
        document_type=doc.document_type,
        name=doc.name,
        file_type=doc.file_type,
        file_url=doc.file_url,
        form_data=_parse_form_data(doc.form_data),
        status=doc.status,
        signed_at=doc.signed_at,
        signed_file_url=doc.signed_file_url,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.put("/{customer_id}/documents/{doc_id}", response_model=CustomerDocumentResponse)
async def update_customer_document(
    customer_id: str,
    doc_id: str,
    data: CustomerDocumentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新客户文档"""
    doc = db.query(CustomerDocument).filter(
        CustomerDocument.id == doc_id,
        CustomerDocument.customer_id == customer_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "form_data" in update_data and update_data["form_data"] is not None:
        doc.form_data = json.dumps(update_data["form_data"], ensure_ascii=False)
        del update_data["form_data"]
    for key, value in update_data.items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return CustomerDocumentResponse(
        id=doc.id,
        customer_id=doc.customer_id,
        document_type=doc.document_type,
        name=doc.name,
        file_type=doc.file_type,
        file_url=doc.file_url,
        form_data=_parse_form_data(doc.form_data),
        status=doc.status,
        signed_at=doc.signed_at,
        signed_file_url=doc.signed_file_url,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.delete("/{customer_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_document(
    customer_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除客户文档"""
    doc = db.query(CustomerDocument).filter(
        CustomerDocument.id == doc_id,
        CustomerDocument.customer_id == customer_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    db.delete(doc)
    db.commit()
    return None


@router.post("/{customer_id}/documents/{doc_id}/generate-pdf")
async def generate_document_pdf_endpoint(
    customer_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """从 form_data 生成 PDF 并更新文档的 file_url（需先上传 PDF）"""
    doc = db.query(CustomerDocument).filter(
        CustomerDocument.id == doc_id,
        CustomerDocument.customer_id == customer_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not doc.file_url:
        raise HTTPException(status_code=400, detail="请先上传 PDF 文件后再生成")

    form_data = _parse_form_data(doc.form_data)
    if not form_data:
        raise HTTPException(status_code=400, detail="请先填写表单后再生成 PDF")

    from modules.houtai.services.document_pdf_service import generate_document_pdf

    base_dir = Path(settings.upload_dir).resolve()
    subfolder = Path("customers") / customer_id / "documents"
    out_dir = base_dir / subfolder
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"doc_{doc_id[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = str(out_dir / filename)

    try:
        generate_document_pdf(
            doc_name=doc.name,
            document_type=doc.document_type,
            form_data=form_data,
            output_path=output_path,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc.file_url = output_path
    doc.file_type = "pdf"
    db.commit()
    db.refresh(doc)

    return CustomerDocumentResponse(
        id=doc.id,
        customer_id=doc.customer_id,
        document_type=doc.document_type,
        name=doc.name,
        file_type=doc.file_type,
        file_url=doc.file_url,
        form_data=form_data,
        status=doc.status,
        signed_at=doc.signed_at,
        signed_file_url=doc.signed_file_url,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/{customer_id}/documents/{doc_id}/preview")
async def preview_customer_document(
    customer_id: str,
    doc_id: str,
    format: str | None = Query(default="pdf", description="预览格式：pdf / origin"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """预览客户文档（用于浏览器/iframe显示）"""
    doc = db.query(CustomerDocument).filter(
        CustomerDocument.id == doc_id,
        CustomerDocument.customer_id == customer_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    path_value = doc.signed_file_url or doc.file_url
    if not path_value:
        raise HTTPException(status_code=404, detail="文档文件未上传")
    p = get_file_path(path_value)
    if not p or not p.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    ext = (doc.file_type or p.suffix.lstrip(".")).lower()
    preview_name = doc.name or p.name

    preview_format = (format or "").lower()
    if preview_format == "origin":
        media_type = "application/pdf" if ext == "pdf" else "application/octet-stream"
        if media_type != "application/pdf":
            guessed, _ = mimetypes.guess_type(str(p))
            media_type = guessed or media_type
        return FileResponse(
            str(p),
            filename=to_ascii_filename(preview_name),
            media_type=media_type,
            headers={
                "Content-Disposition": build_content_disposition(preview_name, "inline"),
                "X-Frame-Options": "ALLOWALL",
            },
        )

    if ext == "pdf":
        return FileResponse(
            str(p),
            filename=to_ascii_filename(preview_name),
            media_type="application/pdf",
            headers={
                "Content-Disposition": build_content_disposition(preview_name, "inline"),
                "X-Frame-Options": "ALLOWALL",
            },
        )

    if ext in ("doc", "docx"):
        uploads_dir = ensure_upload_dir()
        cache_dir = (uploads_dir / "customer_documents_previews").resolve()
        cache_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{doc_id}_{uuid.uuid4().hex}"
        source_copy = cache_dir / f"{stem}.{ext}"
        try:
            shutil.copyfile(str(p), str(source_copy))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"预览失败：复制文件失败: {e}")

        converted = _convert_office_file_to_pdf(source_copy, cache_dir)
        if not converted or not converted.exists():
            raise HTTPException(status_code=500, detail="doc/docx 转 PDF 预览失败（请检查 LibreOffice/soffice 配置）")

        pdf_name = f"{Path(preview_name).stem}.pdf"
        try:
            pdf_bytes = converted.read_bytes()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"预览失败：读取转换后的PDF失败: {e}")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": build_content_disposition(pdf_name, "inline"),
                "X-Frame-Options": "ALLOWALL",
            },
        )

    raise HTTPException(status_code=400, detail="该文件类型不支持预览")


@router.post("/{customer_id}/documents/{doc_id}/upload", response_model=CustomerDocumentResponse)
async def upload_document_file(
    customer_id: str,
    doc_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """上传文档文件"""
    try:
        doc = db.query(CustomerDocument).filter(
            CustomerDocument.id == doc_id,
            CustomerDocument.customer_id == customer_id,
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        content = await file.read()
        ext = (file.filename or "").split(".")[-1] if "." in (file.filename or "") else "pdf"
        filename = f"doc_{doc_id[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{ext}"
        file_url = await save_upload_file(content, filename, subfolder=f"customers/{customer_id}/documents")
        doc.file_url = file_url
        doc.file_type = ext
        db.commit()
        db.refresh(doc)
        
        return CustomerDocumentResponse(
            id=doc.id,
            customer_id=doc.customer_id,
            document_type=doc.document_type,
            name=doc.name,
            file_type=doc.file_type,
            file_url=doc.file_url,
            form_data=_parse_form_data(doc.form_data),
            status=doc.status,
            signed_at=doc.signed_at,
            signed_file_url=doc.signed_file_url,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/{customer_id}/documents/{doc_id}/create-sign-link")
async def create_document_sign_link(
    customer_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """生成文档签字链接，默认 7 天有效"""
    doc = db.query(CustomerDocument).filter(
        CustomerDocument.id == doc_id,
        CustomerDocument.customer_id == customer_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not doc.file_url:
        raise HTTPException(status_code=400, detail="请先上传文档文件")
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)
    req = DocumentSignRequest(
        token=token,
        customer_id=customer_id,
        document_id=doc_id,
        status="pending",
        expires_at=expires_at,
    )
    doc.status = STATUS_PENDING_SIGN
    db.add(req)
    db.commit()
    try:
        admin_users = db.query(User).filter(or_(User.is_active == True, User.is_active.is_(None))).all()
        for u in admin_users:
            touch_business_unread(
                db,
                business_code="customer",
                receiver_user_id=str(u.id),
                data_id=str(customer_id),
                trigger_user_id=str(current_user.id),
            )
        db.commit()
    except Exception:
        db.rollback()
    return {
        "token": token,
        "sign_url": f"/admin/sign/document/{token}",
        "expires_at": expires_at.isoformat(),
    }


@router.post("/{customer_id}/documents/{doc_id}/sync-to-risk")
async def sync_review_to_risk(
    customer_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """将 Review Form 的评审结果同步到 Risk Assessment 文档"""
    review_doc = db.query(CustomerDocument).filter(
        CustomerDocument.id == doc_id,
        CustomerDocument.customer_id == customer_id,
        CustomerDocument.document_type == "review_form",
    ).first()
    if not review_doc:
        raise HTTPException(status_code=404, detail="Review 文档不存在")

    form_data = _parse_form_data(review_doc.form_data)
    goals = form_data.get("goals") if form_data else None
    if not goals:
        return {"message": "无评审目标需同步", "synced": False}

    risk_doc = db.query(CustomerDocument).filter(
        CustomerDocument.customer_id == customer_id,
        CustomerDocument.document_type == "risk_assessment",
    ).first()
    if not risk_doc:
        raise HTTPException(status_code=404, detail="未找到 Risk Assessment 文档")

    risk_fd = _parse_form_data(risk_doc.form_data) or {}
    risk_fd["review_goals"] = goals
    risk_doc.form_data = json.dumps(risk_fd, ensure_ascii=False)
    db.commit()

    return {"message": "已同步到 Risk Assessment", "synced": True}


@router.get("/{customer_id}/documents/{doc_id}/download")
async def download_document_file(
    customer_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """下载文档文件"""
    doc = db.query(CustomerDocument).filter(
        CustomerDocument.id == doc_id,
        CustomerDocument.customer_id == customer_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    path_value = doc.signed_file_url or doc.file_url
    if not path_value:
        raise HTTPException(status_code=404, detail="文档文件未上传")
    file_path = get_file_path(path_value)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )
