from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, or_
from typing import List, Optional
from collections import defaultdict
from core.database import get_db
from decimal import Decimal
from shared.models import (
    Invoice,
    InvoiceItem,
    InvoiceItemCategory,
    InvoiceItemDict,
    InvoiceAuditLog,
    InvoiceServiceLevel1,
    InvoiceServiceLevel2,
    InvoiceServiceLevel3,
    InvoiceServiceCode,
    Customer,
    Task,
    User,
    Employee,
)
from shared.models.customer import customer_service_level1
from ..schemas.invoice import (
    InvoiceResponse,
    InvoiceGenerateRequest,
    InvoiceUpdate,
    InvoiceItemCategoryResponse,
    InvoiceItemDictResponse,
    InvoiceItemDictCreate,
    InvoiceServiceLevel1Response,
    InvoiceServiceLevel2Response,
    InvoiceServiceLevel3Response,
    InvoiceServiceCodeResponse,
    InvoiceServiceLevel1Create,
    InvoiceServiceLevel1Update,
    InvoiceServiceLevel2Create,
    InvoiceServiceLevel2Update,
    InvoiceServiceLevel3Create,
    InvoiceServiceLevel3Update,
    InvoiceServiceCodeCreate,
    InvoiceServiceCodeUpdate,
    BatchSendUnsentInvoicesRequest,
    BatchSendUnsentInvoicesResponse,
    BatchGenerateUninvoicedInvoicesRequest,
    BatchGenerateUninvoicedInvoicesResponse,
    BatchListUninvoicedTasksResponse,
    UninvoicedTaskInfo,
    UninvoicedTaskLine,
    BatchGenerateByTaskResponse,
)
from ..dependencies import get_current_user
from ..services.invoice_service import (
    create_invoice_from_tasks,
    generate_invoice_pdf,
    send_invoice_email,
    normalize_item_code,
    calculate_invoice_line_amounts,
)
from shared.models import TaskStatus, TaskServiceItem, InvoiceServiceCode
from core.utils.file_utils import ensure_upload_dir
from core.auth import decode_access_token
from pathlib import Path
from datetime import datetime, timedelta
import json
import uuid

security_optional = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api/houtai/invoices", tags=["管理-发票"])


def _resolve_invoice_file_path(invoice: Invoice) -> Optional[Path]:
    if not getattr(invoice, "pdf_url", None):
        return None
    file_path = Path(invoice.pdf_url)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path
    elif not file_path.exists():
        upload_dir = ensure_upload_dir()
        file_path = upload_dir / "invoices" / file_path.name
    return file_path


def _normalize_date_end(date_end: Optional[datetime]) -> Optional[datetime]:
    if not date_end:
        return None
    if date_end.hour == 0 and date_end.minute == 0 and date_end.second == 0 and date_end.microsecond == 0:
        return date_end + timedelta(days=1) - timedelta(microseconds=1)
    return date_end


def _ensure_invoice_pdf_file(db: Session, invoice: Invoice, customer: Customer) -> Path:
    existing = _resolve_invoice_file_path(invoice)
    if existing and existing.exists():
        return existing
    upload_dir = ensure_upload_dir()
    pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
    pdf_path = upload_dir / "invoices" / pdf_filename
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    invoice_with_items = (
        db.query(Invoice)
        .options(joinedload(Invoice.items))
        .filter(Invoice.id == invoice.id)
        .first()
    ) or invoice
    generate_invoice_pdf(invoice_with_items, customer, str(pdf_path))
    invoice.pdf_url = str(pdf_path)
    return pdf_path

def _get_task_service_lines(task: Task, db: Session):
    lines = []
    total_amount = Decimal("0")
    total_qty = Decimal("0")

    service_items = (
        db.query(TaskServiceItem)
        .filter(TaskServiceItem.task_id == task.id)
        .order_by(TaskServiceItem.created_at.asc())
        .all()
    )
    if service_items:
        for idx, svc in enumerate(service_items, start=1):
            unit_price = Decimal(str(getattr(svc, "unit_price", None) or "0"))
            quantity = Decimal(str(getattr(svc, "quantity", None) or "0"))
            amount_value = None
            try:
                raw_amount = getattr(svc, "amount", None)
                if raw_amount is not None and str(raw_amount).strip() != "":
                    amount_value = Decimal(str(raw_amount)).quantize(Decimal("0.01"))
            except Exception:
                amount_value = None
            if amount_value is None:
                amount_value = (unit_price * quantity).quantize(Decimal("0.01"))

            code_norm = normalize_item_code(
                getattr(svc, "service_code", None) or task.service_code or "04_104_0125_6_1"
            )
            svc_code = (
                db.query(InvoiceServiceCode)
                .options(joinedload(InvoiceServiceCode.level3))
                .filter(InvoiceServiceCode.is_active == True, InvoiceServiceCode.code == code_norm)
                .first()
            )
            dict_item = None
            if code_norm:
                dict_item = db.query(InvoiceItemDict).filter(InvoiceItemDict.item_code == code_norm).first()
            service_time_start = getattr(svc, "service_time_start", None)
            service_time_end = getattr(svc, "service_time_end", None)
            if not service_time_start or not service_time_end:
                if task.service_start_time and task.service_end_time:
                    service_time_start = task.service_start_time.strftime("%H%M")
                    service_time_end = task.service_end_time.strftime("%H%M")
                elif task.service_time:
                    service_time_start = task.service_time.strftime("%H%M")

            service_name = getattr(getattr(svc_code, "level3", None), "name", None)
            item_name = getattr(svc, "remark", None) or service_name or getattr(dict_item, "item_name", None) or "Service"
            lines.append({
                "line_no": idx,
                "task_service_item_id": getattr(svc, "id", None),
                "description": item_name,
                "code": code_norm,
                "unit": getattr(svc, "unit", None),
                "unit_price": str(unit_price),
                "quantity": str(quantity),
                "amount": str(amount_value),
                "service_date": task.service_time.isoformat() if task.service_time else None,
                "service_time_start": service_time_start,
                "service_time_end": service_time_end,
                "remark": getattr(svc, "remark", None),
            })
            total_amount += amount_value
            total_qty += quantity

        return lines, total_amount, total_qty

    plans = task.service_plans if isinstance(getattr(task, "service_plans", None), list) else None
    if plans:
        for plan in plans:
            unit_price = Decimal(str(plan.get("unit_price") or "0"))
            quantity = Decimal(str(plan.get("quantity") or "0"))
            amount_value = None
            try:
                amount_value = Decimal(str(plan.get("amount") or "")).quantize(Decimal("0.01"))
            except Exception:
                amount_value = None
            if amount_value is None:
                tax_rate = Decimal("0")
                amount_excl_tax, tax_amount, amount_incl_tax = calculate_invoice_line_amounts(unit_price, quantity, tax_rate)
                amount_value = amount_incl_tax

            service_time_start = plan.get("service_time_start")
            service_time_end = plan.get("service_time_end")
            if not service_time_start or not service_time_end:
                if task.service_start_time and task.service_end_time:
                    service_time_start = task.service_start_time.strftime("%H%M")
                    service_time_end = task.service_end_time.strftime("%H%M")
                elif task.service_time:
                    service_time_start = task.service_time.strftime("%H%M")

            code_norm = normalize_item_code(plan.get("service_code") or task.service_code or "04_104_0125_6_1")
            item_name = plan.get("remark") or "Service"
            lines.append({
                "line_no": plan.get("line_no"),
                "description": item_name,
                "code": code_norm,
                "unit": plan.get("unit"),
                "unit_price": str(unit_price),
                "quantity": str(quantity),
                "amount": str(amount_value),
                "service_date": task.service_time.isoformat() if task.service_time else None,
                "service_time_start": service_time_start,
                "service_time_end": service_time_end,
                "remark": plan.get("remark"),
            })
            total_amount += amount_value
            total_qty += quantity
        return lines, total_amount, total_qty

    if task.service_duration_hours:
        try:
            quantity = Decimal(task.service_duration_hours)
        except Exception:
            quantity = Decimal("1")
    else:
        quantity = Decimal("1")
    price = None
    if task.unit_price is not None and Decimal(str(task.unit_price)) > 0:
        price = Decimal(str(task.unit_price))
    raw_code = task.service_code or "04_104_0125_6_1"
    item_code = normalize_item_code(raw_code)
    dict_item = None
    if item_code:
        dict_item = db.query(InvoiceItemDict).filter(InvoiceItemDict.item_code == item_code).first()
    if price is None:
        dict_price = getattr(dict_item, "price_default", None)
        if dict_price is not None and Decimal(str(dict_price)) >= 0:
            price = Decimal(str(dict_price))
        else:
            price = Decimal("60")
    unit_price = price
    tax_rate = Decimal(str(getattr(dict_item, "tax_rate_default", 0) or 0))
    amount_excl_tax, tax_amount, amount_incl_tax = calculate_invoice_line_amounts(unit_price, quantity, tax_rate)
    service_time_start = None
    service_time_end = None
    if task.service_start_time and task.service_end_time:
        service_time_start = task.service_start_time.strftime("%H%M")
        service_time_end = task.service_end_time.strftime("%H%M")
    elif task.service_time:
        service_time_start = task.service_time.strftime("%H%M")
    item_name = getattr(dict_item, "item_name", None) or getattr(task, "title", None) or "Service"
    lines.append({
        "description": item_name,
        "code": item_code,
        "unit_price": str(unit_price),
        "quantity": str(quantity),
        "amount": str(amount_incl_tax),
        "service_date": task.service_time.isoformat() if task.service_time else None,
        "service_time_start": service_time_start,
        "service_time_end": service_time_end,
    })
    total_amount += amount_incl_tax
    total_qty += quantity
    return lines, total_amount, total_qty


@router.get("", response_model=List[InvoiceResponse])
async def get_invoices(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取发票列表"""
    query = db.query(Invoice).options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items)
    )
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    if status:
        query = query.filter(Invoice.status == status)
    invoices = query.order_by(Invoice.invoice_date.desc(), Invoice.created_at.desc()).all()
    return invoices


@router.get("/item-categories", response_model=List[InvoiceItemCategoryResponse])
async def get_invoice_item_categories(
    parent_id: Optional[str] = Query(None, description="父级分类ID，不传则返回一级分类"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(InvoiceItemCategory).filter(InvoiceItemCategory.is_active == True)
    if parent_id:
        query = query.filter(InvoiceItemCategory.parent_id == parent_id)
    else:
        query = query.filter(InvoiceItemCategory.parent_id.is_(None))
    return query.order_by(InvoiceItemCategory.sort_order.asc(), InvoiceItemCategory.name.asc()).all()


@router.get("/item-dict", response_model=List[InvoiceItemDictResponse])
async def get_invoice_item_dict(
    category_id: Optional[str] = Query(None, description="分类ID"),
    keyword: Optional[str] = Query(None, description="按编码/名称模糊搜索"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(InvoiceItemDict).filter(InvoiceItemDict.is_active == True)
    if category_id:
        query = query.filter(InvoiceItemDict.category_id == category_id)
    if keyword:
        like = f"%{keyword.strip()}%"
        query = query.filter((InvoiceItemDict.item_code.like(like)) | (InvoiceItemDict.item_name.like(like)))
    return query.order_by(InvoiceItemDict.item_code.asc()).all()


@router.get("/service-level1", response_model=List[InvoiceServiceLevel1Response])
async def get_invoice_service_level1(
    include_inactive: bool = Query(False, description="是否包含停用"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(InvoiceServiceLevel1)
    if not include_inactive:
        query = query.filter(InvoiceServiceLevel1.is_active == True)
    return query.order_by(InvoiceServiceLevel1.sort_order.asc(), InvoiceServiceLevel1.name.asc()).all()


@router.get("/service-level2", response_model=List[InvoiceServiceLevel2Response])
async def get_invoice_service_level2(
    level1_id: str = Query(..., description="一级大类ID"),
    include_inactive: bool = Query(False, description="是否包含停用"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.level1_id == level1_id)
    if not include_inactive:
        query = query.filter(InvoiceServiceLevel2.is_active == True)
    return query.order_by(InvoiceServiceLevel2.sort_order.asc(), InvoiceServiceLevel2.name.asc()).all()


@router.get("/service-level3", response_model=List[InvoiceServiceLevel3Response])
async def get_invoice_service_level3(
    level1_id: str = Query(..., description="一级大类ID"),
    level2_id: Optional[str] = Query(None, description="二级大类ID（可为空）"),
    include_inactive: bool = Query(False, description="是否包含停用"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.level1_id == level1_id)
    if not include_inactive:
        query = query.filter(InvoiceServiceLevel3.is_active == True)
    if level2_id:
        query = query.filter(InvoiceServiceLevel3.level2_id == level2_id)
    else:
        query = query.filter(InvoiceServiceLevel3.level2_id.is_(None))
    return query.order_by(InvoiceServiceLevel3.sort_order.asc(), InvoiceServiceLevel3.name.asc()).all()


@router.get("/service-codes", response_model=List[InvoiceServiceCodeResponse])
async def get_invoice_service_codes(
    level3_id: str = Query(..., description="三级服务项目ID"),
    include_inactive: bool = Query(False, description="是否包含停用"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.level3_id == level3_id)
    if not include_inactive:
        query = query.filter(InvoiceServiceCode.is_active == True)
    return query.order_by(InvoiceServiceCode.code.asc()).all()


@router.get("/service-code-price", response_model=InvoiceServiceCodeResponse)
async def get_invoice_service_code_price(
    code: str = Query(..., description="服务编码"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceCode).filter(
        InvoiceServiceCode.is_active == True,
        InvoiceServiceCode.code == code,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="服务编码不存在")
    return row


@router.post("/service-level1", response_model=InvoiceServiceLevel1Response, status_code=status.HTTP_201_CREATED)
async def create_invoice_service_level1(
    body: InvoiceServiceLevel1Create,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="一级服务名称不能为空")

    existing = db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.name == name).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            if body.sort_order is not None:
                existing.sort_order = body.sort_order
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=409, detail="一级服务名称已存在")

    row = InvoiceServiceLevel1(name=name, sort_order=body.sort_order or 0, is_active=bool(body.is_active))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/service-level1/{level1_id}", response_model=InvoiceServiceLevel1Response)
async def update_invoice_service_level1(
    level1_id: str,
    body: InvoiceServiceLevel1Update,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.id == level1_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="一级服务不存在")

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="一级服务名称不能为空")
        if name != row.name:
            conflict = db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.name == name).first()
            if conflict:
                raise HTTPException(status_code=409, detail="一级服务名称已存在")
            row.name = name

    if body.sort_order is not None:
        row.sort_order = body.sort_order
    if body.is_active is not None:
        row.is_active = body.is_active

    db.commit()
    db.refresh(row)
    return row


@router.delete("/service-level1/{level1_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice_service_level1(
    level1_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.id == level1_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="一级服务不存在")
    level3_ids = [r[0] for r in db.query(InvoiceServiceLevel3.id).filter(InvoiceServiceLevel3.level1_id == level1_id).all()]
    if level3_ids:
        db.query(InvoiceServiceCode).filter(InvoiceServiceCode.level3_id.in_(level3_ids)).delete(synchronize_session=False)
    db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.level1_id == level1_id).delete(synchronize_session=False)
    db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.level1_id == level1_id).delete(synchronize_session=False)
    db.execute(customer_service_level1.delete().where(customer_service_level1.c.level1_id == level1_id))
    db.delete(row)
    db.commit()
    return None


@router.post("/service-level2", response_model=InvoiceServiceLevel2Response, status_code=status.HTTP_201_CREATED)
async def create_invoice_service_level2(
    body: InvoiceServiceLevel2Create,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    level1 = db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.id == body.level1_id).first()
    if not level1 or not level1.is_active:
        raise HTTPException(status_code=404, detail="一级服务不存在或未启用")

    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="二级服务名称不能为空")

    existing = (
        db.query(InvoiceServiceLevel2)
        .filter(InvoiceServiceLevel2.level1_id == body.level1_id, InvoiceServiceLevel2.name == name)
        .first()
    )
    if existing:
        if not existing.is_active:
            existing.is_active = True
            if body.sort_order is not None:
                existing.sort_order = body.sort_order
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=409, detail="二级服务名称已存在")

    row = InvoiceServiceLevel2(level1_id=body.level1_id, name=name, sort_order=body.sort_order or 0, is_active=bool(body.is_active))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/service-level2/{level2_id}", response_model=InvoiceServiceLevel2Response)
async def update_invoice_service_level2(
    level2_id: str,
    body: InvoiceServiceLevel2Update,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.id == level2_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="二级服务不存在")

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="二级服务名称不能为空")
        if name != row.name:
            conflict = (
                db.query(InvoiceServiceLevel2)
                .filter(InvoiceServiceLevel2.level1_id == row.level1_id, InvoiceServiceLevel2.name == name)
                .first()
            )
            if conflict:
                raise HTTPException(status_code=409, detail="二级服务名称已存在")
            row.name = name

    if body.sort_order is not None:
        row.sort_order = body.sort_order
    if body.is_active is not None:
        row.is_active = body.is_active

    db.commit()
    db.refresh(row)
    return row


@router.delete("/service-level2/{level2_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice_service_level2(
    level2_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.id == level2_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="二级服务不存在")
    level3_ids = [r[0] for r in db.query(InvoiceServiceLevel3.id).filter(InvoiceServiceLevel3.level2_id == level2_id).all()]
    if level3_ids:
        db.query(InvoiceServiceCode).filter(InvoiceServiceCode.level3_id.in_(level3_ids)).delete(synchronize_session=False)
    db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.level2_id == level2_id).delete(synchronize_session=False)
    db.delete(row)
    db.commit()
    return None


@router.post("/service-level3", response_model=InvoiceServiceLevel3Response, status_code=status.HTTP_201_CREATED)
async def create_invoice_service_level3(
    body: InvoiceServiceLevel3Create,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    level1 = db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.id == body.level1_id).first()
    if not level1 or not level1.is_active:
        raise HTTPException(status_code=404, detail="一级服务不存在或未启用")

    if body.level2_id:
        level2 = db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.id == body.level2_id).first()
        if not level2 or not level2.is_active:
            raise HTTPException(status_code=404, detail="二级服务不存在或未启用")
        if level2.level1_id != body.level1_id:
            raise HTTPException(status_code=400, detail="二级服务不属于该一级服务")

    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="三级服务名称不能为空")

    dup_query = db.query(InvoiceServiceLevel3).filter(
        InvoiceServiceLevel3.level1_id == body.level1_id,
        InvoiceServiceLevel3.name == name,
    )
    if body.level2_id:
        dup_query = dup_query.filter(InvoiceServiceLevel3.level2_id == body.level2_id)
    else:
        dup_query = dup_query.filter(InvoiceServiceLevel3.level2_id.is_(None))
    existing = dup_query.first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            if body.sort_order is not None:
                existing.sort_order = body.sort_order
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=409, detail="三级服务名称已存在")

    row = InvoiceServiceLevel3(
        level1_id=body.level1_id,
        level2_id=body.level2_id,
        name=name,
        sort_order=body.sort_order or 0,
        is_active=bool(body.is_active),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/service-level3/{level3_id}", response_model=InvoiceServiceLevel3Response)
async def update_invoice_service_level3(
    level3_id: str,
    body: InvoiceServiceLevel3Update,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.id == level3_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="三级服务不存在")

    target_level2_id = row.level2_id
    if "level2_id" in getattr(body, "__fields_set__", set()):
        if body.level2_id:
            level2 = db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.id == body.level2_id).first()
            if not level2 or not level2.is_active:
                raise HTTPException(status_code=404, detail="二级服务不存在或未启用")
            if level2.level1_id != row.level1_id:
                raise HTTPException(status_code=400, detail="二级服务不属于该一级服务")
            target_level2_id = body.level2_id
        else:
            target_level2_id = None

    target_name = row.name
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="三级服务名称不能为空")
        target_name = name

    if target_name != row.name or target_level2_id != row.level2_id:
        dup_query = db.query(InvoiceServiceLevel3).filter(
            InvoiceServiceLevel3.level1_id == row.level1_id,
            InvoiceServiceLevel3.name == target_name,
            InvoiceServiceLevel3.id != row.id,
        )
        if target_level2_id:
            dup_query = dup_query.filter(InvoiceServiceLevel3.level2_id == target_level2_id)
        else:
            dup_query = dup_query.filter(InvoiceServiceLevel3.level2_id.is_(None))
        if dup_query.first():
            raise HTTPException(status_code=409, detail="三级服务名称已存在")

    if "level2_id" in getattr(body, "__fields_set__", set()):
        row.level2_id = target_level2_id
    if body.name is not None:
        row.name = target_name
    if body.sort_order is not None:
        row.sort_order = body.sort_order
    if body.is_active is not None:
        row.is_active = body.is_active

    db.commit()
    db.refresh(row)
    return row


@router.delete("/service-level3/{level3_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice_service_level3(
    level3_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.id == level3_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="三级服务不存在")
    db.query(InvoiceServiceCode).filter(InvoiceServiceCode.level3_id == level3_id).delete(synchronize_session=False)
    db.delete(row)
    db.commit()
    return None


@router.post("/service-codes", response_model=InvoiceServiceCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_service_code(
    body: InvoiceServiceCodeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    level3 = db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.id == body.level3_id).first()
    if not level3 or not level3.is_active:
        raise HTTPException(status_code=404, detail="三级服务不存在或未启用")

    code = normalize_item_code(body.code)
    if not code or code.endswith("..."):
        raise HTTPException(status_code=400, detail="服务编码不完整")
    if body.price is None:
        raise HTTPException(status_code=400, detail="单价不能为空")

    existing = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.code == code).first()
    if existing:
        existing.is_active = True
        existing.level3_id = body.level3_id
        existing.price = body.price
        existing.unit = (body.unit.strip() if body.unit else None)
        db.commit()
        db.refresh(existing)
        return existing

    row = InvoiceServiceCode(
        level3_id=body.level3_id,
        code=code,
        price=body.price,
        unit=(body.unit.strip() if body.unit else None),
        is_active=bool(body.is_active),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/service-codes/{code_id}", response_model=InvoiceServiceCodeResponse)
async def update_invoice_service_code(
    code_id: str,
    body: InvoiceServiceCodeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.id == code_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="服务编码不存在")

    if "level3_id" in getattr(body, "__fields_set__", set()) and body.level3_id is not None:
        level3 = db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.id == body.level3_id).first()
        if not level3 or not level3.is_active:
            raise HTTPException(status_code=404, detail="三级服务不存在或未启用")
        row.level3_id = body.level3_id

    if body.code is not None:
        code = normalize_item_code(body.code)
        if not code or code.endswith("..."):
            raise HTTPException(status_code=400, detail="服务编码不完整")
        if code != row.code:
            conflict = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.code == code).first()
            if conflict:
                raise HTTPException(status_code=409, detail="服务编码已存在")
            row.code = code

    if body.price is not None:
        row.price = body.price
    if body.unit is not None:
        row.unit = body.unit.strip() if body.unit else None
    if body.is_active is not None:
        row.is_active = body.is_active

    db.commit()
    db.refresh(row)
    return row


@router.delete("/service-codes/{code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice_service_code(
    code_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.id == code_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="服务编码不存在")
    db.delete(row)
    db.commit()
    return None


@router.post("/item-dict", response_model=InvoiceItemDictResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_item_dict(
    body: InvoiceItemDictCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item_code = normalize_item_code(body.item_code, body.reference_code)
    if not item_code or item_code.endswith("..."):
        raise HTTPException(status_code=400, detail="项目编码不完整，无法解析省略号")

    category = db.query(InvoiceItemCategory).filter(InvoiceItemCategory.id == body.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    existing = db.query(InvoiceItemDict).filter(InvoiceItemDict.item_code == item_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="项目编码已存在")

    tax_rate = body.tax_rate_default if body.tax_rate_default is not None else Decimal("0")
    if tax_rate < 0 or tax_rate > 1:
        raise HTTPException(status_code=400, detail="税率必须在 0~1 之间")

    item = InvoiceItemDict(
        id=str(uuid.uuid4()),
        category_id=body.category_id,
        item_code=item_code,
        item_name=body.item_name,
        spec_default=body.spec_default,
        unit_default=body.unit_default,
        price_default=body.price_default,
        tax_rate_default=tax_rate,
        is_active=True,
        created_by=getattr(current_user, "id", None),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/tasks")
async def get_tasks_for_invoice(
    customer_id: Optional[str] = Query(None, description="客户ID"),
    employee_id: Optional[str] = Query(None, description="员工ID"),
    date_start: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    date_end: Optional[str] = Query(None, description="结束日期 (ISO格式)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取符合条件的审核通过任务列表（用于生成发票）"""
    import logging
    logger = logging.getLogger(__name__)
    
    # 查询符合条件的任务
    query = db.query(Task).options(
        joinedload(Task.customer),
        joinedload(Task.assigned_employee),
        joinedload(Task.service_items),
    ).filter(Task.status == TaskStatus.approved)
    invoiced_exists = db.query(InvoiceItem.id).filter(
        or_(
            InvoiceItem.task_id == Task.id,
            InvoiceItem.source_task_id == Task.id,
        )
    ).exists()
    query = query.filter(~invoiced_exists)
    
    # 根据筛选条件过滤
    if customer_id:
        query = query.filter(Task.customer_id == customer_id)
        logger.info(f"添加客户筛选: customer_id = '{customer_id}'")
    if employee_id:
        query = query.filter(Task.assigned_employee_id == employee_id)
        logger.info(f"添加员工筛选: assigned_employee_id = '{employee_id}'")
    
    # 先查询筛选前的任务（不包含日期筛选）
    tasks_before_date_filter = query.all()
    logger.info(f"筛选前（客户+员工）找到 {len(tasks_before_date_filter)} 个任务")
    
    # 处理日期范围 - 只使用 service_end_time 来判断
    # 使用Python层面过滤，因为SQLite的func.date()可能不工作
    date_start_dt = None
    date_end_dt = None
    if date_start and date_end:
        try:
            # 解析开始日期
            if isinstance(date_start, str):
                date_part = date_start.split('T')[0] if 'T' in date_start else date_start[:10]
                date_start_dt = datetime.strptime(date_part, '%Y-%m-%d').date()
            elif isinstance(date_start, datetime):
                date_start_dt = date_start.date()
            else:
                date_start_dt = date_start
            
            # 解析结束日期
            if isinstance(date_end, str):
                date_part = date_end.split('T')[0] if 'T' in date_end else date_end[:10]
                date_end_dt = datetime.strptime(date_part, '%Y-%m-%d').date()
            elif isinstance(date_end, datetime):
                date_end_dt = date_end.date()
            else:
                date_end_dt = date_end
            
            logger.info(f"解析后的日期范围: {date_start_dt} 至 {date_end_dt}")
        except (ValueError, AttributeError, TypeError) as e:
            logger.warning(f"无法解析日期范围 {date_start} 至 {date_end}: {e}")
    
    # 使用Python层面过滤日期范围（因为SQLite的func.date()可能不工作）
    tasks_after_filter = []
    if date_start_dt and date_end_dt:
        for task in tasks_before_date_filter:
            service_dt = task.service_end_time or task.service_time or task.service_start_time
            if service_dt:
                task_date = service_dt.date()
                if date_start_dt <= task_date <= date_end_dt:
                    tasks_after_filter.append(task)
    else:
        # 如果没有日期范围，使用所有筛选前的任务
        tasks_after_filter = tasks_before_date_filter
    
    tasks_after_filter.sort(
        key=lambda task: task.service_end_time or task.service_start_time or task.service_time or task.created_at or datetime.min,
        reverse=True
    )

    task_count = len(tasks_after_filter)
    logger.info(f"筛选后找到 {task_count} 个任务（使用Python层面日期过滤）")
    
    # 返回任务列表，包含任务ID和基本信息
    tasks_after_filter.sort(
        key=lambda task: task.service_end_time or task.service_start_time or task.service_time or task.created_at or datetime.min,
        reverse=True
    )

    result = []
    for task in tasks_after_filter:
        customer_name = getattr(task.customer, "name", None)
        if not customer_name and task.customer_id:
            customer_name = db.query(Customer.name).filter(Customer.id == task.customer_id).scalar()
        employee_name = getattr(task.assigned_employee, "name", None)
        if not employee_name and task.assigned_employee_id:
            employee_name = db.query(Employee.name).filter(Employee.id == task.assigned_employee_id).scalar()

        service_lines, subtotal, _ = _get_task_service_lines(task, db)
        service_count = len(service_lines) if service_lines else 0

        result.append({
            "id": task.id,
            "title": task.title or f"任务 {task.id[:8]}",
            "customer": {
                "id": task.customer_id,
                "name": customer_name
            },
            "customer_name": customer_name,
            "employee": {
                "id": task.assigned_employee_id,
                "name": employee_name
            },
            "employee_name": employee_name,
            "service_time": task.service_time.isoformat() if task.service_time else None,
            "service_start_time": task.service_start_time.isoformat() if task.service_start_time else None,
            "service_end_time": task.service_end_time.isoformat() if task.service_end_time else None,
            "service_code": (service_lines[0].get("code") if service_lines else (task.service_code or "04_104_0125_6_1")),
            "service_count": service_count,
            "total_amount": str(subtotal)
        })
    
    return result

@router.get("/tasks/detail")
async def get_tasks_for_invoice_detail(
    customer_id: Optional[str] = Query(None, description="客户ID"),
    employee_id: Optional[str] = Query(None, description="员工ID"),
    date_start: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    date_end: Optional[str] = Query(None, description="结束日期 (ISO格式)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Task).options(
        joinedload(Task.customer),
        joinedload(Task.assigned_employee),
        joinedload(Task.service_items),
    ).filter(Task.status == TaskStatus.approved)
    invoiced_exists = db.query(InvoiceItem.id).filter(
        or_(
            InvoiceItem.task_id == Task.id,
            InvoiceItem.source_task_id == Task.id,
        )
    ).exists()
    query = query.filter(~invoiced_exists)
    if customer_id:
        query = query.filter(Task.customer_id == customer_id)
    if employee_id:
        query = query.filter(Task.assigned_employee_id == employee_id)
    tasks_before_date_filter = query.all()
    date_start_dt = None
    date_end_dt = None
    if date_start and date_end:
        try:
            date_part = date_start.split('T')[0] if 'T' in date_start else date_start[:10]
            date_start_dt = datetime.strptime(date_part, '%Y-%m-%d').date()
            date_part = date_end.split('T')[0] if 'T' in date_end else date_end[:10]
            date_end_dt = datetime.strptime(date_part, '%Y-%m-%d').date()
        except Exception:
            date_start_dt = None
            date_end_dt = None
    tasks_after_filter = []
    if date_start_dt and date_end_dt:
        for task in tasks_before_date_filter:
            service_dt = task.service_end_time or task.service_time or task.service_start_time
            if service_dt:
                task_date = service_dt.date()
                if date_start_dt <= task_date <= date_end_dt:
                    tasks_after_filter.append(task)
    else:
        tasks_after_filter = tasks_before_date_filter
    result = []
    for task in tasks_after_filter:
        lines, total_amount, _ = _get_task_service_lines(task, db)
        result.append({
            "id": task.id,
            "title": task.title or f"任务 {task.id[:8]}",
            "customer": {
                "id": task.customer_id,
                "name": getattr(task.customer, "name", None)
            },
            "customer_name": getattr(task.customer, "name", None),
            "employee": {
                "id": task.assigned_employee_id,
                "name": getattr(task.assigned_employee, "name", None)
            },
            "employee_name": getattr(task.assigned_employee, "name", None),
            "service_end_time": task.service_end_time.isoformat() if task.service_end_time else None,
            "service_lines": lines,
            "subtotal": str(total_amount)
        })
    return result

@router.get("/tasks/{task_id}")
@router.get("/tasks/{task_id}/")
async def get_task_invoice_detail(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = db.query(Task).options(
        joinedload(Task.customer),
        joinedload(Task.assigned_employee),
        joinedload(Task.service_items),
    ).filter(Task.id == task_id, Task.status == TaskStatus.approved).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或未审核通过")
    invoiced_exists = db.query(InvoiceItem.id).filter(
        or_(
            InvoiceItem.task_id == task.id,
            InvoiceItem.source_task_id == task.id,
        )
    ).first()
    if invoiced_exists:
        raise HTTPException(status_code=400, detail="该任务已开发票")
    lines, total_amount, _ = _get_task_service_lines(task, db)
    return {
        "task": {
            "id": task.id,
            "title": task.title or f"任务 {task.id[:8]}",
            "customer": {
                "id": task.customer_id,
                "name": getattr(task.customer, "name", None)
            },
            "customer_name": getattr(task.customer, "name", None),
            "employee": {
                "id": task.assigned_employee_id,
                "name": getattr(task.assigned_employee, "name", None)
            },
            "employee_name": getattr(task.assigned_employee, "name", None),
            "service_end_time": task.service_end_time.isoformat() if task.service_end_time else None
        },
        "service_lines": lines,
        "total_amount": str(total_amount)
    }

@router.post("/tasks/{task_id}/generate", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
@router.post("/tasks/{task_id}/generate/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def generate_invoice_from_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    payload: dict = Body(default={})
):
    task = db.query(Task).filter(Task.id == task_id, Task.status == TaskStatus.approved).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或未审核通过")
    exists_row = db.query(InvoiceItem.id).filter(
        or_(
            InvoiceItem.task_id == task.id,
            InvoiceItem.source_task_id == task.id,
        )
    ).first()
    if exists_row:
        raise HTTPException(status_code=400, detail="该任务已开发票")
    is_paid = bool(payload.get("is_paid")) if isinstance(payload, dict) else False
    invoice = create_invoice_from_tasks(
        db=db,
        customer_id=task.customer_id,
        task_ids=[task.id],
        invoice_date=datetime.utcnow(),
        is_paid=is_paid,
    )
    customer = db.query(Customer).filter(Customer.id == task.customer_id).first()
    upload_dir = ensure_upload_dir()
    pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
    pdf_path = upload_dir / "invoices" / pdf_filename
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    generate_invoice_pdf(invoice, customer, str(pdf_path))
    invoice.pdf_url = str(pdf_path)
    db.commit()
    invoice_with_relations = db.query(Invoice).options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items)
    ).filter(Invoice.id == invoice.id).first()
    return invoice_with_relations

@router.post("/generate", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def generate_invoice(
    request: InvoiceGenerateRequest,
    db: Session = Depends(get_db),
):
    """生成发票（从审核通过的任务，支持筛选条件）"""
    try:
        invoice = create_invoice_from_tasks(
            db=db,
            customer_id=request.customer_id,
            task_ids=request.task_ids,
            employee_id=request.employee_id,
            date_start=request.date_start,
            date_end=request.date_end,
            task_overrides=request.task_overrides,
            invoice_date=request.invoice_date or datetime.utcnow(),
            is_paid=bool(getattr(request, "is_paid", False)),
        )
        
        # 生成PDF（主要格式）
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        upload_dir = ensure_upload_dir()
        pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
        pdf_path = upload_dir / "invoices" / pdf_filename
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        generate_invoice_pdf(invoice, customer, str(pdf_path))
        
        # 更新发票文件URL（使用绝对路径）
        invoice.pdf_url = str(pdf_path)
        db.commit()
        
        # 重新加载发票及其关系
        db.refresh(invoice)
        # 使用joinedload重新查询以加载关系
        invoice_with_relations = db.query(Invoice).options(
            joinedload(Invoice.customer),
            joinedload(Invoice.items)
        ).filter(Invoice.id == invoice.id).first()
        
        return invoice_with_relations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/generate-uninvoiced", response_model=BatchGenerateUninvoicedInvoicesResponse, status_code=status.HTTP_201_CREATED)
async def batch_generate_uninvoiced_invoices(
    request: BatchGenerateUninvoicedInvoicesRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Task.id, Task.customer_id).filter(Task.status == TaskStatus.approved)
    invoiced_exists = db.query(InvoiceItem.id).filter(
        or_(
            InvoiceItem.task_id == Task.id,
            InvoiceItem.source_task_id == Task.id,
        )
    ).exists()
    query = query.filter(~invoiced_exists)

    if request.customer_id:
        query = query.filter(Task.customer_id == request.customer_id)
    if request.employee_id:
        query = query.filter(Task.assigned_employee_id == request.employee_id)
    if request.date_start:
        query = query.filter(Task.service_time >= request.date_start)
    date_end = _normalize_date_end(request.date_end)
    if date_end:
        query = query.filter(Task.service_time <= date_end)

    rows = query.all()
    if not rows:
        return {
            "customers": 0,
            "created": 0,
            "skipped": 0,
            "failed": 0,
            "results": [],
        }

    task_ids_by_customer_id = defaultdict(list)
    for task_id, customer_id in rows:
        if task_id and customer_id:
            task_ids_by_customer_id[customer_id].append(task_id)

    results = []
    created = 0
    skipped = 0
    failed = 0

    for customer_id, task_ids in task_ids_by_customer_id.items():
        if not task_ids:
            skipped += 1
            results.append(
                {
                    "customer_id": customer_id,
                    "task_count": 0,
                    "status": "skipped",
                    "reason": "没有可开发票的任务",
                }
            )
            continue

        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError("客户不存在")

            invoice = create_invoice_from_tasks(
                db=db,
                customer_id=customer_id,
                task_ids=task_ids,
                invoice_date=request.invoice_date or datetime.utcnow(),
                commit=False,
            )

            pdf_path = _ensure_invoice_pdf_file(db, invoice, customer)
            if not pdf_path.exists():
                raise ValueError("发票文件生成失败")

            db.commit()
            created += 1
            results.append(
                {
                    "customer_id": customer_id,
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "task_count": len(task_ids),
                    "total_amount": invoice.total_amount,
                    "status": "created",
                }
            )
        except Exception as e:
            db.rollback()
            failed += 1
            results.append(
                {
                    "customer_id": customer_id,
                    "task_count": len(task_ids),
                    "status": "failed",
                    "reason": str(e),
                }
            )

    return {
        "customers": len(task_ids_by_customer_id),
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


@router.get("/batch/tasks-uninvoiced-detail", response_model=BatchListUninvoicedTasksResponse)
@router.get("/batch/tasks-uninvoiced-detail/", response_model=BatchListUninvoicedTasksResponse)
async def list_uninvoiced_tasks_detail(
    customer_id: Optional[str] = Query(None, description="客户ID"),
    employee_id: Optional[str] = Query(None, description="员工ID"),
    date_start: Optional[datetime] = Query(None, description="开始日期 (ISO格式)"),
    date_end: Optional[datetime] = Query(None, description="结束日期 (ISO格式)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Task).options(
        joinedload(Task.customer),
        joinedload(Task.assigned_employee),
        joinedload(Task.service_items),
    ).filter(Task.status == TaskStatus.approved)
    invoiced_exists = db.query(InvoiceItem.id).filter(
        or_(
            InvoiceItem.task_id == Task.id,
            InvoiceItem.source_task_id == Task.id,
        )
    ).exists()
    query = query.filter(~invoiced_exists)
    if customer_id:
        query = query.filter(Task.customer_id == customer_id)
    if employee_id:
        query = query.filter(Task.assigned_employee_id == employee_id)
    if date_start:
        query = query.filter(Task.service_time >= date_start)
    date_end = _normalize_date_end(date_end)
    if date_end:
        query = query.filter(Task.service_time <= date_end)
    tasks = query.all()
    result = []
    for task in tasks:
        lines, total_amount, _ = _get_task_service_lines(task, db)
        result.append(
            {
                "id": task.id,
                "title": task.title or f"任务 {task.id[:8]}",
                "customer_id": task.customer_id,
                "customer_name": getattr(task.customer, "name", None),
                "employee_id": task.assigned_employee_id,
                "employee_name": getattr(task.assigned_employee, "name", None),
                "service_start_time": task.service_start_time.isoformat() if task.service_start_time else None,
                "service_end_time": task.service_end_time.isoformat() if task.service_end_time else None,
                "service_lines": [
                    {
                        "description": line.get("description"),
                        "code": line.get("code"),
                        "unit": line.get("unit"),
                        "unit_price": line.get("unit_price"),
                        "quantity": line.get("quantity"),
                        "amount": line.get("amount"),
                        "service_date": line.get("service_date"),
                        "service_time_start": line.get("service_time_start"),
                        "service_time_end": line.get("service_time_end"),
                    }
                    for line in lines
                ],
                "subtotal": str(total_amount),
            }
        )
    return {
        "count": len(result),
        "tasks": result,
    }


@router.get("/tasks-uninvoiced-detail", response_model=BatchListUninvoicedTasksResponse)
@router.get("/tasks-uninvoiced-detail/", response_model=BatchListUninvoicedTasksResponse)
async def list_uninvoiced_tasks_detail_alias(
    customer_id: Optional[str] = Query(None, description="客户ID"),
    employee_id: Optional[str] = Query(None, description="员工ID"),
    date_start: Optional[datetime] = Query(None, description="开始日期 (ISO格式)"),
    date_end: Optional[datetime] = Query(None, description="结束日期 (ISO格式)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await list_uninvoiced_tasks_detail(
        customer_id=customer_id,
        employee_id=employee_id,
        date_start=date_start,
        date_end=date_end,
        db=db,
        current_user=current_user,
    )


@router.post("/batch/generate-by-task", response_model=BatchGenerateByTaskResponse, status_code=status.HTTP_200_OK)
@router.post("/batch/generate-by-task/", response_model=BatchGenerateByTaskResponse, status_code=status.HTTP_200_OK)
async def batch_generate_invoices_by_task(
    request: BatchGenerateUninvoicedInvoicesRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Task).filter(Task.status == TaskStatus.approved)
    invoiced_exists = db.query(InvoiceItem.id).filter(
        or_(
            InvoiceItem.task_id == Task.id,
            InvoiceItem.source_task_id == Task.id,
        )
    ).exists()
    query = query.filter(~invoiced_exists)
    if request.customer_id:
        query = query.filter(Task.customer_id == request.customer_id)
    if request.employee_id:
        query = query.filter(Task.assigned_employee_id == request.employee_id)
    if request.date_start:
        query = query.filter(Task.service_time >= request.date_start)
    date_end = _normalize_date_end(request.date_end)
    if date_end:
        query = query.filter(Task.service_time <= date_end)
    tasks = query.all()

    results = []
    created = 0
    skipped = 0
    failed = 0

    for task in tasks:
        try:
            exists_row = db.query(InvoiceItem.id).filter(
                or_(
                    InvoiceItem.task_id == task.id,
                    InvoiceItem.source_task_id == task.id,
                )
            ).first()
            if exists_row:
                skipped += 1
                results.append(
                    {
                        "task_id": task.id,
                        "customer_id": task.customer_id,
                        "status": "skipped",
                        "reason": "该任务已开发票",
                    }
                )
                continue

            invoice = create_invoice_from_tasks(
                db=db,
                customer_id=task.customer_id,
                task_ids=[task.id],
                invoice_date=request.invoice_date or datetime.utcnow(),
                commit=False,
            )
            customer = db.query(Customer).filter(Customer.id == task.customer_id).first()
            pdf_path = _ensure_invoice_pdf_file(db, invoice, customer)
            if not pdf_path.exists():
                raise ValueError("发票文件生成失败")
            db.commit()
            created += 1
            results.append(
                {
                    "task_id": task.id,
                    "customer_id": task.customer_id,
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "total_amount": invoice.total_amount,
                    "status": "created",
                }
            )
        except Exception as e:
            db.rollback()
            failed += 1
            results.append(
                {
                    "task_id": task.id,
                    "customer_id": task.customer_id,
                    "status": "failed",
                    "reason": str(e),
                }
            )

    return {
        "total_tasks": len(tasks),
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


@router.post("/tasks/generate-all", response_model=BatchGenerateByTaskResponse, status_code=status.HTTP_200_OK)
@router.post("/tasks/generate-all/", response_model=BatchGenerateByTaskResponse, status_code=status.HTTP_200_OK)
@router.post("/generate-all", response_model=BatchGenerateByTaskResponse, status_code=status.HTTP_200_OK)
@router.post("/generate-all/", response_model=BatchGenerateByTaskResponse, status_code=status.HTTP_200_OK)
async def batch_generate_invoices_by_task_alias(
    request: BatchGenerateUninvoicedInvoicesRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await batch_generate_invoices_by_task(request=request, db=db, current_user=current_user)

@router.post("/preview")
async def preview_invoice_data(
    request: InvoiceGenerateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    query = db.query(Task).filter(
        Task.customer_id == request.customer_id,
        Task.status == TaskStatus.approved
    )
    invoiced_exists = db.query(InvoiceItem.id).filter(
        or_(
            InvoiceItem.task_id == Task.id,
            InvoiceItem.source_task_id == Task.id,
        )
    ).exists()
    query = query.filter(~invoiced_exists)
    if request.task_ids:
        query = query.filter(Task.id.in_(request.task_ids))
    else:
        if request.employee_id:
            query = query.filter(Task.assigned_employee_id == request.employee_id)
        if request.date_start:
            query = query.filter(Task.service_time >= request.date_start)
        date_end = _normalize_date_end(request.date_end)
        if date_end:
            query = query.filter(Task.service_time <= date_end)
    tasks = query.options(joinedload(Task.service_items)).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="没有找到符合条件的审核通过的任务")
    total_amount = Decimal("0")
    total_qty = Decimal("0")
    items = []
    for task in tasks:
        lines, subtotal, qty_total = _get_task_service_lines(task, db)
        for line in lines:
            items.append({
                "task_id": task.id,
                "description": line.get("description"),
                "code": line.get("code"),
                "unit_price": line.get("unit_price"),
                "quantity": line.get("quantity"),
                "amount": line.get("amount"),
                "service_date": line.get("service_date"),
                "service_time_start": line.get("service_time_start"),
                "service_time_end": line.get("service_time_end"),
            })
        total_amount += subtotal
        total_qty += qty_total
    return {
        "customer": {"id": customer.id, "name": customer.name},
        "task_count": len(tasks),
        "items": items,
        "total_amount": str(total_amount),
        "total_qty": str(total_qty)
    }

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取发票详情"""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items)
    ).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    request: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新发票信息"""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items)
    ).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    before_snapshot = None
    try:
        before_snapshot = json.dumps(
            {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "customer_id": invoice.customer_id,
                "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "status": invoice.status,
                "total_amount": str(invoice.total_amount) if invoice.total_amount is not None else None,
                "total_excl_tax": str(invoice.total_excl_tax) if getattr(invoice, "total_excl_tax", None) is not None else None,
                "total_tax": str(invoice.total_tax) if getattr(invoice, "total_tax", None) is not None else None,
                "total_incl_tax": str(invoice.total_incl_tax) if getattr(invoice, "total_incl_tax", None) is not None else None,
                "items": [
                    {
                        "id": it.id,
                        "line_no": it.line_no,
                        "item_code": it.item_code or it.service_code,
                        "item_name": it.item_name or it.description,
                        "unit_price": str(it.unit_price or it.price) if (it.unit_price or it.price) is not None else None,
                        "quantity": str(it.quantity) if it.quantity is not None else None,
                        "amount_incl_tax": str(it.amount_incl_tax or it.amount) if (it.amount_incl_tax or it.amount) is not None else None,
                    }
                    for it in (invoice.items or [])
                ],
            },
            ensure_ascii=False,
        )
    except Exception:
        before_snapshot = None

    if request.customer_id and request.customer_id != invoice.customer_id:
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")
        invoice.customer_id = request.customer_id

    if request.invoice_date:
        invoice.invoice_date = request.invoice_date

    if request.items is not None:
        for item in list(invoice.items):
            db.delete(item)

        total_excl_tax = Decimal("0")
        total_tax = Decimal("0")
        total_incl_tax = Decimal("0")
        last_full_code = None
        for item_data in request.items:
            raw_code = item_data.item_code or item_data.service_code
            if raw_code:
                normalized_code = normalize_item_code(raw_code, last_full_code)
            else:
                normalized_code = None

            if normalized_code and normalized_code.endswith("..."):
                raise HTTPException(status_code=400, detail="项目编码不完整，无法解析省略号")

            if normalized_code:
                last_full_code = normalized_code

            unit_price = item_data.unit_price if item_data.unit_price is not None else item_data.price
            if unit_price is None:
                raise HTTPException(status_code=400, detail="缺少单价")
            unit_price = Decimal(str(unit_price))
            if unit_price < 0:
                raise HTTPException(status_code=400, detail="单价不能为负数")

            quantity = Decimal(str(item_data.quantity or 1))
            if quantity <= 0:
                raise HTTPException(status_code=400, detail="数量必须大于 0")

            tax_rate = item_data.tax_rate
            if tax_rate is None and normalized_code:
                dict_item = db.query(InvoiceItemDict).filter(InvoiceItemDict.item_code == normalized_code).first()
                if dict_item and dict_item.tax_rate_default is not None:
                    tax_rate = Decimal(str(dict_item.tax_rate_default))
            if tax_rate is None:
                tax_rate = Decimal("0")
            tax_rate = Decimal(str(tax_rate))
            if tax_rate < 0 or tax_rate > 1:
                raise HTTPException(status_code=400, detail="税率必须在 0~1 之间")

            amount_excl_tax, tax_amount, amount_incl_tax = calculate_invoice_line_amounts(unit_price, quantity, tax_rate)

            item_name = item_data.item_name or item_data.description
            if not item_name:
                raise HTTPException(status_code=400, detail="缺少项目名称")

            line_no = item_data.line_no
            new_item = InvoiceItem(
                invoice_id=invoice.id,
                task_id=item_data.task_id,
                line_no=line_no,
                item_id=item_data.item_id,
                category_id=item_data.category_id,
                item_code=normalized_code,
                item_name=item_name,
                specification=item_data.specification,
                unit=item_data.unit,
                unit_price=unit_price,
                amount_excl_tax=amount_excl_tax,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                amount_incl_tax=amount_incl_tax,
                source_task_id=item_data.task_id,
                remark=item_data.remark,
                description=item_name,
                service_code=normalized_code,
                price=unit_price,
                quantity=quantity,
                amount=amount_incl_tax,
                service_date=item_data.service_date,
                service_time_start=item_data.service_time_start,
                service_time_end=item_data.service_time_end
            )
            db.add(new_item)
            total_excl_tax += amount_excl_tax
            total_tax += tax_amount
            total_incl_tax += amount_incl_tax

        invoice.total_excl_tax = total_excl_tax
        invoice.total_tax = total_tax
        invoice.total_incl_tax = total_incl_tax
        invoice.total_amount = total_incl_tax

    try:
        audit = InvoiceAuditLog(
            id=str(uuid.uuid4()),
            invoice_id=invoice.id,
            action="update",
            actor_id=getattr(current_user, "id", None),
            actor_type=getattr(current_user, "role", None) or "admin",
            before_json=before_snapshot,
            after_json=None,
        )
        db.add(audit)
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新发票失败: {str(e)}")

    invoice_with_relations = db.query(Invoice).options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items)
    ).filter(Invoice.id == invoice.id).first()

    if not invoice_with_relations or not invoice_with_relations.customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    upload_dir = ensure_upload_dir()
    pdf_filename = f"invoice_{invoice_with_relations.invoice_number}.pdf"
    pdf_path = upload_dir / "invoices" / pdf_filename
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    generate_invoice_pdf(invoice_with_relations, invoice_with_relations.customer, str(pdf_path))
    invoice_with_relations.pdf_url = str(pdf_path)
    try:
        last_audit = db.query(InvoiceAuditLog).filter(InvoiceAuditLog.invoice_id == invoice.id).order_by(InvoiceAuditLog.changed_at.desc()).first()
        if last_audit and last_audit.after_json is None:
            last_audit.after_json = json.dumps(
                {
                    "id": invoice_with_relations.id,
                    "invoice_number": invoice_with_relations.invoice_number,
                    "customer_id": invoice_with_relations.customer_id,
                    "invoice_date": invoice_with_relations.invoice_date.isoformat() if invoice_with_relations.invoice_date else None,
                    "status": invoice_with_relations.status,
                    "total_amount": str(invoice_with_relations.total_amount) if invoice_with_relations.total_amount is not None else None,
                    "total_excl_tax": str(getattr(invoice_with_relations, "total_excl_tax", None)) if getattr(invoice_with_relations, "total_excl_tax", None) is not None else None,
                    "total_tax": str(getattr(invoice_with_relations, "total_tax", None)) if getattr(invoice_with_relations, "total_tax", None) is not None else None,
                    "total_incl_tax": str(getattr(invoice_with_relations, "total_incl_tax", None)) if getattr(invoice_with_relations, "total_incl_tax", None) is not None else None,
                    "items": [
                        {
                            "id": it.id,
                            "line_no": it.line_no,
                            "item_code": it.item_code or it.service_code,
                            "item_name": it.item_name or it.description,
                            "unit_price": str(it.unit_price or it.price) if (it.unit_price or it.price) is not None else None,
                            "quantity": str(it.quantity) if it.quantity is not None else None,
                            "amount_incl_tax": str(it.amount_incl_tax or it.amount) if (it.amount_incl_tax or it.amount) is not None else None,
                        }
                        for it in (invoice_with_relations.items or [])
                    ],
                },
                ensure_ascii=False,
            )
        db.commit()
    except Exception:
        db.rollback()

    invoice_updated = db.query(Invoice).options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items)
    ).filter(Invoice.id == invoice.id).first()

    return invoice_updated


# ============================================================================
# 已废弃：PDF生成端点 - 现在统一使用Excel格式
# ============================================================================
# @router.post("/{invoice_id}/generate-pdf")
# async def generate_invoice_pdf_endpoint(
#     invoice_id: str,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_user)
# ):
#     """手动生成发票PDF（已废弃，现在使用Excel格式）"""
#     invoice = db.query(Invoice).options(
#         joinedload(Invoice.customer),
#         joinedload(Invoice.items)
#     ).filter(Invoice.id == invoice_id).first()
#     if not invoice:
#         raise HTTPException(status_code=404, detail="发票不存在")
#     
#     customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
#     if not customer:
#         raise HTTPException(status_code=404, detail="客户不存在")
#     
#     try:
#         upload_dir = ensure_upload_dir()
#         pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
#         pdf_path = upload_dir / "invoices" / pdf_filename
#         pdf_path.parent.mkdir(parents=True, exist_ok=True)
#         
#         generate_invoice_pdf(invoice, customer, str(pdf_path))
#         
#         # 更新发票PDF URL（使用绝对路径）
#         invoice.pdf_url = str(pdf_path)
#         db.commit()
#         
#         # 重新加载发票及其关系
#         invoice_with_relations = db.query(Invoice).options(
#             joinedload(Invoice.customer),
#             joinedload(Invoice.items)
#         ).filter(Invoice.id == invoice.id).first()
#         
#         return invoice_with_relations
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"生成PDF失败: {str(e)}")


@router.get("/{invoice_id}/preview")
async def preview_invoice(
    invoice_id: str,
    token: Optional[str] = Query(default=None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: Session = Depends(get_db)
):
    """预览发票文件（支持Excel和PDF），支持token查询参数以便Office Online Viewer访问"""
    # 验证认证：支持token查询参数或Authorization header
    auth_token = token or (credentials.credentials if credentials else None)
    if not auth_token:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    
    # 验证token
    payload = decode_access_token(auth_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.customer), joinedload(Invoice.items))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    if not invoice.pdf_url:
        raise HTTPException(status_code=404, detail="发票文件未生成，请先生成发票")
    
    # 处理路径：如果是相对路径，转换为绝对路径
    file_path = Path(invoice.pdf_url)
    if not file_path.is_absolute():
        # 如果是相对路径，从项目根目录开始
        file_path = Path.cwd() / file_path
    elif not file_path.exists():
        # 如果绝对路径不存在，尝试从uploads目录查找
        upload_dir = ensure_upload_dir()
        file_path = upload_dir / "invoices" / file_path.name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        try:
            customer = invoice.customer or db.query(Customer).filter(Customer.id == invoice.customer_id).first()
            if customer:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                generate_invoice_pdf(invoice, customer, str(file_path))
            else:
                raise HTTPException(status_code=404, detail="客户不存在")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成PDF失败: {str(e)}")

    # 根据文件扩展名确定媒体类型
    if suffix == '.xlsx':
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"invoice_{invoice.invoice_number}.xlsx"
    else:
        media_type = "application/pdf"
        filename = f"invoice_{invoice.invoice_number}.pdf"
    
    # 添加必要的响应头，支持Office Online Viewer和iframe预览
    headers = {
        "Content-Disposition": f"inline; filename=\"{filename}\"",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "Access-Control-Allow-Origin": "*",  # 允许跨域访问（Office Online Viewer需要）
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    
    return FileResponse(
        str(file_path),
        filename=filename,
        media_type=media_type,
        headers=headers
    )


@router.post("/batch/send-unsent", response_model=BatchSendUnsentInvoicesResponse)
async def batch_send_unsent_invoices(
    request: BatchSendUnsentInvoicesRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    language = (getattr(request, "language", None) or "en").strip().lower()
    query = (
        db.query(Invoice)
        .options(joinedload(Invoice.customer), joinedload(Invoice.items))
        .filter(Invoice.sent_at.is_(None), Invoice.voided_at.is_(None))
        .order_by(Invoice.created_at.asc())
    )
    if request.customer_id:
        query = query.filter(Invoice.customer_id == request.customer_id)

    invoices = query.all()
    results = []
    sent = 0
    skipped = 0
    failed = 0

    for invoice in invoices:
        if invoice.sent_at or invoice.status == "sent":
            skipped += 1
            results.append(
                {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "email": invoice.email,
                    "status": "skipped",
                    "reason": "已发送",
                }
            )
            continue

        customer = invoice.customer or db.query(Customer).filter(Customer.id == invoice.customer_id).first()
        if not customer:
            failed += 1
            results.append(
                {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "status": "failed",
                    "reason": "客户不存在",
                }
            )
            continue

        send_to = (
            getattr(invoice, "buyer_email", None)
            or getattr(customer, "invoice_receiver_email", None)
            or getattr(customer, "email", None)
        )
        if not send_to:
            failed += 1
            results.append(
                {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "status": "failed",
                    "reason": "客户邮箱不存在，无法发送邮件",
                }
            )
            continue

        try:
            file_path = _ensure_invoice_pdf_file(db, invoice, customer)
            if not file_path.exists():
                raise ValueError("发票文件不存在")
            send_invoice_email(invoice, customer, str(file_path), to_email=send_to, language=language)
            if invoice.status != "paid":
                invoice.status = "sent"
            invoice.sent_at = datetime.utcnow()
            invoice.email = send_to
            db.commit()
            sent += 1
            results.append(
                {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "email": send_to,
                    "status": "sent",
                }
            )
        except Exception as e:
            db.rollback()
            failed += 1
            results.append(
                {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_id": invoice.customer_id,
                    "email": send_to,
                    "status": "failed",
                    "reason": str(e),
                }
            )

    return {
        "total": len(invoices),
        "sent": sent,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    language: str = Query("en", description="邮件语言：zh / en"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """发送发票到客户邮箱"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    if not invoice.pdf_url:
        raise HTTPException(status_code=400, detail="发票文件未生成，请先生成发票")
    
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    send_to = (getattr(invoice, "buyer_email", None) or getattr(customer, "invoice_receiver_email", None) or customer.email)
    if not send_to:
        raise HTTPException(status_code=400, detail="客户邮箱不存在，无法发送邮件")
    
    # 处理路径：如果是相对路径，转换为绝对路径
    file_path = Path(invoice.pdf_url)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path
    elif not file_path.exists():
        upload_dir = ensure_upload_dir()
        file_path = upload_dir / "invoices" / file_path.name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="发票文件不存在")
    
    try:
        send_invoice_email(invoice, customer, str(file_path), to_email=send_to, language=(language or "en").strip().lower())
        if invoice.status != "paid":
            invoice.status = "sent"
        invoice.sent_at = datetime.utcnow()
        invoice.email = send_to
        db.commit()
        return {"message": "发票已成功发送", "email": send_to}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送邮件失败: {str(e)}")


@router.put("/{invoice_id}/status")
async def update_invoice_status(
    invoice_id: str,
    new_status: str = Query(..., description="新状态"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新发票状态"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    invoice.status = new_status
    if new_status == "paid":
        # 可以添加支付时间等逻辑
        pass
    
    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除发票"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    # 删除发票文件（支持Excel和PDF）
    if invoice.pdf_url:
        file_path = Path(invoice.pdf_url)
        if file_path.exists():
            file_path.unlink()

    db.query(InvoiceItemDict).filter(InvoiceItemDict.created_from_invoice_id == invoice_id).update(
        {"created_from_invoice_id": None}, synchronize_session=False
    )
    db.query(InvoiceAuditLog).filter(InvoiceAuditLog.invoice_id == invoice_id).delete(synchronize_session=False)
    db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete(synchronize_session=False)
    
    db.delete(invoice)
    db.commit()
    return None
