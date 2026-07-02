from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any
import json

from core.database import get_db
from shared.models import Task, TaskRecord, TaskRecordTemplate, Customer, Employee, Questionnaire
from ..dependencies import get_current_user


router = APIRouter(prefix="/api/houtai/task-records", tags=["管理-任务记录"])


def _parse_json(raw):
    if not raw:
        return None
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return None


@router.get("")
async def get_task_record(
    task_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).order_by(TaskRecord.created_at.desc()).first()
    template = None
    if record and record.template_id:
        template = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.id == record.template_id).first()
    if not template:
        chosen_id = getattr(task, "task_record_template_id", None)
        if chosen_id:
            template = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.id == chosen_id, TaskRecordTemplate.is_active == True).first()
    if not template:
        template = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.is_active == True).first()

    return {
        "task_id": task_id,
        "template": (
            {
                "id": template.id,
                "title": template.title,
                "title_i18n": template.title_i18n,
                "description": template.description,
                "description_i18n": template.description_i18n,
                "schema_json": template.schema_json,
                "style_json": template.style_json,
            }
            if template
            else None
        ),
        "record": (
            {
                "id": record.id,
                "template_id": record.template_id,
                "record_data": _parse_json(record.record_data),
                "created_at": record.created_at.isoformat() if getattr(record, "created_at", None) else None,
                "updated_at": record.updated_at.isoformat() if getattr(record, "updated_at", None) else None,
            }
            if record
            else None
        ),
    }


@router.get("/submissions")
async def list_task_record_submissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order_desc = str(sort).lower() != "asc"
    base = (
        db.query(
            TaskRecord,
            Task.title.label("task_title"),
            Customer.name.label("customer_name"),
            Employee.name.label("employee_name"),
            Questionnaire.title.label("questionnaire_title"),
            TaskRecordTemplate.title.label("template_title"),
        )
        .join(Task, Task.id == TaskRecord.task_id)
        .join(Customer, Customer.id == Task.customer_id)
        .outerjoin(Employee, Employee.id == TaskRecord.employee_id)
        .outerjoin(Questionnaire, Questionnaire.id == Task.questionnaire_id)
        .outerjoin(TaskRecordTemplate, TaskRecordTemplate.id == TaskRecord.template_id)
    )
    total = base.count()
    q = base.order_by(
        TaskRecord.created_at.desc() if order_desc else TaskRecord.created_at.asc()
    )
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for r, task_title, customer_name, employee_name, questionnaire_title, template_title in rows:
        items.append({
            "id": r.id,
            "template_id": r.template_id,
            "template_title": template_title or "",
            "questionnaire_title": questionnaire_title or "",
            "customer_id": r.customer_id,
            "customer_name": customer_name or "",
            "employee_id": r.employee_id,
            "employee_name": employee_name or "",
            "task_id": r.task_id,
            "task_title": task_title or "",
            "submitted_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
        })
    return {"items": items, "total": total}


@router.get("/submissions/{record_id}")
async def get_task_record_submission(
    record_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    record = db.query(TaskRecord).filter(TaskRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    task = db.query(Task).filter(Task.id == record.task_id).first()
    customer = db.query(Customer).filter(Customer.id == record.customer_id).first()
    employee = db.query(Employee).filter(Employee.id == record.employee_id).first() if record.employee_id else None
    template = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.id == record.template_id).first() if record.template_id else None
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == getattr(task, "questionnaire_id", None)).first() if task and getattr(task, "questionnaire_id", None) else None
    return {
        "id": record.id,
        "template_id": record.template_id,
        "template_title": template.title if template else "",
        "questionnaire_title": questionnaire.title if questionnaire else "",
        "customer_id": record.customer_id,
        "customer_name": customer.name if customer else "",
        "employee_id": record.employee_id,
        "employee_name": employee.name if employee else "",
        "task_id": record.task_id,
        "task_title": task.title if task else "",
        "submitted_at": record.created_at.isoformat() if getattr(record, "created_at", None) else None,
        "record_data": _parse_json(record.record_data),
    }


@router.delete("/submissions/{record_id}")
async def delete_task_record_submission(
    record_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    record = db.query(TaskRecord).filter(TaskRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    db.delete(record)
    db.commit()
    return {"ok": True}
