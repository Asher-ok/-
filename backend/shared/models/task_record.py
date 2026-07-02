from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base
import uuid


class TaskRecord(Base):
    __tablename__ = "task_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, nullable=False)
    customer_id = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    template_id = Column(String)
    record_data = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
