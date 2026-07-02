"""
客户文档模型 - 12 类 NDIS 文档
"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base
import uuid


DOCUMENT_TYPES = [
    "easy_read",
    "intake_form",
    "consent_form",
    "handbook",
    "service_agreement",
    "support_plan",
    "emergency_plan",
    "home_safety",
    "risk_assessment",
    "feedback",
    "review_form",
    "exit_form",
]

STATUS_DRAFT = "draft"
STATUS_PENDING_SIGN = "pending_sign"
STATUS_SIGNED = "signed"


class CustomerDocument(Base):
    __tablename__ = "customer_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False)  # FK to customers
    document_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    file_type = Column(String)  # pdf, docx, etc.
    file_url = Column(String)  # 文件存储路径
    form_data = Column(Text)  # JSON 表单数据
    status = Column(String)  # draft / pending_sign / signed
    signed_at = Column(DateTime(timezone=True))
    signed_file_url = Column(String)  # 已签字文件路径
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
