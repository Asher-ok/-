from pydantic import BaseModel, EmailStr, field_validator, field_serializer
from typing import Optional, List, Union
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
    certificate_url: Optional[str] = None
    obtained_date: datetime
    expiry_date: Optional[datetime] = None
    issuing_authority: Optional[str] = None
    
    @field_serializer("obtained_date", "expiry_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)


class QualificationResponse(BaseModel):
    id: str
    employee_id: Optional[str] = None
    name: str
    certificate_number: Optional[str]
    certificate_url: Optional[str]
    obtained_date: datetime
    expiry_date: Optional[datetime]
    issuing_authority: Optional[str]
    
    @field_serializer("obtained_date", "expiry_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class QualificationUpdate(BaseModel):
    name: Optional[str] = None
    certificate_number: Optional[str] = None
    obtained_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    issuing_authority: Optional[str] = None


class QualificationListItem(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    employee_number: str
    name: str
    certificate_number: Optional[str]
    certificate_url: Optional[str]
    obtained_date: datetime
    expiry_date: Optional[datetime]
    issuing_authority: Optional[str]
    
    @field_serializer("obtained_date", "expiry_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)


class TrainingRecordCreate(BaseModel):
    name: str
    category: Optional[str] = None  # 分类：certificate, first-aid, manual-handling
    completed_date: datetime
    status: Optional[TrainingStatus] = None
    score: Optional[str] = None
    has_certificate: Optional[bool] = None
    certificate_number: Optional[str] = None
    certificate_url: Optional[str] = None
    certificate_obtained_date: Optional[Union[datetime, str]] = None
    certificate_expiry_date: Optional[Union[datetime, str]] = None
    training_institution: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('certificate_obtained_date', 'certificate_expiry_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                # 处理 YYYY-MM-DD 格式
                if len(v) == 10:
                    return datetime.fromisoformat(v + "T00:00:00")
                return datetime.fromisoformat(v)
            except (ValueError, TypeError):
                return None
        return None
    
    @field_serializer("completed_date", "certificate_obtained_date", "certificate_expiry_date")
    def serialize_datetimes(self, value):
        if isinstance(value, str):
            return value
        return _format_datetime_minute(value)


class TrainingRecordUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None  # 分类：certificate, first-aid, manual-handling
    completed_date: Optional[datetime] = None
    status: Optional[TrainingStatus] = None
    score: Optional[str] = None
    has_certificate: Optional[bool] = None
    certificate_number: Optional[str] = None
    certificate_url: Optional[str] = None
    certificate_obtained_date: Optional[Union[datetime, str]] = None
    certificate_expiry_date: Optional[Union[datetime, str]] = None
    training_institution: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('certificate_obtained_date', 'certificate_expiry_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        return TrainingRecordCreate.parse_date(v)

    @field_validator('completed_date', mode='before')
    @classmethod
    def parse_completed_date(cls, v):
        return TrainingRecordCreate.parse_date(v)


class TrainingRecordResponse(BaseModel):
    id: str
    name: str
    category: Optional[str]
    completed_date: datetime
    status: Optional[TrainingStatus]
    score: Optional[str]
    has_certificate: Optional[bool]
    certificate_number: Optional[str]
    certificate_url: Optional[str]
    certificate_obtained_date: Optional[datetime]
    certificate_expiry_date: Optional[datetime]
    training_institution: Optional[str]
    notes: Optional[str]
    created_by: Optional[str] = None  # 创建者类型：'employee' 或 'admin'
    
    @field_serializer("completed_date", "certificate_obtained_date", "certificate_expiry_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    name: str
    password: str
    department: Optional[str] = None
    phone: str
    email: EmailStr
    avatar_url: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class EmployeeAccountStatusUpdate(BaseModel):
    account_status: str


class EmployeeResponse(BaseModel):
    employee_number: str
    name: str
    id: str
    has_update: bool = False
    has_qualification_update: bool = False
    department: Optional[str]
    phone: str
    email: Optional[str]
    avatar_url: Optional[str]
    account_status: Optional[str] = None
    weekly_served_hours: Optional[float] = None
    created_at: Optional[datetime] = None
    qualifications: List[QualificationResponse] = []
    training_records: List[TrainingRecordResponse] = []
    expiring_qualifications: List[QualificationResponse] = []
    expiring_count: int = 0
    expiring_primary_certificate_number: Optional[str] = None
    expiring_primary_expiry_date: Optional[datetime] = None
    expiring_primary_qualification_name: Optional[str] = None
    expiring_primary_days_until_expiry: Optional[int] = None
    
    @field_serializer("created_at", "expiring_primary_expiry_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class ExpiringTrainingRecordItem(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    employee_number: str
    name: str
    category: Optional[str]
    completed_date: datetime
    expiry_date: datetime  # 计算值：completed_date + 12个月
    days_until_expiry: int  # 距离到期的天数
    reminder_status: str  # 提醒状态：3_months, 1_month, 1_week, expired, normal
    certificate_url: Optional[str]
    certificate_number: Optional[str]
    training_institution: Optional[str]
    
    @field_serializer("completed_date", "expiry_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)


class ReminderSettingPayload(BaseModel):
    days: int


class EmployeeDocumentResponse(BaseModel):
    id: str
    employee_id: str
    name: str
    file_type: Optional[str]
    file_url: str
    document_type: str
    uploaded_at: datetime
    uploaded_by: Optional[str]
    employee_signed_at: Optional[datetime] = None
    admin_signed_at: Optional[datetime] = None
    admin_signed_by: Optional[str] = None
    employee_signature_x: Optional[float] = None
    employee_signature_y: Optional[float] = None
    employee_signature_width: Optional[float] = None
    employee_signature_height: Optional[float] = None
    employee_signature_page: Optional[int] = None
    admin_signature_x: Optional[float] = None
    admin_signature_y: Optional[float] = None
    admin_signature_width: Optional[float] = None
    admin_signature_height: Optional[float] = None
    admin_signature_page: Optional[int] = None
    
    @field_serializer("uploaded_at", "employee_signed_at", "admin_signed_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class ContractGenerateRequest(BaseModel):
    start_date: str
    employment_type: str  # full-time, part-time, casual
    position: str  # support-worker, admin, office-staff
    superior_first_name: str
    superior_last_name: str
    superior_title: str
    hours_per_week: float
    work_hours: str  # Format: "HH:mm to HH:mm"
    gross_salary: float
    signature_date: str
