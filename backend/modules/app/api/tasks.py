from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from fastapi.responses import Response
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload
import logging

logger = logging.getLogger(__name__)
from typing import List, Optional, Any
from core.database import get_db
from shared.models import (
    Task,
    Customer,
    TaskStatus as TaskStatusEnum,
    Employee,
    User,
    BusinessUnread,
    TaskPhoto,
    TaskLocationTrack,
    Questionnaire,
    InvoiceServiceLevel1,
    InvoiceServiceLevel2,
    InvoiceServiceLevel3,
    InvoiceServiceCode,
    TaskServiceItem,
)
from shared.models.update_notification import touch_business_unread
from ..schemas.task import (
    TaskResponse,
    TaskCreate,
    TaskUpdate,
    TaskStatus,
    LocationTrackCreate,
    LocationTrackResponse,
    TaskServiceItemResponse,
    TaskRemarkUpdateRequest,
)
from ..dependencies import get_current_employee
from datetime import datetime, timedelta, time as dt_time
import json
import base64
import re
import mimetypes
from decimal import Decimal
from core.config import settings

router = APIRouter(prefix="/api/app/tasks", tags=["任务"])


def _week_bounds_local(reference: datetime | None = None) -> tuple[datetime, datetime]:
    now = reference or datetime.now()
    today = now.date()
    week_start_date = today - timedelta(days=today.weekday())
    start = datetime.combine(week_start_date, dt_time(0, 0))
    end = start + timedelta(days=7)
    
    # 调试日志
    print(f"Weekly bounds (App): reference={now}, start={start}, end={end}")
    
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


def _recalc_customer_weekly_served_hours(db: Session, customer_id: str) -> None:
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
            try:
                val = t.service_duration_hours
                if val:
                    total_hours += float(str(val).replace(",", "."))
            except Exception:
                pass

    # 调试日志
    logger.info(f"Recalc hours for customer {customer_id}: total={total_hours} (tasks_count={len(tasks)})")

    # 更新客户的周累计时长
    db.query(Customer).filter(Customer.id == customer_id).update(
        {"weekly_served_hours": total_hours}
    )
    db.commit()


def _ensure_employee_can_service(employee: Employee):
    status_value = (getattr(employee, "account_status", None) or "normal").strip().lower()
    if status_value != "normal":
        raise HTTPException(status_code=403, detail="账号已被禁用，无法进行服务操作")


def _notify_admin_task_status_changed(
    db: Session,
    task_id: str,
    old_status: str | None,
    new_status: str | None,
):
    try:
        admin_users = db.query(User).filter(or_(User.is_active == True, User.is_active.is_(None))).all()
        payload = json.dumps(
            {"from": old_status, "to": new_status},
            ensure_ascii=False,
        )
        for u in admin_users:
            touch_business_unread(
                db,
                business_code="task",
                receiver_user_id=str(u.id),
                data_id=str(task_id),
            )
        db.commit()
    except Exception:
        db.rollback()


def _parse_data_url(data_url: str):
    match = re.match(r"^data:(.+?);base64,(.+)$", data_url, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None, None
    mime_type = match.group(1)
    raw = match.group(2).strip()
    raw = re.sub(r"\s+", "", raw)
    try:
        data = base64.b64decode(raw)
    except Exception:
        return None, None
    return mime_type, data


def _try_decode_base64(value: str):
    raw = (value or "").strip()
    if not raw:
        return None
    raw = re.sub(r"\s+", "", raw)
    if len(raw) < 64:
        return None
    if not re.fullmatch(r"[A-Za-z0-9+/=]+", raw):
        return None
    try:
        return base64.b64decode(raw)
    except Exception:
        return None


def _looks_like_base64(value: str) -> bool:
    raw = (value or "").strip()
    if not raw:
        return False
    raw = re.sub(r"\s+", "", raw)
    if len(raw) < 64:
        return False
    return re.fullmatch(r"[A-Za-z0-9+/=]+", raw) is not None


def _guess_mime_from_path(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def _parse_iso_datetime(value: Any):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _build_task_response(task: Task, db: Session | None = None):
    data = TaskResponse.from_orm(task).dict()
    data["assigned_employee_name"] = task.assigned_employee.name if task.assigned_employee else None
    
    # Fallback to old flat fields if no service_items and no service_plans
    if not data.get("service_items") and not data.get("service_plans"):
        raw_code = getattr(task, "service_code", None)
        raw_qty = getattr(task, "service_duration_hours", None) or "1"
        raw_price = getattr(task, "unit_price", None)
        if raw_code:
            try:
                qty = Decimal(str(raw_qty))
            except Exception:
                qty = Decimal("1")
            try:
                price = Decimal(str(raw_price)) if raw_price is not None else Decimal("0")
            except Exception:
                price = Decimal("0")
            amount = (price * qty).quantize(Decimal("0.01"))
            # Make a fake item for compatibility
            fake_item = {
                "id": "fake-1",
                "level1_id": None,
                "level2_id": None,
                "level3_id": None,
                "service_code": str(raw_code),
                "unit": "Hour",
                "unit_price": price,
                "quantity": qty,
                "amount": amount,
                "remark": None,
                "service_time_start": task.service_start_time.strftime("%H:%M") if task.service_start_time else None,
                "service_time_end": task.service_end_time.strftime("%H:%M") if task.service_end_time else None,
            }
            data["service_items"] = [fake_item]
            
            # Also set service_plans for compatibility
            data["service_plans"] = [
                {
                    "line_no": 1,
                    "level1_id": None,
                    "level2_id": None,
                    "level3_id": None,
                    "service_code": str(raw_code),
                    "unit": "Hour",
                    "unit_price": str(price),
                    "quantity": str(qty),
                    "amount": str(amount),
                    "remark": None,
                    "service_time_start": task.service_start_time.strftime("%H:%M") if task.service_start_time else None,
                    "service_time_end": task.service_end_time.strftime("%H:%M") if task.service_end_time else None,
                }
            ]
            
    # Fill empty time fields in service_items with task time
    if data.get("service_items"):
        if db:
            level1_ids = {i.get("level1_id") for i in data["service_items"] if i.get("level1_id")}
            level2_ids = {i.get("level2_id") for i in data["service_items"] if i.get("level2_id")}
            level3_ids = {i.get("level3_id") for i in data["service_items"] if i.get("level3_id")}
            level1_map = {r.id: r.name for r in db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.id.in_(list(level1_ids))).all()} if level1_ids else {}
            level2_map = {r.id: r.name for r in db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.id.in_(list(level2_ids))).all()} if level2_ids else {}
            level3_map = {r.id: r.name for r in db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.id.in_(list(level3_ids))).all()} if level3_ids else {}
        for item in data["service_items"]:
            if not item.get("service_time_start") and task.service_start_time:
                item["service_time_start"] = task.service_start_time.strftime("%H:%M")
            if not item.get("service_time_end") and task.service_end_time:
                item["service_time_end"] = task.service_end_time.strftime("%H:%M")
            if db:
                if item.get("level1_id"):
                    item["level1_name"] = level1_map.get(item.get("level1_id"))
                if item.get("level2_id"):
                    item["level2_name"] = level2_map.get(item.get("level2_id"))
                if item.get("level3_id"):
                    item["level3_name"] = level3_map.get(item.get("level3_id"))
                
    return data


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取任务列表"""
    from sqlalchemy.orm import joinedload
    unread_task_ids = {
        (r.data_id or "")
        for r in db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_employee.id),
            BusinessUnread.business_code == "task",
            BusinessUnread.is_unread == 1,
        )
        .all()
    }
    query = db.query(Task).options(joinedload(Task.service_items)).filter(Task.assigned_employee_id == current_employee.id)
    if status:
        query = query.filter(Task.status == status.value)
    tasks = query.all()
    result = []
    for task in tasks:
        data = _build_task_response(task)
        data["has_update"] = str(task.id) in unread_task_ids
        result.append(data)
    return result


@router.get("/{task_id}/questionnaires", response_model=List[dict])
async def list_task_questionnaires(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """获取任务关联的问卷列表及其填写状态"""
    from sqlalchemy.orm import joinedload
    from shared.models.questionnaire import TaskQuestionnaire, QuestionnaireResponse as QRModel
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看此任务")
        
    # 获取关联的问卷
    tq_list = db.query(TaskQuestionnaire).filter(TaskQuestionnaire.task_id == task_id).order_by(TaskQuestionnaire.order_index).all()
    
    # 如果没有关联问卷，尝试获取旧版的单个问卷
    if not tq_list:
        chosen_id = getattr(task, "questionnaire_id", None)
        if chosen_id:
            chosen = db.query(Questionnaire).filter(Questionnaire.id == chosen_id, Questionnaire.is_active == True).first()
            if chosen:
                # 检查是否已填写
                has_filled = db.query(QRModel).filter(QRModel.task_id == task_id, QRModel.questionnaire_id == chosen_id).first() is not None
                return [{
                    "id": chosen.id,
                    "title": chosen.title,
                    "is_required": True,
                    "is_filled": has_filled or (task.questionnaire_data is not None)
                }]
        
        # 仍然没有，按客户类型匹配一个默认的
        customer = db.query(Customer).filter(Customer.id == task.customer_id).first()
        customer_type = customer.customer_type if customer else None
        q_query = db.query(Questionnaire).filter(Questionnaire.is_active == True)
        if customer_type:
            from sqlalchemy import or_
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
            has_filled = db.query(QRModel).filter(QRModel.task_id == task_id, QRModel.questionnaire_id == preferred.id).first() is not None
            return [{
                "id": preferred.id,
                "title": preferred.title,
                "is_required": True,
                "is_filled": has_filled or (task.questionnaire_data is not None)
            }]
        return []

    # 获取已填写的问卷ID
    filled_qids = {r.questionnaire_id for r in db.query(QRModel).filter(QRModel.task_id == task_id).all()}
    
    result = []
    for tq in tq_list:
        q = db.query(Questionnaire).filter(Questionnaire.id == tq.questionnaire_id).first()
        if q:
            result.append({
                "id": q.id,
                "title": q.title,
                "is_required": tq.is_required,
                "is_filled": q.id in filled_qids
            })
    return result

@router.get("/{task_id}/questionnaires/{questionnaire_id}", response_model=dict)
async def get_task_questionnaire_template(
    task_id: str,
    questionnaire_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """获取指定问卷的模板"""
    from ..schemas.questionnaire import QuestionnaireResponse
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看此任务")
        
    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="问卷不存在")
        
    return QuestionnaireResponse.model_validate(q).model_dump()

@router.post("/{task_id}/questionnaires/{questionnaire_id}/responses")
async def submit_task_questionnaire_response(
    task_id: str,
    questionnaire_id: str,
    answers: dict = Body(...),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """提交问卷回答"""
    from shared.models.questionnaire import QuestionnaireResponse as QRModel
    from shared.models.questionnaire import TaskQuestionnaire as TQModel
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
        
    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="问卷不存在")

    tq_list = db.query(TQModel).filter(TQModel.task_id == task_id).all()
    if tq_list:
        allowed = {tq.questionnaire_id for tq in tq_list}
        if questionnaire_id not in allowed:
            raise HTTPException(status_code=400, detail="该任务未关联此问卷")
    elif getattr(task, "questionnaire_id", None) and task.questionnaire_id != questionnaire_id:
        raise HTTPException(status_code=400, detail="该任务指定的问卷与提交问卷不一致")
        
    existing = db.query(QRModel).filter(
        QRModel.questionnaire_id == questionnaire_id,
        QRModel.task_id == task_id,
        QRModel.customer_id == task.customer_id,
        QRModel.employee_id == current_employee.id,
    ).first()
    now = datetime.utcnow()
    if existing:
        db.query(QRModel).filter(QRModel.id == existing.id).update(
            {"answers": answers, "submitted_at": now}
        )
    else:
        response = QRModel(
            task_id=task_id,
            questionnaire_id=questionnaire_id,
            customer_id=task.customer_id,
            employee_id=current_employee.id,
            answers=answers,
            submitted_at=now,
        )
        db.add(response)
    
    if tq_list:
        db.query(TQModel).filter(
            TQModel.task_id == task_id,
            TQModel.questionnaire_id == questionnaire_id,
        ).update({"is_filled": True})
    else:
        if getattr(task, "questionnaire_id", None) == questionnaire_id:
            task.questionnaire_data = answers
    
    db.commit()
    return {"status": "success"}

@router.get("/{task_id}/questionnaire", response_model=dict)
async def get_task_questionnaire(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """按任务获取对应客户类型的 Progress Notes 问卷模板"""
    from ..schemas.questionnaire import QuestionnaireResponse, QuestionResponse

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看此任务")
    chosen_id = getattr(task, "questionnaire_id", None)
    if chosen_id:
        chosen = (
            db.query(Questionnaire)
            .filter(Questionnaire.id == chosen_id, Questionnaire.is_active == True)
            .first()
        )
        if chosen:
            result = QuestionnaireResponse.model_validate(chosen)
            return result.model_dump()
    customer = db.query(Customer).filter(Customer.id == task.customer_id).first()
    customer_type = customer.customer_type if customer else None
    q = db.query(Questionnaire).filter(Questionnaire.is_active == True)
    if customer_type:
        from sqlalchemy import or_
        match_types = [customer_type]
        if customer_type == "助残":
            match_types.append("NDIS")
        q = q.filter(or_(
            Questionnaire.customer_type.in_(match_types),
            Questionnaire.customer_type == None
        ))
    questionnaires = q.all()
    if not questionnaires:
        q_any = db.query(Questionnaire).filter(Questionnaire.is_active == True).first()
        if q_any:
            preferred = q_any
        else:
            raise HTTPException(status_code=404, detail="暂无可用的问卷模板")
    else:
        match_types = [customer_type, "NDIS"] if customer_type == "助残" else [customer_type]
        preferred = next(
            (q for q in questionnaires if q.customer_type in match_types),
            questionnaires[0]
        )

    result = QuestionnaireResponse.model_validate(preferred)
    return result.model_dump()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取任务详情"""
    from sqlalchemy.orm import joinedload
    task = db.query(Task).options(joinedload(Task.service_items)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看此任务")
    has_update = (
        db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_employee.id),
            BusinessUnread.business_code == "task",
            BusinessUnread.data_id == str(task_id),
            BusinessUnread.is_unread == 1,
        )
        .first()
        is not None
    )
    data = _build_task_response(task, db)
    data["has_update"] = has_update
    return data

@router.get("/{task_id}/services", response_model=List[TaskServiceItemResponse])
async def list_task_services(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看此任务")
    items = (
        db.query(TaskServiceItem)
        .filter(TaskServiceItem.task_id == task_id)
        .order_by(TaskServiceItem.created_at.asc())
        .all()
    )
    level1_ids = {i.level1_id for i in items if i.level1_id}
    level2_ids = {i.level2_id for i in items if i.level2_id}
    level3_ids = {i.level3_id for i in items if i.level3_id}
    level1_map = {r.id: r.name for r in db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.id.in_(list(level1_ids))).all()} if level1_ids else {}
    level2_map = {r.id: r.name for r in db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.id.in_(list(level2_ids))).all()} if level2_ids else {}
    level3_map = {r.id: r.name for r in db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.id.in_(list(level3_ids))).all()} if level3_ids else {}
    result = []
    for i in items:
        result.append({
            "id": i.id,
            "level1_id": i.level1_id,
            "level2_id": i.level2_id,
            "level3_id": i.level3_id,
            "level1_name": level1_map.get(i.level1_id),
            "level2_name": level2_map.get(i.level2_id),
            "level3_name": level3_map.get(i.level3_id),
            "service_code": i.service_code,
            "unit": i.unit,
            "unit_price": i.unit_price,
            "quantity": i.quantity,
            "amount": i.amount,
            "remark": i.remark,
            "service_time_start": i.service_time_start,
            "service_time_end": i.service_time_end,
        })
    return result


@router.get("/{task_id}/services/{item_id}", response_model=TaskServiceItemResponse)
async def get_task_service(
    task_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看此任务")
    item = db.query(TaskServiceItem).filter(TaskServiceItem.id == item_id, TaskServiceItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="服务不存在")
    level1_name = None
    level2_name = None
    level3_name = None
    if item.level1_id:
        row = db.query(InvoiceServiceLevel1).filter(InvoiceServiceLevel1.id == item.level1_id).first()
        level1_name = row.name if row else None
    if item.level2_id:
        row = db.query(InvoiceServiceLevel2).filter(InvoiceServiceLevel2.id == item.level2_id).first()
        level2_name = row.name if row else None
    if item.level3_id:
        row = db.query(InvoiceServiceLevel3).filter(InvoiceServiceLevel3.id == item.level3_id).first()
        level3_name = row.name if row else None
    return {
        "id": item.id,
        "level1_id": item.level1_id,
        "level2_id": item.level2_id,
        "level3_id": item.level3_id,
        "level1_name": level1_name,
        "level2_name": level2_name,
        "level3_name": level3_name,
        "service_code": item.service_code,
        "unit": item.unit,
        "unit_price": item.unit_price,
        "quantity": item.quantity,
        "amount": item.amount,
        "remark": item.remark,
        "service_time_start": item.service_time_start,
        "service_time_end": item.service_time_end,
    }


@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """领取任务"""
    _ensure_employee_can_service(current_employee)
    from sqlalchemy.orm import joinedload
    task = db.query(Task).options(joinedload(Task.service_items)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != TaskStatusEnum.pending:
        raise HTTPException(status_code=400, detail="任务已被领取或已完成")

    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="只能领取指派给自己的任务")
    
    old_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    task.status = TaskStatusEnum.in_progress
    task.assigned_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    _notify_admin_task_status_changed(db, task.id, old_status, "in_progress")
    return _build_task_response(task, db)

@router.put("/{task_id}/remark", response_model=TaskResponse)
async def update_task_remark(
    task_id: str,
    body: TaskRemarkUpdateRequest,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    from sqlalchemy.orm import joinedload
    task = db.query(Task).options(joinedload(Task.service_items)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    task.employee_remark = body.employee_remark
    db.commit()
    db.refresh(task)
    return _build_task_response(task, db)


@router.put("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    payload: Any = Body(...),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """更新任务状态"""
    from sqlalchemy.orm import joinedload
    task = db.query(Task).options(joinedload(Task.service_items)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")

    raw_status = None
    employee_remark = None
    if isinstance(payload, dict):
        raw_status = payload.get("status")
        employee_remark = payload.get("employee_remark")
        if employee_remark is None:
            employee_remark = payload.get("remark")
        if employee_remark is None:
            employee_remark = payload.get("employee_note")
    else:
        raw_status = payload

    try:
        status_value = raw_status if isinstance(raw_status, TaskStatus) else TaskStatus(str(raw_status))
    except Exception:
        raise HTTPException(status_code=422, detail="status 无效")

    if status_value == TaskStatus.completed:
        _ensure_employee_can_service(current_employee)
        
        # 检查必填问卷是否已填写
        from shared.models.questionnaire import TaskQuestionnaire, QuestionnaireResponse as QRModel
        tq_any = db.query(TaskQuestionnaire).filter(TaskQuestionnaire.task_id == task_id).first()
        tq_required = db.query(TaskQuestionnaire).filter(
            TaskQuestionnaire.task_id == task_id,
            TaskQuestionnaire.is_required == True,
        ).all()
        if tq_required:
            filled_qids = {r.questionnaire_id for r in db.query(QRModel).filter(QRModel.task_id == task_id).all()}
            missing = [tq.questionnaire_id for tq in tq_required if tq.questionnaire_id not in filled_qids]
            if missing:
                raise HTTPException(status_code=400, detail="请先填写所有必填问卷")
        elif (not tq_any) and task.questionnaire_id:
            # 旧版兼容：如果有关联 questionnaire_id，也检查是否已填写（如果是 legacy 模式）
            has_filled = db.query(QRModel).filter(QRModel.task_id == task_id, QRModel.questionnaire_id == task.questionnaire_id).first() is not None
            if not has_filled and not task.questionnaire_data:
                raise HTTPException(status_code=400, detail="请先填写问卷")

    old_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    task.status = status_value.value
    if employee_remark is not None:
        task.employee_remark = employee_remark
    if status_value == TaskStatus.completed:
        task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    new_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    if old_status != new_status:
        _notify_admin_task_status_changed(db, task.id, old_status, new_status)
    if (
        old_status != new_status
        and (old_status in ("completed", "approved") or new_status in ("completed", "approved"))
    ):
        try:
            _recalc_customer_weekly_served_hours(db, task.customer_id)
        except Exception:
            pass
    return _build_task_response(task, db)


@router.put("/{task_id}/questionnaire", response_model=TaskResponse)
async def update_task_questionnaire(
    task_id: str,
    questionnaire_data: dict,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """更新任务问卷数据"""
    from sqlalchemy.orm import joinedload
    task = db.query(Task).options(joinedload(Task.service_items)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    task.questionnaire_data = questionnaire_data
    db.commit()
    db.refresh(task)
    return _build_task_response(task, db)


@router.put("/{task_id}/signature", response_model=TaskResponse)
async def update_task_signature(
    task_id: str,
    signature_data: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """更新任务签名"""
    from sqlalchemy.orm import joinedload
    task = db.query(Task).options(joinedload(Task.service_items)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    mime_type = None
    blob = None
    if signature_data.startswith("data:image"):
        mime_type, blob = _parse_data_url(signature_data)
    elif signature_data:
        mime_type = _guess_mime_from_path(signature_data)

    if blob:
        task.signature_blob = blob
        task.signature_mime = mime_type
        task.signature_image_url = f"/api/app/tasks/{task_id}/signature/image"
    else:
        task.signature_image_url = signature_data
    db.commit()
    db.refresh(task)
    return _build_task_response(task, db)


@router.get("/{task_id}/signature/image")
async def get_task_signature_image(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取任务签名图片"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.signature_blob:
        raise HTTPException(status_code=404, detail="签名不存在")
    return Response(content=task.signature_blob, media_type=task.signature_mime or "image/png")


@router.put("/{task_id}/photos", response_model=TaskResponse)
async def update_task_photos(
    task_id: str,
    payload: Any = Body(...),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """更新任务照片"""
    from sqlalchemy.orm import joinedload
    task = db.query(Task).options(joinedload(Task.service_items)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")

    photo_items = payload
    if isinstance(payload, dict):
        photo_items = payload.get("photo_items") or payload.get("photo_urls") or []
    if not isinstance(photo_items, list):
        raise HTTPException(status_code=400, detail="照片数据格式错误")

    db.query(TaskPhoto).filter(TaskPhoto.task_id == task_id).delete()
    db.flush()
    new_urls = []
    for item in photo_items:
        mime_type = None
        blob = None
        photo_value = item
        shot_at = None
        latitude = None
        longitude = None
        address = None

        if isinstance(item, dict):
            mime_type = item.get("mime_type") or item.get("content_type") or item.get("type")
            photo_value = (
                item.get("data_url")
                or item.get("photo_url")
                or item.get("url")
                or item.get("base64")
                or item.get("data")
            )
            shot_at = _parse_iso_datetime(item.get("shot_at"))
            latitude = item.get("latitude")
            longitude = item.get("longitude")
            address = item.get("address")

        if not photo_value:
            continue
        if isinstance(photo_value, str) and photo_value.startswith("data:"):
            mime_type, blob = _parse_data_url(photo_value)
            if not blob:
                raise HTTPException(status_code=400, detail="照片数据无法解析")
        elif isinstance(photo_value, str):
            blob = _try_decode_base64(photo_value)
            if blob is None and _looks_like_base64(photo_value):
                raise HTTPException(status_code=400, detail="照片数据无法解析")
            if blob and not mime_type:
                mime_type = "image/jpeg"
        if blob:
            if settings.max_upload_size and len(blob) > int(settings.max_upload_size):
                raise HTTPException(status_code=413, detail="照片过大，请压缩后再上传")
            task_photo = TaskPhoto(
                task_id=task_id,
                photo_blob=blob,
                photo_mime=mime_type or "image/jpeg",
                shot_at=shot_at,
                latitude=latitude,
                longitude=longitude,
                address=address
            )
            db.add(task_photo)
            db.flush()
            new_urls.append(f"/api/app/tasks/{task_id}/photos/{task_photo.id}")
        else:
            new_urls.append(photo_value)

    task.photo_urls = new_urls
    db.commit()
    db.refresh(task)
    return _build_task_response(task, db)


@router.post("/{task_id}/photos", response_model=TaskResponse)
async def upload_task_photos(
    task_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    from sqlalchemy.orm import joinedload
    task = db.query(Task).options(joinedload(Task.service_items)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")

    existing_urls = task.photo_urls or []
    if not isinstance(existing_urls, list):
        existing_urls = []

    new_urls: list[str] = []
    for f in files:
        content = await f.read()
        if settings.max_upload_size and len(content) > int(settings.max_upload_size):
            raise HTTPException(status_code=413, detail="照片过大，请压缩后再上传")

        mime_type = f.content_type or _guess_mime_from_path(f.filename or "")
        if not mime_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="仅支持上传图片文件")

        task_photo = TaskPhoto(
            task_id=task_id,
            photo_blob=content,
            photo_mime=mime_type,
        )
        db.add(task_photo)
        db.flush()
        new_urls.append(f"/api/app/tasks/{task_id}/photos/{task_photo.id}")

    task.photo_urls = existing_urls + new_urls
    db.commit()
    db.refresh(task)
    return _build_task_response(task, db)


@router.get("/{task_id}/photos/{photo_id}")
async def get_task_photo(
    task_id: str,
    photo_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取任务照片"""
    photo = db.query(TaskPhoto).filter(
        TaskPhoto.id == photo_id,
        TaskPhoto.task_id == task_id
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    return Response(content=photo.photo_blob, media_type=photo.photo_mime or "image/jpeg")


@router.post("/{task_id}/location-tracks", response_model=List[LocationTrackResponse])
async def create_location_tracks(
    task_id: str,
    tracks: List[LocationTrackCreate],
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """批量上传任务轨迹点"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    if task.status != TaskStatusEnum.in_progress:
        raise HTTPException(status_code=400, detail="只能为进行中的任务记录轨迹")
    
    track_objects = []
    for track_data in tracks:
        track = TaskLocationTrack(
            task_id=task_id,
            latitude=track_data.latitude,
            longitude=track_data.longitude,
            address=track_data.address,
            accuracy=track_data.accuracy,
            speed=track_data.speed,
            altitude=track_data.altitude,
            recorded_at=track_data.recorded_at or datetime.utcnow(),
        )
        track_objects.append(track)
    
    db.add_all(track_objects)
    db.commit()
    
    for track in track_objects:
        db.refresh(track)
    
    return track_objects


@router.get("/{task_id}/location-tracks", response_model=List[LocationTrackResponse])
async def get_location_tracks(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取任务轨迹"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.assigned_employee_id != current_employee.id:
            raise HTTPException(status_code=403, detail="无权查看此任务")
        
        tracks = db.query(TaskLocationTrack).filter(
            TaskLocationTrack.task_id == task_id
        ).order_by(TaskLocationTrack.recorded_at.asc()).all()
        
        return tracks
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        error_detail = f"获取轨迹失败: {str(e)}"
        logger.error(error_detail, exc_info=True)
        # 对于数据库错误，返回更友好的错误消息
        raise HTTPException(
            status_code=500, 
            detail="加载轨迹数据时发生错误，请稍后重试"
        )
