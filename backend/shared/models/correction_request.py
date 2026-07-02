"""修改审批请求模型"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base
import uuid


class CorrectionRequest(Base):
    __tablename__ = "correction_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, nullable=False)
    requested_by = Column(String, nullable=False)  # employee_id
    original_data = Column(Text)  # JSON
    corrected_data = Column(Text)  # JSON
    reason = Column(Text)
    status = Column(String, nullable=False)  # pending / approved / rejected
    approver_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
