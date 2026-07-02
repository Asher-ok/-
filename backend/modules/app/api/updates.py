from fastapi import APIRouter, Depends
import json
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from core.database import get_db
from shared.models import Employee, Qualification, TrainingRecord, BusinessUnread
from ..dependencies import get_current_employee


router = APIRouter(prefix="/api/app/updates", tags=["App-红点"])


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


def _ensure_employee_certificate_expired_notifications(
    db: Session,
    employee_id: str,
) -> None:
    now = datetime.now(timezone.utc)
    today = now.date()
    created_any = False

    qualifications = (
        db.query(Qualification)
        .filter(
            Qualification.employee_id == employee_id,
            Qualification.expiry_date.isnot(None),
        )
        .all()
    )
    for qual in qualifications:
        expiry = _as_aware_utc(qual.expiry_date)
        if expiry.date() >= today:
            continue
        entity_id = f"qualification:{qual.id}"
        exists = (
            db.query(BusinessUnread)
            .filter(
                BusinessUnread.receiver_user_id == employee_id,
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
            scope_id=employee_id,
            receiver_user_id=employee_id,
            trigger_user_id=None,
            is_unread=1,
            triggered_at=now,
        ))
        created_any = True

    records = (
        db.query(TrainingRecord)
        .filter(
            TrainingRecord.employee_id == employee_id,
            TrainingRecord.status == "completed",
            TrainingRecord.completed_date.isnot(None),
        )
        .all()
    )
    for record in records:
        expiry = _training_record_expiry_date(record)
        if not expiry:
            continue
        if expiry.date() >= today:
            continue
        entity_id = f"training_record:{record.id}"
        exists = (
            db.query(BusinessUnread)
            .filter(
                BusinessUnread.receiver_user_id == employee_id,
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
            scope_id=employee_id,
            receiver_user_id=employee_id,
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
    current_employee: Employee = Depends(get_current_employee),
):
    _ensure_employee_certificate_expired_notifications(db, str(current_employee.id))
    q = (
        db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_employee.id),
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
    current_employee: Employee = Depends(get_current_employee),
):
    q = (
        db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_employee.id),
            BusinessUnread.business_code == body.entity_type,
            BusinessUnread.is_unread == 1,
        )
    )
    if body.entity_id:
        q = q.filter(BusinessUnread.data_id == body.entity_id)
    q.update({"is_unread": 0})
    db.commit()
    return {"ok": True}
