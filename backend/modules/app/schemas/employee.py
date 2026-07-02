from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional, List
from datetime import datetime
from enum import Enum
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")
class TrainingStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"
    pending = "pending"



class QualificationCreate(BaseModel):
    name: str
    certificate_number: Optional[str] = None
    obtained_date: datetime
    expiry_date: Optional[datetime] = None
    issuing_authority: Optional[str] = None
    
    @field_serializer("obtained_date", "expiry_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)


class QualificationResponse(BaseModel):
    id: str
    name: str
    certificate_number: Optional[str]
    obtained_date: datetime
    expiry_date: Optional[datetime]
    issuing_authority: Optional[str]
    
    @field_serializer("obtained_date", "expiry_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class TrainingRecordCreate(BaseModel):
    name: str
    completed_date: datetime
    status: Optional[TrainingStatus] = None
    score: Optional[str] = None
    has_certificate: Optional[bool] = None
    certificate_number: Optional[str] = None
    certificate_url: Optional[str] = None
    training_institution: Optional[str] = None
    notes: Optional[str] = None
    
    @field_serializer("completed_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)


class TrainingRecordResponse(BaseModel):
    id: str
    name: str
    completed_date: datetime
    status: Optional[TrainingStatus]
    score: Optional[str]
    has_certificate: Optional[bool]
    certificate_number: Optional[str]
    certificate_url: Optional[str]
    training_institution: Optional[str]
    notes: Optional[str]
    created_by: Optional[str] = None  # 创建者类型：'employee' 或 'admin'
    
    @field_serializer("completed_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    name: str
    employee_number: str
    department: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: str
    name: str
    employee_number: str
    department: Optional[str]
    phone: str
    email: Optional[str]
    avatar_url: Optional[str]
    account_status: Optional[str] = None
    qualifications: List[QualificationResponse] = []
    training_records: List[TrainingRecordResponse] = []
    
    class Config:
        from_attributes = True
