from sqlalchemy import Column, String, DateTime, ForeignKey, Text, LargeBinary, Boolean, Float, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    employee_number = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    department = Column(String)
    phone = Column(String, nullable=False)
    email = Column(String)
    avatar_url = Column(String)
    account_status = Column(String, default="normal")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    reset_password_code_hash = Column(String)
    reset_password_code_expires_at = Column(DateTime(timezone=True))
    reset_password_code_sent_at = Column(DateTime(timezone=True))
    reset_password_code_attempts = Column(Integer)
    
    # 关系
    qualifications = relationship("Qualification", back_populates="employee", cascade="all, delete-orphan")
    training_records = relationship("TrainingRecord", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("EmployeeDocument", back_populates="employee", cascade="all, delete-orphan")
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
    created_by = Column(String)  # 创建者类型：'employee' 或 'admin'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    employee = relationship("Employee", back_populates="training_records")


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    name = Column(String, nullable=False)  # 文件名称
    file_type = Column(String)  # 文件类型：pdf, docx, jpg等
    file_url = Column(String, nullable=False)  # 文件URL
    document_type = Column(String, nullable=False)  # 文档类型：contract, checklist, code, tracker, handbook, onboarding
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(String)  # 上传者ID（管理员ID）
    
    # 合同签字相关字段
    employee_signature_blob = Column(LargeBinary)  # 员工签名图片二进制数据
    employee_signature_mime = Column(String)  # 员工签名图片MIME类型
    employee_signed_at = Column(DateTime(timezone=True))  # 员工签字时间
    employee_signature_x = Column(Float)  # 员工签字X坐标
    employee_signature_y = Column(Float)  # 员工签字Y坐标
    employee_signature_width = Column(Float)  # 员工签字区域宽度
    employee_signature_height = Column(Float)  # 员工签字区域高度
    employee_signature_page = Column(Integer)  # 员工签字页码（0-based）
    admin_signature_blob = Column(LargeBinary)  # 管理员签名图片二进制数据
    admin_signature_mime = Column(String)  # 管理员签名图片MIME类型
    admin_signed_at = Column(DateTime(timezone=True))  # 管理员签字时间
    admin_signed_by = Column(String)  # 签字的管理员ID
    admin_signature_x = Column(Float)  # 管理员签字X坐标
    admin_signature_y = Column(Float)  # 管理员签字Y坐标
    admin_signature_width = Column(Float)  # 管理员签字区域宽度
    admin_signature_height = Column(Float)  # 管理员签字区域高度
    admin_signature_page = Column(Integer)  # 管理员签字页码（0-based）
    
    # 关系
    employee = relationship("Employee", back_populates="documents")
