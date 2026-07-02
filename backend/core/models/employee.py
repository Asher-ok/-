from sqlalchemy import Column, String, DateTime, ForeignKey, Text, LargeBinary, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    employee_number = Column(String, unique=True, nullable=False)
    department = Column(String)
    phone = Column(String, nullable=False)
    email = Column(String)
    avatar_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    qualifications = relationship("Qualification", back_populates="employee", cascade="all, delete-orphan")
    training_records = relationship("TrainingRecord", back_populates="employee", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="assigned_employee")


class Qualification(Base):
    __tablename__ = "qualifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    name = Column(String, nullable=False)
    certificate_number = Column(String)
    certificate_url = Column(String)
    certificate_blob = Column(LargeBinary)
    certificate_mime = Column(String)
    obtained_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True))
    issuing_authority = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    employee = relationship("Employee", back_populates="qualifications")


class TrainingRecord(Base):
    __tablename__ = "training_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)  # 分类：certificate, first-aid, manual-handling
    status = Column(String, nullable=False, default="rejected")
    completed_date = Column(DateTime(timezone=True), nullable=False)
    score = Column(String)  # 使用字符串以支持各种格式
    has_certificate = Column(Boolean, default=False)
    certificate_number = Column(String)
    certificate_url = Column(String)
    certificate_obtained_date = Column(DateTime(timezone=True))  # 证书颁发日期
    certificate_expiry_date = Column(DateTime(timezone=True))  # 证书到期日期
    training_institution = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    employee = relationship("Employee", back_populates="training_records")
