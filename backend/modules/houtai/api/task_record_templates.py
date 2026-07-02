from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Optional

from core.database import get_db
from shared.models import TaskRecordTemplate
from ..dependencies import get_current_user


router = APIRouter(prefix="/api/houtai/task-record-templates", tags=["管理-任务记录模板"])


class TemplateUpsert(BaseModel):
    title: Optional[str] = ""
    title_i18n: Optional[dict] = None
    description: Optional[str] = None
    description_i18n: Optional[dict] = None
    schema_json: Optional[dict] = None
    style_json: Optional[dict] = None
    is_active: Optional[bool] = True


def _serialize(row: TaskRecordTemplate) -> dict[str, Any]:
    return {
        "id": row.id,
        "title": row.title,
        "title_i18n": row.title_i18n,
        "description": row.description,
        "description_i18n": row.description_i18n,
        "schema_json": row.schema_json,
        "style_json": row.style_json,
        "is_active": bool(row.is_active),
        "created_at": row.created_at.isoformat() if getattr(row, "created_at", None) else None,
        "updated_at": row.updated_at.isoformat() if getattr(row, "updated_at", None) else None,
    }


@router.get("")
async def list_task_record_templates(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = db.query(TaskRecordTemplate).order_by(TaskRecordTemplate.created_at.desc()).all()
    return [_serialize(r) for r in rows]


@router.post("")
async def create_task_record_template(
    body: TemplateUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = TaskRecordTemplate(
        title=(body.title or "").strip(),
        title_i18n=body.title_i18n,
        description=body.description,
        description_i18n=body.description_i18n,
        schema_json=body.schema_json,
        style_json=body.style_json,
        is_active=True if body.is_active is None else bool(body.is_active),
    )
    if not row.title:
        row.title = "Task Record Template"
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.get("/{template_id}")
async def get_task_record_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="模板不存在")
    return _serialize(row)


@router.put("/{template_id}")
async def update_task_record_template(
    template_id: str,
    body: TemplateUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="模板不存在")
    if body.title is not None:
        row.title = (body.title or "").strip()
    if body.title_i18n is not None:
        row.title_i18n = body.title_i18n
    if body.description is not None:
        row.description = body.description
    if body.description_i18n is not None:
        row.description_i18n = body.description_i18n
    if body.schema_json is not None:
        row.schema_json = body.schema_json
    if body.style_json is not None:
        row.style_json = body.style_json
    if body.is_active is not None:
        row.is_active = bool(body.is_active)
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.delete("/{template_id}")
async def delete_task_record_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(TaskRecordTemplate).filter(TaskRecordTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.delete(row)
    db.commit()
    return {"ok": True}
