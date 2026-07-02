"""员工合同签署请求模型（无需登录的签署链接）"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from core.database import Base
import uuid


class EmployeeContractSignRequest(Base):
    __tablename__ = "employee_contract_sign_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String, unique=True, nullable=False)
    employee_id = Column(String, nullable=False)
    contract_id = Column(String, nullable=False)  # EmployeeDocument id
    status = Column(String, nullable=False)  # pending / signed / expired
    expires_at = Column(DateTime(timezone=True), nullable=False)
    signed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
