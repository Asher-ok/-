from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String)  # image, pdf, etc.
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(String)  # 上传者ID（员工ID或管理员ID）
    
    # 关系
    task = relationship("Task", back_populates="documents")
