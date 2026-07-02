from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


class TaskCancellationNotification(Base):
    __tablename__ = "task_cancellation_notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    cancel_reason = Column(Text)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    confirmed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", backref="cancellation_notifications")
    employee = relationship("Employee", backref="cancellation_notifications")
