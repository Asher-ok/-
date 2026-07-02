import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class InvoiceServiceLevel1(Base):
    __tablename__ = "invoice_service_level1"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    level2_list = relationship("InvoiceServiceLevel2", back_populates="level1", cascade="all, delete-orphan")
    level3_list = relationship("InvoiceServiceLevel3", back_populates="level1", cascade="all, delete-orphan")
    customers = relationship(
        "Customer",
        secondary="customer_service_level1",
        back_populates="accepted_service_level1",
    )


class InvoiceServiceLevel2(Base):
    __tablename__ = "invoice_service_level2"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    level1_id = Column(String, ForeignKey("invoice_service_level1.id"), nullable=False)
    name = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    level1 = relationship("InvoiceServiceLevel1", back_populates="level2_list")
    level3_list = relationship("InvoiceServiceLevel3", back_populates="level2", cascade="all, delete-orphan")


class InvoiceServiceLevel3(Base):
    __tablename__ = "invoice_service_level3"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    level1_id = Column(String, ForeignKey("invoice_service_level1.id"), nullable=False)
    level2_id = Column(String, ForeignKey("invoice_service_level2.id"))
    name = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    level1 = relationship("InvoiceServiceLevel1", back_populates="level3_list")
    level2 = relationship("InvoiceServiceLevel2", back_populates="level3_list")
    codes = relationship("InvoiceServiceCode", back_populates="level3", cascade="all, delete-orphan")


class InvoiceServiceCode(Base):
    __tablename__ = "invoice_service_codes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    level3_id = Column(String, ForeignKey("invoice_service_level3.id"), nullable=False)
    code = Column(String, nullable=False, unique=True)
    price = Column(Numeric(12, 4))
    unit = Column(String)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    level3 = relationship("InvoiceServiceLevel3", back_populates="codes")
