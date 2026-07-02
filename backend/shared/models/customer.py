from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, Date, Table, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


CUSTOMER_STATUS_UNARCHIVED = "未建档"
CUSTOMER_STATUS_PENDING_ARCHIVE = "待建档"
CUSTOMER_STATUS_ARCHIVED = "已建档"


customer_service_level1 = Table(
    "customer_service_level1",
    Base.metadata,
    Column("customer_id", String, ForeignKey("customers.id"), primary_key=True),
    Column("level1_id", String, ForeignKey("invoice_service_level1.id"), primary_key=True),
)


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
    ndis_plan_copy_path = Column(String)  # NDIS计划文件路径（客户类型为NDIS时使用）
    # M1 NDIS 档案扩展
    aboriginal_torres_strait = Column(Boolean)  # 原住民/托雷斯海峡岛民
    ndis_funding_type = Column(String)  # NDIS Managed / Self-Managed / Plan Managed
    medicare_number = Column(String)
    medicare_expiry = Column(Date)
    has_medical_card = Column(Boolean)  # 是否有医疗卡
    medical_card_number = Column(String)  # 医疗卡号
    private_health_fund = Column(String)  # 私立医保供应商
    private_policy_number = Column(String)  # 私立保单号
    customer_status = Column(String, default=CUSTOMER_STATUS_UNARCHIVED)
    weekly_service_hours = Column(Float)  # 本次每周服务时长（计划）
    weekly_served_hours = Column(Float, default=0)  # 本周累计已服务时长
    invoice_receiver_name = Column(String)
    invoice_receiver_phone = Column(String)
    invoice_receiver_email = Column(String)
    invoice_receiver_address = Column(Text)
    emergency_contact1_name = Column(String)
    emergency_contact1_phone = Column(String)
    emergency_contact1_email = Column(String)
    emergency_contact2_name = Column(String)
    emergency_contact2_phone = Column(String)
    emergency_contact2_email = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    tasks = relationship("Task", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    accepted_service_level1 = relationship(
        "InvoiceServiceLevel1",
        secondary=customer_service_level1,
        back_populates="customers",
    )
