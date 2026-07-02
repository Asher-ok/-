from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, LargeBinary, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum
import uuid


class TaskStatus(str, enum.Enum):
    pending = "pending"  # 待领取
    in_progress = "in_progress"  # 进行中
    completed = "completed"  # 已完成
    rejected = "rejected"  # 审核未通过
    approved = "approved"  # 审核通过


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    service_time = Column(DateTime(timezone=True), nullable=False)
    service_start_time = Column(DateTime(timezone=True))
    service_end_time = Column(DateTime(timezone=True))
    status = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False)
    assigned_employee_id = Column(String, ForeignKey("employees.id"))
    assigned_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    reject_reason = Column(Text)
    questionnaire_data = Column(JSON)  # 问卷数据
    signature_image_url = Column(String)  # 签名图片URL
    signature_blob = Column(LargeBinary)  # 签名图片二进制
    signature_mime = Column(String)  # 签名图片类型
    photo_urls = Column(JSON)  # 照片URL列表
    service_code = Column(String)  # 服务代码（用于发票）
    service_duration_hours = Column(String)  # 服务时长（小时）
    latest_claim_time = Column(DateTime(timezone=True))  # 最晚领取时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    customer = relationship("Customer", back_populates="tasks")
    assigned_employee = relationship("Employee", back_populates="tasks")
    documents = relationship("Document", back_populates="task", cascade="all, delete-orphan")
    invoice_items = relationship("InvoiceItem", back_populates="task")
    photos = relationship("TaskPhoto", back_populates="task", cascade="all, delete-orphan")
    location_tracks = relationship("TaskLocationTrack", back_populates="task", cascade="all, delete-orphan")


class TaskPhoto(Base):
    __tablename__ = "task_photos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    photo_blob = Column(LargeBinary, nullable=False)
    photo_mime = Column(String, nullable=False)
    shot_at = Column(DateTime(timezone=True))
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="photos")


class TaskLocationTrack(Base):
    __tablename__ = "task_location_tracks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text)
    accuracy = Column(Float)  # 位置精度（米）
    speed = Column(Float)  # 速度（米/秒）
    altitude = Column(Float)  # 海拔（米）
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="location_tracks")