from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


class InvoiceItemCategory(Base):
    __tablename__ = "invoice_item_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String, ForeignKey("invoice_item_categories.id"))
    name = Column(String, nullable=False)
    code = Column(String)
    level = Column(Integer, nullable=False, default=1)
    path = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent = relationship("InvoiceItemCategory", remote_side=[id])
    items = relationship("InvoiceItemDict", back_populates="category")


class InvoiceItemDict(Base):
    __tablename__ = "invoice_item_dict"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey("invoice_item_categories.id"), nullable=False)

    item_code = Column(String, unique=True, nullable=False)
    item_name = Column(String, nullable=False)
    spec_default = Column(String)
    unit_default = Column(String)
    price_default = Column(Numeric(12, 4))
    tax_rate_default = Column(Numeric(6, 5), nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)
    created_from_invoice_id = Column(String, ForeignKey("invoices.id"))
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("InvoiceItemCategory", back_populates="items")
    versions = relationship("InvoiceItemDictVersion", back_populates="item", cascade="all, delete-orphan")


class InvoiceItemDictVersion(Base):
    __tablename__ = "invoice_item_dict_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String, ForeignKey("invoice_item_dict.id"), nullable=False)
    version_no = Column(Integer, nullable=False)

    item_code = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    spec_default = Column(String)
    unit_default = Column(String)
    price_default = Column(Numeric(12, 4))
    tax_rate_default = Column(Numeric(6, 5), nullable=False)

    changed_by = Column(String)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    item = relationship("InvoiceItemDict", back_populates="versions")


class InvoiceAuditLog(Base):
    __tablename__ = "invoice_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    action = Column(String, nullable=False)
    actor_id = Column(String)
    actor_type = Column(String)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    before_json = Column(Text)
    after_json = Column(Text)

    invoice = relationship("Invoice")


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = Column(String, unique=True, nullable=False)  # INV-YYMMDD格式
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default="draft")  # draft, sent, paid
    sent_at = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    voided_at = Column(DateTime(timezone=True))
    void_reason = Column(Text)
    email = Column(String)  # 发送到的邮箱
    pdf_url = Column(String)  # PDF文件URL
    currency = Column(String, nullable=False, default="AUD")
    buyer_name = Column(String)
    buyer_phone = Column(String)
    buyer_email = Column(String)
    buyer_address = Column(Text)
    total_excl_tax = Column(Numeric(12, 2), nullable=False, default=0)
    total_tax = Column(Numeric(12, 2), nullable=False, default=0)
    total_incl_tax = Column(Numeric(12, 2), nullable=False, default=0)
    created_by = Column(String)
    updated_by = Column(String)
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
    task_service_item_id = Column(String)
    line_no = Column(Integer)
    item_id = Column(String, ForeignKey("invoice_item_dict.id"))
    category_id = Column(String, ForeignKey("invoice_item_categories.id"))
    item_code = Column(String)
    item_name = Column(String)
    specification = Column(String)
    unit = Column(String)
    unit_price = Column(Numeric(12, 4))
    amount_excl_tax = Column(Numeric(12, 2))
    tax_rate = Column(Numeric(6, 5), default=0)
    tax_amount = Column(Numeric(12, 2))
    amount_incl_tax = Column(Numeric(12, 2))
    source_task_id = Column(String, ForeignKey("tasks.id"))
    remark = Column(Text)
    description = Column(String, nullable=False)  # 服务描述
    service_code = Column(String)  # 服务代码
    price = Column(Numeric(10, 2), nullable=False)  # 单价
    quantity = Column(Numeric(10, 2), nullable=False, default=1)  # 数量
    amount = Column(Numeric(10, 2), nullable=False)  # 金额
    service_date = Column(DateTime(timezone=True))  # 服务日期
    service_time_start = Column(String)  # 服务开始时间（如 0900）
    service_time_end = Column(String)  # 服务结束时间（如 1200）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    invoice = relationship("Invoice", back_populates="items")
    task = relationship("Task", back_populates="invoice_items", foreign_keys=[task_id])
    source_task = relationship("Task", foreign_keys=[source_task_id])
