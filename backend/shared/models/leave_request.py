"""请假请求模型"""
from sqlalchemy import Column, String, Text, DateTime, Date
from sqlalchemy.sql import func
from core.database import Base
import uuid


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(String, nullable=False)  # pending / approved / rejected
    approver_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
