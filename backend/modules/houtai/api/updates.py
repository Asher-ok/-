from fastapi import APIRouter, Depends
import json
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from core.database import get_db
from shared.models import Qualification, TrainingRecord, Employee, BusinessUnread
from ..dependencies import get_current_user


router = APIRouter(prefix="/api/houtai/updates", tags=["管理-红点"])


class MarkReadBody(BaseModel):
    entity_type: str
    entity_id: str | None = None


def _as_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _training_record_expiry_date(record: TrainingRecord) -> datetime | None:
    if record.certificate_expiry_date:
        return _as_aware_utc(record.certificate_expiry_date)
    if record.category in ["first-aid", "manual-handling"] and record.completed_date:
        base = _as_aware_utc(record.completed_date)
        return base + relativedelta(months=12)
    return None


def _ensure_admin_certificate_expired_notifications(
    db: Session,
    admin_user_id: str,
) -> None:
    now = datetime.now(timezone.utc)
    today = now.date()
    created_any = False

    qualification_rows = (
        db.query(Qualification, Employee)
        .join(Employee, Qualification.employee_id == Employee.id)
        .filter(Qualification.expiry_date.isnot(None))
        .all()
    )
    for qual, employee in qualification_rows:
        expiry = _as_aware_utc(qual.expiry_date)
        if expiry.date() >= today:
            continue
        entity_id = f"qualification:{qual.id}"
        exists = (
            db.query(BusinessUnread)
            .filter(
                BusinessUnread.receiver_user_id == admin_user_id,
                BusinessUnread.business_code == "qualification",
                BusinessUnread.data_id == entity_id,
            )
            .first()
        )
        if exists:
            continue
        db.add(BusinessUnread(
            business_code="qualification",
            data_id=entity_id,
            scope_id=str(employee.id),
            receiver_user_id=admin_user_id,
            trigger_user_id=None,
            is_unread=1,
            triggered_at=now,
        ))
        created_any = True

    record_rows = (
        db.query(TrainingRecord, Employee)
        .join(Employee, TrainingRecord.employee_id == Employee.id)
        .filter(
            TrainingRecord.status == "completed",
            TrainingRecord.completed_date.isnot(None),
        )
        .all()
    )
    for record, employee in record_rows:
        expiry = _training_record_expiry_date(record)
        if not expiry:
            continue
        if expiry.date() >= today:
            continue
        entity_id = f"training_record:{record.id}"
        exists = (
            db.query(BusinessUnread)
            .filter(
                BusinessUnread.receiver_user_id == admin_user_id,
                BusinessUnread.business_code == "qualification",
                BusinessUnread.data_id == entity_id,
            )
            .first()
        )
        if exists:
            continue
        db.add(BusinessUnread(
            business_code="qualification",
            data_id=entity_id,
            scope_id=str(employee.id),
            receiver_user_id=admin_user_id,
            trigger_user_id=None,
            is_unread=1,
            triggered_at=now,
        ))
        created_any = True

    if created_any:
        db.commit()


@router.get("/summary")
async def get_update_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _ensure_admin_certificate_expired_notifications(db, str(current_user.id))
    q = (
        db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_user.id),
            BusinessUnread.is_unread == 1,
        )
    )
    rows = q.all()
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.business_code] = counts.get(r.business_code, 0) + 1
    return {"counts": counts}


@router.post("/mark-read")
async def mark_updates_read(
    body: MarkReadBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_user.id),
            BusinessUnread.business_code == body.entity_type,
            BusinessUnread.is_unread == 1,
        )
    )
    if body.entity_id:
        q = q.filter(BusinessUnread.data_id == body.entity_id)
    q.update({"is_unread": 0})
    db.commit()
    return {"ok": True}
