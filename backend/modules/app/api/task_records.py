from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
import json

from core.database import get_db
from shared.models import Task, TaskRecord, TaskRecordTemplate, Employee
from ..dependencies import get_current_employee


router = APIRouter(prefix="/api/app", tags=["App-任务记录"])


class TaskRecordUpsert(BaseModel):
    template_id: Optional[str] = None
    record_data: Optional[dict] = None


def _parse_json(raw):
    if not raw:
        return None
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return None


def _serialize_template(t: TaskRecordTemplate) -> dict[str, Any]:
    return {
        "id": t.id,
        "title": t.title,
        "title_i18n": t.title_i18n,
        "description": t.description,
        "description_i18n": t.description_i18n,
        "schema_json": t.schema_json,
        "style_json": t.style_json,
        "is_active": bool(t.is_active),
    }


@router.get("/tasks/{task_id}/task-record/template")
async def get_task_record_template(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看该任务")

    chosen_id = getattr(task, "task_record_template_id", None)
    template = None
    if chosen_id:
        template = db.query(TaskRecordTemplate).filter(
            TaskRecordTemplate.id == chosen_id, TaskRecordTemplate.is_active == True
        ).first()
    if not template:
        template = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.is_active == True).first()
    if not template:
        return None
    return _serialize_template(template)


@router.get("/tasks/{task_id}/task-record")
async def get_task_record(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看该任务")

    record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).order_by(TaskRecord.created_at.desc()).first()
    if not record:
        return None
    return {
        "id": record.id,
        "task_id": record.task_id,
        "template_id": record.template_id,
        "record_data": _parse_json(record.record_data),
        "created_at": record.created_at.isoformat() if getattr(record, "created_at", None) else None,
        "updated_at": record.updated_at.isoformat() if getattr(record, "updated_at", None) else None,
    }


@router.post("/tasks/{task_id}/task-record")
async def upsert_task_record(
    task_id: str,
    body: TaskRecordUpsert = Body(...),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权提交该任务记录")

    template_id = body.template_id or getattr(task, "task_record_template_id", None)
    template = None
    if template_id:
        template = db.query(TaskRecordTemplate).filter(
            TaskRecordTemplate.id == template_id, TaskRecordTemplate.is_active == True
        ).first()
    if not template:
        template = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.is_active == True).first()
    resolved_template_id = template.id if template else None

    payload_json = json.dumps(body.record_data, ensure_ascii=False) if body.record_data else None
    record = db.query(TaskRecord).filter(TaskRecord.task_id == task_id).first()
    if record:
        record.template_id = resolved_template_id
        record.record_data = payload_json
    else:
        record = TaskRecord(
            task_id=task_id,
            customer_id=task.customer_id,
            employee_id=current_employee.id,
            template_id=resolved_template_id,
            record_data=payload_json,
        )
        db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "template_id": record.template_id,
        "record_data": _parse_json(record.record_data),
        "message": "任务记录已提交",
    }
