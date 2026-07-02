from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional, Any
from core.database import get_db
from shared.models import (
    Task,
    TaskStatus as TaskStatusEnum,
    Employee,
    Customer,
    BusinessUnread,
    TaskPhoto,
    TaskLocationTrack,
    InvoiceServiceCode,
    InvoiceServiceLevel1,
    InvoiceServiceLevel2,
    InvoiceServiceLevel3,
    TaskServiceItem,
    Questionnaire,
    TaskQuestionnaire,
    TaskCancellationNotification,
    QuestionnaireResponse,
    Document,
    InvoiceItem,
    IncidentReport,
    CorrectionRequest,
)
from shared.models.update_notification import touch_business_unread
from shared.models.customer import CUSTOMER_STATUS_ARCHIVED
from ..schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatus, TaskServiceLineCreate
from modules.app.schemas.task import LocationTrackResponse
from ..dependencies import get_current_user
from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import json
import logging
import base64
import mimetypes
import re

router = APIRouter(prefix="/api/houtai/tasks", tags=["管理-任务"])
logger = logging.getLogger(__name__)


def _parse_data_url(data_url: str):
    match = re.match(r"^data:(.+?);base64,(.+)$", data_url, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None, None
    mime_type = match.group(1)
    raw = re.sub(r"\s+", "", match.group(2).strip())
    try:
        return mime_type, base64.b64decode(raw)
    except Exception:
        return None, None


def _guess_mime_from_path(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def _build_task_response(task: Task):
    data = TaskResponse.model_validate(task).model_dump()
    data["assigned_employee_name"] = task.assigned_employee.name if task.assigned_employee else None
    return data


def _week_bounds_local(reference: datetime | None = None) -> tuple[datetime, datetime]:
    # 强制使用本地时间
    now = reference or datetime.now()
    today = now.date()
    # 这里的 weekday() 返回 0-6，对应 周一到周日
    # 我们认为周一是一周的开始
    week_start_date = today - timedelta(days=today.weekday())
    start = datetime.combine(week_start_date, dt_time(0, 0))
    # 结束时间为下周一 00:00:00
    end = start + timedelta(days=7)
    
    # 调试日志：确认时间范围
    logger.info(f"Weekly bounds calculation: reference={now}, start={start}, end={end}")
    
    return start, end


def _parse_hours(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        s = str(value).strip()
        if not s:
            return 0.0
        return float(s.replace(",", "."))
    except Exception:
        return 0.0


def recalc_customer_weekly_served_hours(db: Session, customer_id: str) -> float:
    start, end = _week_bounds_local()
    task_statuses = [TaskStatusEnum.approved]

    # 获取本周该客户的所有已审核通过的任务，并加载其服务项
    tasks = (
        db.query(Task)
        .options(joinedload(Task.service_items))
        .filter(
            Task.customer_id == customer_id,
            Task.status.in_(task_statuses),
            Task.service_time >= start,
            Task.service_time < end,
        )
        .all()
    )

    total_hours = 0.0
    for t in tasks:
        if t.service_items:
            # 如果任务有服务项，累加服务项的数量（通常代表时长）
            task_items_total = sum(float(item.quantity or 0) for item in t.service_items)
            total_hours += task_items_total
        else:
            # 如果没有服务项，尝试从任务本身的 service_duration_hours 字段获取时长
            total_hours += _parse_hours(t.service_duration_hours)

    # 调试日志
    logger.info(f"Recalc hours for customer {customer_id}: bounds=[{start}, {end}), total={total_hours} (tasks_count={len(tasks)})")

    # 更新客户的周累计时长
    db.query(Customer).filter(Customer.id == customer_id).update(
        {"weekly_served_hours": total_hours}
    )
    db.commit()
    return total_hours

def _notify_employee_task_status_changed(
    db: Session,
    employee_id: str | None,
    task_id: str,
    old_status: str | None,
    new_status: str | None,
):
    if not employee_id:
        return
    try:
        touch_business_unread(
            db,
            business_code="task",
            receiver_user_id=str(employee_id),
            data_id=str(task_id),
        )
        db.commit()
    except Exception:
        db.rollback()

def _delete_task_internal(db: Session, task_id: str) -> None:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.query(TaskCancellationNotification).filter(TaskCancellationNotification.task_id == task_id).delete(synchronize_session=False)
    db.query(TaskQuestionnaire).filter(TaskQuestionnaire.task_id == task_id).delete(synchronize_session=False)
    db.query(QuestionnaireResponse).filter(QuestionnaireResponse.task_id == task_id).delete(synchronize_session=False)
    db.query(IncidentReport).filter(IncidentReport.task_id == task_id).delete(synchronize_session=False)
    db.query(CorrectionRequest).filter(CorrectionRequest.task_id == task_id).delete(synchronize_session=False)
    db.query(Document).filter(Document.task_id == task_id).delete(synchronize_session=False)
    db.query(TaskServiceItem).filter(TaskServiceItem.task_id == task_id).delete(synchronize_session=False)
    db.query(TaskPhoto).filter(TaskPhoto.task_id == task_id).delete(synchronize_session=False)
    db.query(TaskLocationTrack).filter(TaskLocationTrack.task_id == task_id).delete(synchronize_session=False)
    for item in db.query(InvoiceItem).filter(InvoiceItem.task_id == task_id).all():
        item.task_id = None
    for item in db.query(InvoiceItem).filter(InvoiceItem.source_task_id == task_id).all():
        item.source_task_id = None
    customer_id = task.customer_id
    db.delete(task)
    try:
        recalc_customer_weekly_served_hours(db, customer_id)
    except Exception:
        pass


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    field: Optional[str] = None,
    keyword: Optional[str] = None,
    assigned_employee_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取所有任务列表"""
    unread_task_ids = {
        (r.data_id or "")
        for r in db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_user.id),
            BusinessUnread.business_code == "task",
            BusinessUnread.is_unread == 1,
        )
        .all()
    }
    query = db.query(Task).options(
        joinedload(Task.customer),
        joinedload(Task.assigned_employee),
        joinedload(Task.service_items),
        joinedload(Task.task_questionnaires)
    )
    if status:
        query = query.filter(Task.status == status.value)
    if assigned_employee_id:
        # 只返回分配给指定员工的任务，且确保assigned_employee_id不为空
        query = query.filter(
            Task.assigned_employee_id == assigned_employee_id,
            Task.assigned_employee_id.isnot(None)
        )
    keyword_value = (keyword or "").strip()
    if keyword_value:
        like_value = f"%{keyword_value}%"
        query = query.join(Customer, Task.customer_id == Customer.id)
        query = query.outerjoin(Employee, Task.assigned_employee_id == Employee.id)
        if field == "customer_name":
            query = query.filter(Customer.name.ilike(like_value))
        elif field == "assigned_employee":
            query = query.filter(
                or_(
                    Employee.name.ilike(like_value),
                    Employee.employee_number.ilike(like_value)
                )
            )
        elif field == "title":
            query = query.filter(Task.title.ilike(like_value))
        else:
            query = query.filter(
                or_(
                    Customer.name.ilike(like_value),
                    Employee.name.ilike(like_value),
                    Employee.employee_number.ilike(like_value),
                    Task.title.ilike(like_value)
                )
            )
    tasks = query.order_by(
        Task.service_start_time.desc(),
        Task.service_time.desc(),
        Task.created_at.desc()
    ).all()
    result = []
    for t in tasks:
        data = _build_task_response(t)
        data["has_update"] = str(t.id) in unread_task_ids
        result.append(data)
    return result


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建任务"""
    services = task_data.services
    questionnaires = task_data.questionnaires
    task_dict = task_data.model_dump(exclude={"services", "questionnaires"}, exclude_none=True)
    repeat_rule = task_dict.pop("repeat_rule", None)
    repeat_months = task_dict.pop("repeat_months", None)
    assigned_employee_id = task_dict.pop("assigned_employee_id", None)
    customer_id = task_dict.get("customer_id")
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail="客户不存在")
    if getattr(customer, "customer_status", None) != CUSTOMER_STATUS_ARCHIVED:
        raise HTTPException(status_code=400, detail="只有已建档的客户可以新建任务")
    questionnaire_id = task_dict.get("questionnaire_id")
    service_start_time = task_dict.get("service_start_time")
    service_end_time = task_dict.get("service_end_time")
    if service_start_time and not task_dict.get("service_time"):
        task_dict["service_time"] = service_start_time
    if not questionnaire_id and questionnaires:
        first_qid = (
            questionnaires[0].get("questionnaire_id")
            if isinstance(questionnaires[0], dict)
            else getattr(questionnaires[0], "questionnaire_id", None)
        )
        if first_qid:
            task_dict["questionnaire_id"] = first_qid
            questionnaire_id = first_qid
    if questionnaire_id:
        q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
        if not q:
            raise HTTPException(status_code=400, detail="选择的问卷不存在")
        if not getattr(q, "is_active", True):
            raise HTTPException(status_code=400, detail="选择的问卷未启用")
    else:
        customer_type = getattr(customer, "customer_type", None) if customer else None
        q_query = db.query(Questionnaire).filter(Questionnaire.is_active == True)
        if customer_type:
            match_types = [customer_type]
            if customer_type == "助残":
                match_types.append("NDIS")
            q_query = q_query.filter(or_(
                Questionnaire.customer_type.in_(match_types),
                Questionnaire.customer_type == None
            ))
        preferred = q_query.first()
        if not preferred:
            preferred = db.query(Questionnaire).filter(Questionnaire.is_active == True).first()
        if preferred:
            task_dict["questionnaire_id"] = preferred.id
    # 创建任务时始终为待领取状态，即使指定了员工
    task = Task(**task_dict, status=TaskStatusEnum.pending)
    if assigned_employee_id:
        employee = db.query(Employee).filter(Employee.id == assigned_employee_id).first()
        if not employee:
            raise HTTPException(status_code=400, detail="指定员工不存在")
        # 即使指定了员工，任务状态仍为待领取，需要员工主动领取后才会变为进行中
        task.assigned_employee_id = assigned_employee_id
        # 不设置 assigned_at，等员工领取时再设置
        # 不设置状态为 in_progress，保持 pending 状态
    if repeat_rule:
        normalized_rule = str(repeat_rule).strip().lower()
        rule_map = {
            "weekly": "weekly",
            "every_week": "weekly",
            "week": "weekly",
            "odd_week": "odd_week",
            "single_week": "odd_week",
            "even_week": "even_week",
            "double_week": "even_week",
        }
        task.recurrence_rule = rule_map.get(normalized_rule) or None
    if repeat_months is not None:
        try:
            task.recurrence_months = int(repeat_months)
        except Exception:
            task.recurrence_months = None
    db.add(task)
    db.flush()
    normalized = []
    if services:
        accepted_ids = {svc.id for svc in getattr(customer, "accepted_service_level1", [])} if customer else set()
        for idx, line in enumerate(services, start=1):
            line_level1_id = (line.get("level1_id") if isinstance(line, dict) else getattr(line, "level1_id", None))
            line_level2_id = (line.get("level2_id") if isinstance(line, dict) else getattr(line, "level2_id", None))
            line_level3_id = (line.get("level3_id") if isinstance(line, dict) else getattr(line, "level3_id", None))
            line_service_code = (line.get("service_code") if isinstance(line, dict) else getattr(line, "service_code", None))
            line_unit_price_override = (line.get("unit_price_override") if isinstance(line, dict) else getattr(line, "unit_price_override", None))
            line_duration_hours = (line.get("duration_hours") if isinstance(line, dict) else getattr(line, "duration_hours", None))
            line_remark = (line.get("remark") if isinstance(line, dict) else getattr(line, "remark", None))
            line_service_time_start = (line.get("service_time_start") if isinstance(line, dict) else getattr(line, "service_time_start", None))
            line_service_time_end = (line.get("service_time_end") if isinstance(line, dict) else getattr(line, "service_time_end", None))
            if accepted_ids and line_level1_id and line_level1_id not in accepted_ids:
                raise HTTPException(status_code=400, detail="选择的一级服务不在客户可接受范围")
            code = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.code == line_service_code, InvoiceServiceCode.is_active == True).first()
            if not code:
                raise HTTPException(status_code=400, detail="服务编码不存在或未启用")
            if code.price is None and line_unit_price_override is None:
                raise HTTPException(status_code=400, detail="服务编码未设置单价，请先在服务编码中设置单价或填写覆盖单价")
            unit_price = Decimal(str(code.price)) if code.price is not None else Decimal("0")
            if line_unit_price_override is not None:
                unit_price = Decimal(str(line_unit_price_override))
            quantity = Decimal(str(line_duration_hours or "0"))
            amount = (unit_price * quantity).quantize(Decimal("0.01"))
            normalized.append({
                "line_no": idx,
                "level1_id": line_level1_id,
                "level2_id": line_level2_id,
                "level3_id": line_level3_id,
                "service_code": line_service_code,
                "unit": str(code.unit) if code.unit else None,
                "unit_price": str(unit_price),
                "quantity": str(quantity),
                "amount": str(amount),
                "remark": line_remark,
                "service_time_start": line_service_time_start,
                "service_time_end": line_service_time_end,
            })
        for line in normalized:
            db.add(TaskServiceItem(
                task_id=task.id,
                level1_id=line["level1_id"],
                level2_id=line["level2_id"],
                level3_id=line["level3_id"],
                service_code=line["service_code"],
                unit=line["unit"],
                unit_price=Decimal(str(line["unit_price"])),
                quantity=Decimal(str(line["quantity"])),
                amount=Decimal(str(line["amount"])),
                remark=line["remark"],
                service_time_start=line["service_time_start"],
                service_time_end=line["service_time_end"],
            ))

    normalized_questionnaires = []
    if questionnaires:
        for q_line in questionnaires:
            q_id = (q_line.get("questionnaire_id") if isinstance(q_line, dict) else getattr(q_line, "questionnaire_id", None))
            q_is_required = (q_line.get("is_required", True) if isinstance(q_line, dict) else getattr(q_line, "is_required", True))
            q_order = (q_line.get("order_index", 0) if isinstance(q_line, dict) else getattr(q_line, "order_index", 0))
            if not q_id:
                continue
            q = db.query(Questionnaire).filter(Questionnaire.id == q_id).first()
            if not q:
                raise HTTPException(status_code=400, detail="选择的问卷不存在")
            if not getattr(q, "is_active", True):
                raise HTTPException(status_code=400, detail="选择的问卷未启用")
            normalized_questionnaires.append(
                {
                    "questionnaire_id": q_id,
                    "is_required": bool(q_is_required),
                    "order_index": int(q_order or 0),
                }
            )
        for q_line in normalized_questionnaires:
            db.add(TaskQuestionnaire(
                task_id=task.id,
                questionnaire_id=q_line["questionnaire_id"],
                is_required=q_line["is_required"],
                order_index=q_line["order_index"],
            ))


    def _shift_service_item_time_str(val: str | None, day_delta: int) -> str | None:
        if not val or not isinstance(val, str):
            return val
        s = val.strip()
        if len(s) < 10:
            return val
        try:
            date_part = s[:10]
            base_date = datetime.strptime(date_part, "%Y-%m-%d").date()
            new_date = base_date + timedelta(days=day_delta)
            return f"{new_date.strftime('%Y-%m-%d')}{s[10:]}"
        except Exception:
            return val

    should_generate_repeat = bool(task.recurrence_rule) and bool(task.recurrence_months) and int(task.recurrence_months) > 0
    if should_generate_repeat:
        anchor = task.service_start_time or task.service_time
        if anchor:
            end_at = anchor + relativedelta(months=int(task.recurrence_months))
            base_title = task.title

            def _next_occurrences(start_dt: datetime, rule: str):
                if rule == "weekly":
                    cursor = start_dt + timedelta(days=7)
                    while True:
                        yield cursor
                        cursor = cursor + timedelta(days=7)
                if rule in ("odd_week", "even_week"):
                    want_odd = rule == "odd_week"
                    cursor = start_dt + timedelta(days=7)
                    while (cursor.isocalendar().week % 2 == 1) != want_odd:
                        cursor = cursor + timedelta(days=7)
                    while True:
                        yield cursor
                        cursor = cursor + timedelta(days=14)

            generated_index = 2
            for next_anchor in _next_occurrences(anchor, task.recurrence_rule):
                if next_anchor >= end_at:
                    break
                day_delta = (next_anchor.date() - anchor.date()).days
                new_task = Task(
                    title=f"{base_title}-{generated_index}",
                    description=task.description,
                    customer_id=task.customer_id,
                    service_time=(task.service_time + timedelta(days=day_delta)) if task.service_time else next_anchor,
                    service_start_time=(task.service_start_time + timedelta(days=day_delta)) if task.service_start_time else None,
                    service_end_time=(task.service_end_time + timedelta(days=day_delta)) if task.service_end_time else None,
                    status=TaskStatusEnum.pending,
                    assigned_employee_id=task.assigned_employee_id,
                    questionnaire_id=task.questionnaire_id,
                    service_code=task.service_code,
                    service_duration_hours=task.service_duration_hours,
                    unit_price=task.unit_price,
                    latest_claim_time=(task.latest_claim_time + timedelta(days=day_delta)) if task.latest_claim_time else None,
                )
                db.add(new_task)
                db.flush()
                for line in normalized:
                    db.add(TaskServiceItem(
                        task_id=new_task.id,
                        level1_id=line["level1_id"],
                        level2_id=line["level2_id"],
                        level3_id=line["level3_id"],
                        service_code=line["service_code"],
                        unit=line["unit"],
                        unit_price=Decimal(str(line["unit_price"])),
                        quantity=Decimal(str(line["quantity"])),
                        amount=Decimal(str(line["amount"])),
                        remark=line["remark"],
                        service_time_start=_shift_service_item_time_str(line.get("service_time_start"), day_delta),
                        service_time_end=_shift_service_item_time_str(line.get("service_time_end"), day_delta),
                    ))
                for q_line in normalized_questionnaires:
                    db.add(TaskQuestionnaire(
                        task_id=new_task.id,
                        questionnaire_id=q_line["questionnaire_id"],
                        is_required=q_line["is_required"],
                        order_index=q_line["order_index"],
                    ))
                generated_index += 1
    db.commit()
    db.refresh(task)
    return task


@router.get("/customers/options", response_model=List[dict])
async def get_archived_customer_options(
    keyword: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Customer).filter(Customer.customer_status == CUSTOMER_STATUS_ARCHIVED)
    keyword_value = (keyword or "").strip()
    if keyword_value:
        like_value = f"%{keyword_value}%"
        query = query.filter(
            or_(
                Customer.name.ilike(like_value),
                Customer.customer_code.ilike(like_value),
            )
        )
    rows = query.order_by(Customer.name.asc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "customer_code": r.customer_code,
        }
        for r in rows
    ]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取任务详情"""
    task = db.query(Task).options(
        joinedload(Task.customer),
        joinedload(Task.assigned_employee),
        joinedload(Task.service_items),
        joinedload(Task.task_questionnaires)
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _build_task_response(task)


@router.get("/customer/{customer_id}/service-level1", response_model=List[dict])
async def get_customer_accepted_service_level1(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    ids = [svc.id for svc in getattr(customer, "accepted_service_level1", []) or []]
    if not ids:
        return []
    query = db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.is_active == True, InvoiceServiceLevel1.id.in_(ids))
    rows = query.order_by(InvoiceServiceLevel1.sort_order.asc(), InvoiceServiceLevel1.name.asc()).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("/customer/{customer_id}/service-level2", response_model=List[dict])
async def get_customer_service_level2(
    customer_id: str,
    level1_id: str = Query(..., description="一级大类ID"),
    include_inactive: bool = Query(False, description="是否包含停用"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    accepted_ids = {svc.id for svc in getattr(customer, "accepted_service_level1", []) or []}
    if accepted_ids and level1_id not in accepted_ids:
        return []
    query = db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.level1_id == level1_id)
    if not include_inactive:
        query = query.filter(InvoiceServiceLevel2.is_active == True)
    rows = query.order_by(InvoiceServiceLevel2.sort_order.asc(), InvoiceServiceLevel2.name.asc()).all()
    return [{"id": r.id, "name": r.name, "level1_id": r.level1_id} for r in rows]


@router.get("/customer/{customer_id}/service-level3", response_model=List[dict])
async def get_customer_service_level3(
    customer_id: str,
    level1_id: str = Query(..., description="一级大类ID"),
    level2_id: Optional[str] = Query(None, description="二级大类ID（可为空）"),
    include_inactive: bool = Query(False, description="是否包含停用"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    accepted_ids = {svc.id for svc in getattr(customer, "accepted_service_level1", []) or []}
    if accepted_ids and level1_id not in accepted_ids:
        return []
    query = db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.level1_id == level1_id)
    if not include_inactive:
        query = query.filter(InvoiceServiceLevel3.is_active == True)
    if level2_id:
        query = query.filter(InvoiceServiceLevel3.level2_id == level2_id)
    else:
        query = query.filter(InvoiceServiceLevel3.level2_id.is_(None))
    rows = query.order_by(InvoiceServiceLevel3.sort_order.asc(), InvoiceServiceLevel3.name.asc()).all()
    return [{"id": r.id, "name": r.name, "level1_id": r.level1_id, "level2_id": r.level2_id} for r in rows]


@router.get("/customer/{customer_id}/service-codes", response_model=List[dict])
async def get_customer_service_codes(
    customer_id: str,
    level3_id: str = Query(..., description="三级服务项目ID"),
    include_inactive: bool = Query(False, description="是否包含停用"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    level3 = db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.id == level3_id).first()
    if not level3:
        return []
    accepted_ids = {svc.id for svc in getattr(customer, "accepted_service_level1", []) or []}
    if accepted_ids and level3.level1_id not in accepted_ids:
        return []
    if not include_inactive and not getattr(level3, "is_active", True):
        return []
    query = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.level3_id == level3_id)
    if not include_inactive:
        query = query.filter(InvoiceServiceCode.is_active == True)
    rows = query.order_by(InvoiceServiceCode.code.asc()).all()
    return [
        {
            "id": r.id,
            "level3_id": r.level3_id,
            "code": r.code,
            "price": str(r.price) if r.price is not None else None,
            "unit": r.unit,
            "is_active": bool(r.is_active),
        }
        for r in rows
    ]


@router.get("/{task_id}/signature/image")
async def get_task_signature_image(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取任务签名图片"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.signature_blob:
        raise HTTPException(status_code=404, detail="签名不存在")
    return Response(content=task.signature_blob, media_type=task.signature_mime or "image/png")


@router.put("/{task_id}/signature", response_model=TaskResponse)
async def update_task_signature(
    task_id: str,
    signature_data: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task = db.query(Task).options(joinedload(Task.customer), joinedload(Task.assigned_employee)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    mime_type = None
    blob = None
    if isinstance(signature_data, str) and signature_data.startswith("data:image"):
        mime_type, blob = _parse_data_url(signature_data)
    elif signature_data:
        mime_type = _guess_mime_from_path(signature_data)

    if blob:
        task.signature_blob = blob
        task.signature_mime = mime_type or "image/png"
        task.signature_image_url = f"/api/houtai/tasks/{task_id}/signature/image"
    else:
        task.signature_blob = None
        task.signature_mime = None
        task.signature_image_url = signature_data or None
    db.commit()
    db.refresh(task)
    return _build_task_response(task)


@router.delete("/{task_id}/signature")
async def delete_task_signature(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.signature_blob = None
    task.signature_mime = None
    task.signature_image_url = None
    db.commit()
    return {"message": "签名已删除"}


@router.get("/{task_id}/photos/{photo_id}")
async def get_task_photo(
    task_id: str,
    photo_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取任务照片"""
    photo = db.query(TaskPhoto).filter(
        TaskPhoto.id == photo_id,
        TaskPhoto.task_id == task_id
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    return Response(content=photo.photo_blob, media_type=photo.photo_mime or "image/jpeg")


@router.post("/{task_id}/photos", response_model=TaskResponse)
async def upload_task_photos(
    task_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task = db.query(Task).options(joinedload(Task.customer), joinedload(Task.assigned_employee)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    existing_urls = task.photo_urls or []
    if not isinstance(existing_urls, list):
        existing_urls = []

    new_urls: list[str] = []
    for file in files:
        content = await file.read()
        mime_type = file.content_type or _guess_mime_from_path(file.filename or "")
        if not mime_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="仅支持上传图片文件")
        photo = TaskPhoto(task_id=task_id, photo_blob=content, photo_mime=mime_type)
        db.add(photo)
        db.flush()
        new_urls.append(f"/api/houtai/tasks/{task_id}/photos/{photo.id}")

    task.photo_urls = existing_urls + new_urls
    db.commit()
    db.refresh(task)
    return _build_task_response(task)


@router.delete("/{task_id}/photos/{photo_id}")
async def delete_task_photo(
    task_id: str,
    photo_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    photo = db.query(TaskPhoto).filter(TaskPhoto.id == photo_id, TaskPhoto.task_id == task_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    db.delete(photo)
    urls = task.photo_urls or []
    if isinstance(urls, list):
        task.photo_urls = [url for url in urls if not str(url).endswith(f"/{photo_id}")]
    db.commit()
    return {"message": "照片已删除"}


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    old_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    old_assigned_employee_id = getattr(task, "assigned_employee_id", None)
    
    services = task_data.services if "services" in task_data.model_fields_set else None
    questionnaires = task_data.questionnaires if "questionnaires" in task_data.model_fields_set else None
    raw_service_plans = task_data.service_plans if "service_plans" in task_data.model_fields_set else None
    should_recalc_customer_weekly = (
        services is not None
        or raw_service_plans is not None
        or ("status" in task_data.model_fields_set)
        or ("service_time" in task_data.model_fields_set)
        or ("service_start_time" in task_data.model_fields_set)
        or ("service_end_time" in task_data.model_fields_set)
    )
    update_data = task_data.model_dump(exclude_unset=True, exclude={"services", "service_plans", "repeat_rule", "repeat_months"})
    if "status" in update_data:
        update_data["status"] = TaskStatusEnum(update_data["status"])
    if "service_start_time" in update_data and "service_time" not in update_data:
        update_data["service_time"] = update_data["service_start_time"]
    if "assigned_employee_id" in update_data:
        assigned_employee_id = update_data["assigned_employee_id"]
        if assigned_employee_id:
            employee = db.query(Employee).filter(Employee.id == assigned_employee_id).first()
            if not employee:
                raise HTTPException(status_code=400, detail="指定员工不存在")
            if not task.assigned_at:
                task.assigned_at = datetime.utcnow()
        else:
            task.assigned_at = None
    if "questionnaire_id" in update_data:
        qid = update_data.get("questionnaire_id")
        if qid:
            q = db.query(Questionnaire).filter(Questionnaire.id == qid).first()
            if not q:
                raise HTTPException(status_code=400, detail="选择的问卷不存在")
            if not getattr(q, "is_active", True):
                raise HTTPException(status_code=400, detail="选择的问卷未启用")
    if services is not None:
        customer = db.query(Customer).filter(Customer.id == task.customer_id).first()
        accepted_ids = {svc.id for svc in getattr(customer, "accepted_service_level1", [])} if customer else set()
        normalized = []
        for idx, line in enumerate(services, start=1):
            line_level1_id = (line.get("level1_id") if isinstance(line, dict) else getattr(line, "level1_id", None))
            line_level2_id = (line.get("level2_id") if isinstance(line, dict) else getattr(line, "level2_id", None))
            line_level3_id = (line.get("level3_id") if isinstance(line, dict) else getattr(line, "level3_id", None))
            line_service_code = (line.get("service_code") if isinstance(line, dict) else getattr(line, "service_code", None))
            line_unit_price_override = (line.get("unit_price_override") if isinstance(line, dict) else getattr(line, "unit_price_override", None))
            line_duration_hours = (line.get("duration_hours") if isinstance(line, dict) else getattr(line, "duration_hours", None))
            line_remark = (line.get("remark") if isinstance(line, dict) else getattr(line, "remark", None))
            line_service_time_start = (line.get("service_time_start") if isinstance(line, dict) else getattr(line, "service_time_start", None))
            line_service_time_end = (line.get("service_time_end") if isinstance(line, dict) else getattr(line, "service_time_end", None))
            if accepted_ids and line_level1_id and line_level1_id not in accepted_ids:
                raise HTTPException(status_code=400, detail="选择的一级服务不在客户可接受范围")
            code = (
                db.query(InvoiceServiceCode)
                .filter(InvoiceServiceCode.code == line_service_code, InvoiceServiceCode.is_active == True)
                .first()
            )
            if not code:
                raise HTTPException(status_code=400, detail="服务编码不存在或未启用")
            if code.price is None and line_unit_price_override is None:
                raise HTTPException(status_code=400, detail="服务编码未设置单价，请先在服务编码中设置单价或填写覆盖单价")
            unit_price = Decimal(str(code.price)) if code.price is not None else Decimal("0")
            if line_unit_price_override is not None:
                unit_price = Decimal(str(line_unit_price_override))
            quantity = Decimal(str(line_duration_hours or "0"))
            amount = (unit_price * quantity).quantize(Decimal("0.01"))
            normalized.append({
                "line_no": idx,
                "level1_id": line_level1_id,
                "level2_id": line_level2_id,
                "level3_id": line_level3_id,
                "service_code": line_service_code,
                "unit": str(code.unit) if code.unit else None,
                "unit_price": str(unit_price),
                "quantity": str(quantity),
                "amount": str(amount),
                "remark": line_remark,
                "service_time_start": line_service_time_start,
                "service_time_end": line_service_time_end,
            })
        db.query(TaskServiceItem).filter(TaskServiceItem.task_id == task.id).delete()
        for line in normalized:
            db.add(TaskServiceItem(
                task_id=task.id,
                level1_id=line.get("level1_id"),
                level2_id=line.get("level2_id"),
                level3_id=line.get("level3_id"),
                service_code=line.get("service_code"),
                unit=line["unit"],
                unit_price=Decimal(str(line["unit_price"])),
                quantity=Decimal(str(line["quantity"])),
                amount=Decimal(str(line["amount"])),
                remark=line["remark"],
                service_time_start=line["service_time_start"],
                service_time_end=line["service_time_end"],
            ))
        # 不再写入任务表的 service_plans
    elif raw_service_plans is not None:
        db.query(TaskServiceItem).filter(TaskServiceItem.task_id == task.id).delete()
        normalized = []
        for idx, line in enumerate(raw_service_plans or [], start=1):
            unit_price = Decimal(str(line.get("unit_price") or "0"))
            quantity = Decimal(str(line.get("quantity") or "0"))
            amount = Decimal(str(line.get("amount") or (unit_price * quantity)))
            normalized.append({
                "line_no": idx,
                "level1_id": line.get("level1_id"),
                "level2_id": line.get("level2_id"),
                "level3_id": line.get("level3_id"),
                "service_code": line.get("service_code"),
                "unit": line.get("unit"),
                "unit_price": str(unit_price),
                "quantity": str(quantity),
                "amount": str(amount),
                "remark": line.get("remark"),
                "service_time_start": line.get("service_time_start"),
                "service_time_end": line.get("service_time_end"),
            })
            db.add(TaskServiceItem(
                task_id=task.id,
                level1_id=line.get("level1_id"),
                level2_id=line.get("level2_id"),
                level3_id=line.get("level3_id"),
                service_code=line.get("service_code"),
                unit=line.get("unit"),
                unit_price=unit_price,
                quantity=quantity,
                amount=amount,
                remark=line.get("remark"),
                service_time_start=line.get("service_time_start"),
                service_time_end=line.get("service_time_end"),
            ))
        # 不再写入任务表的 service_plans
    if questionnaires is not None:
        db.query(TaskQuestionnaire).filter(TaskQuestionnaire.task_id == task.id).delete()
        for q_line in questionnaires:
            q_id = (q_line.get("questionnaire_id") if isinstance(q_line, dict) else getattr(q_line, "questionnaire_id", None))
            q_is_required = (q_line.get("is_required", True) if isinstance(q_line, dict) else getattr(q_line, "is_required", True))
            q_order = (q_line.get("order_index", 0) if isinstance(q_line, dict) else getattr(q_line, "order_index", 0))
            if q_id:
                db.add(TaskQuestionnaire(
                    task_id=task.id,
                    questionnaire_id=q_id,
                    is_required=q_is_required,
                    order_index=q_order,
                ))
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    new_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    new_assigned_employee_id = getattr(task, "assigned_employee_id", None)
    if old_status != new_status or old_assigned_employee_id != new_assigned_employee_id:
        _notify_employee_task_status_changed(
            db,
            new_assigned_employee_id,
            str(task.id),
            old_status,
            new_status,
        )
    if should_recalc_customer_weekly:
        try:
            recalc_customer_weekly_served_hours(db, task.customer_id)
        except Exception:
            pass
    return task


@router.get("/{task_id}/services")
async def list_task_services(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    items = (
        db.query(TaskServiceItem)
        .filter(TaskServiceItem.task_id == task_id)
        .order_by(TaskServiceItem.created_at.asc())
        .all()
    )
    return [
        {
            "id": i.id,
            "level1_id": i.level1_id,
            "level2_id": i.level2_id,
            "level3_id": i.level3_id,
            "service_code": i.service_code,
            "unit": i.unit,
            "unit_price": str(i.unit_price or 0),
            "quantity": str(i.quantity or 0),
            "amount": str(i.amount or 0),
            "remark": i.remark,
            "service_time_start": i.service_time_start,
            "service_time_end": i.service_time_end,
        }
        for i in items
    ]


@router.post("/{task_id}/services")
async def add_task_service(
    task_id: str,
    payload: TaskServiceLineCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    customer = db.query(Customer).filter(Customer.id == task.customer_id).first()
    accepted_ids = {svc.id for svc in getattr(customer, "accepted_service_level1", [])} if customer else set()
    if accepted_ids and payload.level1_id not in accepted_ids:
        raise HTTPException(status_code=400, detail="选择的一级服务不在客户可接受范围")
    code = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.code == payload.service_code, InvoiceServiceCode.is_active == True).first()
    if not code:
        raise HTTPException(status_code=400, detail="服务编码不存在或未启用")
    if code.price is None and payload.unit_price_override is None:
        raise HTTPException(status_code=400, detail="服务编码未设置单价，请先在服务编码中设置单价或填写覆盖单价")
    unit_price = Decimal(str(code.price)) if code.price is not None else Decimal("0")
    if payload.unit_price_override is not None:
        unit_price = Decimal(str(payload.unit_price_override))
    quantity = Decimal(str(payload.duration_hours))
    amount = (unit_price * quantity).quantize(Decimal("0.01"))
    item = TaskServiceItem(
        task_id=task_id,
        level1_id=payload.level1_id,
        level2_id=payload.level2_id,
        level3_id=payload.level3_id,
        service_code=payload.service_code,
        unit=str(code.unit) if code.unit else None,
        unit_price=unit_price,
        quantity=quantity,
        amount=amount,
        remark=payload.remark,
        service_time_start=payload.service_time_start,
        service_time_end=payload.service_time_end,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    try:
        recalc_customer_weekly_served_hours(db, task.customer_id)
    except Exception as e:
        logger.error(f"Error in approve_task recalculating hours: {e}", exc_info=True)
    return {
        "id": item.id,
        "level1_id": item.level1_id,
        "level2_id": item.level2_id,
        "level3_id": item.level3_id,
        "service_code": item.service_code,
        "unit": item.unit,
        "unit_price": str(item.unit_price),
        "quantity": str(item.quantity),
        "amount": str(item.amount),
        "remark": item.remark,
        "service_time_start": item.service_time_start,
        "service_time_end": item.service_time_end,
    }


@router.put("/{task_id}/services/{item_id}")
async def update_task_service(
    task_id: str,
    item_id: str,
    payload: TaskServiceLineCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    item = db.query(TaskServiceItem).filter(TaskServiceItem.id == item_id, TaskServiceItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="服务不存在")
    customer = db.query(Customer).filter(Customer.id == task.customer_id).first()
    accepted_ids = {svc.id for svc in getattr(customer, "accepted_service_level1", [])} if customer else set()
    if accepted_ids and payload.level1_id not in accepted_ids:
        raise HTTPException(status_code=400, detail="选择的一级服务不在客户可接受范围")
    code = db.query(InvoiceServiceCode).filter(InvoiceServiceCode.code == payload.service_code, InvoiceServiceCode.is_active == True).first()
    if not code:
        raise HTTPException(status_code=400, detail="服务编码不存在或未启用")
    if code.price is None and payload.unit_price_override is None:
        raise HTTPException(status_code=400, detail="服务编码未设置单价，请先在服务编码中设置单价或填写覆盖单价")
    unit_price = Decimal(str(code.price)) if code.price is not None else Decimal("0")
    if payload.unit_price_override is not None:
        unit_price = Decimal(str(payload.unit_price_override))
    quantity = Decimal(str(payload.duration_hours))
    amount = (unit_price * quantity).quantize(Decimal("0.01"))
    item.level1_id = payload.level1_id
    item.level2_id = payload.level2_id
    item.level3_id = payload.level3_id
    item.service_code = payload.service_code
    item.unit = str(code.unit) if code.unit else None
    item.unit_price = unit_price
    item.quantity = quantity
    item.amount = amount
    item.remark = payload.remark
    item.service_time_start = payload.service_time_start
    item.service_time_end = payload.service_time_end
    db.commit()
    db.refresh(item)
    try:
        recalc_customer_weekly_served_hours(db, task.customer_id)
    except Exception as e:
        logger.error(f"Error recalculating weekly served hours: {e}", exc_info=True)
    return {
        "id": item.id,
        "level1_id": item.level1_id,
        "level2_id": item.level2_id,
        "level3_id": item.level3_id,
        "service_code": item.service_code,
        "unit": item.unit,
        "unit_price": str(item.unit_price),
        "quantity": str(item.quantity),
        "amount": str(item.amount),
        "remark": item.remark,
        "service_time_start": item.service_time_start,
        "service_time_end": item.service_time_end,
    }


@router.delete("/{task_id}/services/{item_id}")
async def delete_task_service(
    task_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    item = db.query(TaskServiceItem).filter(TaskServiceItem.id == item_id, TaskServiceItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="服务不存在")
    db.delete(item)
    db.commit()
    try:
        recalc_customer_weekly_served_hours(db, task.customer_id)
    except Exception as e:
        logger.error(f"Error recalculating weekly served hours for customer {task.customer_id}: {e}", exc_info=True)
    return {"ok": True}


@router.post("/{task_id}/approve", response_model=TaskResponse)
async def approve_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """审核通过任务"""
    task = db.query(Task).options(joinedload(Task.customer)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != TaskStatusEnum.completed:
        raise HTTPException(status_code=400, detail="只能审核已完成的任务")
    
    old_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    # 审核通过：清空拒绝原因（如果存在），将状态改为 approved
    task.reject_reason = None
    task.status = TaskStatusEnum.approved
    db.commit()
    db.refresh(task)
    _notify_employee_task_status_changed(
        db,
        getattr(task, "assigned_employee_id", None),
        str(task.id),
        old_status,
        "approved",
    )
    try:
        recalc_customer_weekly_served_hours(db, task.customer_id)
    except Exception as e:
        logger.error(f"Error recalculating weekly served hours for customer {task.customer_id} in approve_task: {e}", exc_info=True)
    return task


@router.post("/{task_id}/reject", response_model=TaskResponse)
async def reject_task(
    task_id: str,
    reject_reason: str = Query(..., description="拒绝原因"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """审核拒绝任务"""
    
    task = db.query(Task).options(joinedload(Task.customer)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 允许审核已完成、已拒绝或已通过的任务（支持重新提交后再次审核）
    if task.status not in (TaskStatusEnum.completed, TaskStatusEnum.rejected, TaskStatusEnum.approved):
        raise HTTPException(status_code=400, detail="只能审核已完成、已拒绝或已通过的任务")
    
    old_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    task.status = TaskStatusEnum.rejected
    if reject_reason:
        task.reject_reason = reject_reason
    db.commit()
    db.refresh(task)
    _notify_employee_task_status_changed(
        db,
        getattr(task, "assigned_employee_id", None),
        str(task.id),
        old_status,
        "rejected",
    )
    try:
        recalc_customer_weekly_served_hours(db, task.customer_id)
    except Exception as e:
        logger.error(f"Error recalculating weekly served hours for customer {task.customer_id} in reject_task: {e}", exc_info=True)
    return task


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    cancel_reason: str = Query(..., description="取消原因"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """取消任务"""
    
    task = db.query(Task).options(joinedload(Task.customer)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 只允许取消待领取或已分配的任务
    if task.status not in (TaskStatusEnum.pending, TaskStatusEnum.in_progress):
        raise HTTPException(status_code=400, detail="只能取消待领取或进行中的任务")
    
    old_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    # 如果任务已分配给员工，创建取消通知
    if task.assigned_employee_id:
        from shared.models import TaskCancellationNotification
        notification = TaskCancellationNotification(
            task_id=task_id,
            employee_id=task.assigned_employee_id,
            cancel_reason=cancel_reason,
            is_confirmed=False
        )
        db.add(notification)
    
    task.status = TaskStatusEnum.cancelled
    task.reject_reason = cancel_reason
    db.commit()
    db.refresh(task)
    _notify_employee_task_status_changed(
        db,
        getattr(task, "assigned_employee_id", None),
        str(task.id),
        old_status,
        "cancelled",
    )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除任务"""
    try:
        _delete_task_internal(db, task_id)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除任务失败: task_id={task_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="数据库操作失败")

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_by_query(
    task_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    try:
        _delete_task_internal(db, task_id)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除任务失败: task_id={task_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="数据库操作失败")


@router.post("/{task_id}/delete")
async def delete_task_by_post(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    try:
        _delete_task_internal(db, task_id)
        db.commit()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除任务失败: task_id={task_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="数据库操作失败")


@router.get("/{task_id}/location-tracks", response_model=List[LocationTrackResponse])
async def get_task_location_tracks(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取任务轨迹（后台管理）"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        tracks = db.query(TaskLocationTrack).filter(
            TaskLocationTrack.task_id == task_id
        ).order_by(TaskLocationTrack.recorded_at.asc()).all()
        
        # 如果没有轨迹数据，返回空列表而不是错误
        return tracks
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        error_detail = f"获取任务轨迹失败: {str(e)}"
        logger.error(error_detail, exc_info=True)
        # 对于数据库错误，返回更友好的错误消息
        raise HTTPException(
            status_code=500, 
            detail="加载轨迹数据时发生错误，请稍后重试"
        )
