from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.sql import func
from core.database import Base
from datetime import datetime
import uuid


class UpdateNotification(Base):
    __tablename__ = "update_notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    audience_type = Column(String, nullable=False)  # admin / employee
    audience_id = Column(String, nullable=False)  # admin user id / employee id
    entity_type = Column(String, nullable=False)  # employee / customer / task / leave_request / employee_document ...
    entity_id = Column(String, nullable=True)
    event_type = Column(String, nullable=True)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)


class BusinessUnread(Base):
    __tablename__ = "business_unread"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_code = Column(String, nullable=False)
    data_id = Column(String, nullable=True)
    scope_id = Column(String, nullable=True)
    receiver_user_id = Column(String, nullable=False)
    trigger_user_id = Column(String, nullable=True)
    is_unread = Column(Integer, nullable=False, default=1)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def touch_business_unread(
    db,
    *,
    business_code: str,
    receiver_user_id: str,
    data_id: str | None = None,
    scope_id: str | None = None,
    trigger_user_id: str | None = None,
    triggered_at: datetime | None = None,
) -> None:
    now = triggered_at or datetime.utcnow()
    q = (
        db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == receiver_user_id,
            BusinessUnread.business_code == business_code,
            BusinessUnread.data_id == data_id,
        )
    )
    row = q.first()
    if row:
        row.is_unread = 1
        row.triggered_at = now
        row.trigger_user_id = trigger_user_id
        if scope_id is not None:
            row.scope_id = scope_id
        return
    db.add(
        BusinessUnread(
            business_code=business_code,
            data_id=data_id,
            scope_id=scope_id,
            receiver_user_id=receiver_user_id,
            trigger_user_id=trigger_user_id,
            is_unread=1,
            triggered_at=now,
        )
    )
