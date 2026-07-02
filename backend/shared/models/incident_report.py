"""事故报告模型"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base
import uuid


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, nullable=False)
    customer_id = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    incident_type = Column(String)  # fall, near_fall, etc.
    description = Column(Text)
    occurred_at = Column(DateTime(timezone=True))
    template_id = Column(String)  # 关联事故报告模板（可为空）
    report_data = Column(Text)  # JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
