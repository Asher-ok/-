from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    email = Column(String)
    customer_code = Column(String, unique=True)
    customer_type = Column(String)
    gender = Column(String)
    age = Column(Integer)
    disability_type = Column(String)
    notes = Column(Text)
    introduction = Column(Text)  # 介绍
    attachments = Column(Text)  # 附件列表JSON
    ndis_number = Column(String)  # NDIS号码
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    tasks = relationship("Task", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
