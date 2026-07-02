from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = Column(String, unique=True, nullable=False)  # INV-YYMMDD格式
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default="draft")  # draft, sent, paid
    sent_at = Column(DateTime(timezone=True))
    email = Column(String)  # 发送到的邮箱
    pdf_url = Column(String)  # PDF文件URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"))
    description = Column(String, nullable=False)  # 服务描述
    service_code = Column(String)  # 服务代码
    price = Column(Numeric(10, 2), nullable=False)  # 单价
    quantity = Column(Numeric(10, 2), nullable=False, default=1)  # 数量
    amount = Column(Numeric(10, 2), nullable=False)  # 金额
    service_date = Column(DateTime(timezone=True))  # 服务日期
    service_time_start = Column(String)  # 服务开始时间（如 0900）
    service_time_end = Column(String)  # 服务结束时间（如 1200）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    invoice = relationship("Invoice", back_populates="items")
    task = relationship("Task", back_populates="invoice_items")
