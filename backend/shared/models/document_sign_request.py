"""文档签字请求模型"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from core.database import Base
import uuid


class DocumentSignRequest(Base):
    __tablename__ = "document_sign_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String, unique=True, nullable=False)
    customer_id = Column(String, nullable=False)
    document_id = Column(String, nullable=False)  # CustomerDocument id
    status = Column(String, nullable=False)  # pending / signed / expired
    expires_at = Column(DateTime(timezone=True), nullable=False)
    signed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
