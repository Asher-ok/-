from pydantic import BaseModel, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"
    approved = "approved"
    cancelled = "cancelled"


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    customer_id: str
    service_time: Optional[datetime] = None
    service_start_time: Optional[datetime] = None
    service_end_time: Optional[datetime] = None
    service_code: Optional[str] = None
    service_duration_hours: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    service_time: Optional[datetime] = None
    service_start_time: Optional[datetime] = None
    service_end_time: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    reject_reason: Optional[str] = None
    service_code: Optional[str] = None
    service_duration_hours: Optional[str] = None


class TaskServiceLineCreate(BaseModel):
    id: Optional[str] = None
    level1_id: Optional[str] = None
    level2_id: Optional[str] = None
    level3_id: Optional[str] = None
    service_code: Optional[str] = None
    duration_hours: Optional[str] = None
    quantity: Optional[str] = None
    duration_minutes: Optional[str] = None
    amount: Optional[str] = None
    unit_price: Optional[str] = None
    unit_price_override: Optional[str] = None
    remark: Optional[str] = None
    service_time_start: Optional[str] = None
    service_time_end: Optional[str] = None
    
    class Config:
        extra = "ignore"


class TaskEditRequest(BaseModel):
    services: List[TaskServiceLineCreate]
    employee_note: Optional[str] = None
    reason: Optional[str] = None


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatus
    employee_remark: Optional[str] = None


class TaskRemarkUpdateRequest(BaseModel):
    employee_remark: Optional[str] = None


class TaskServiceItemResponse(BaseModel):
    id: str
    level1_id: Optional[str] = None
    level2_id: Optional[str] = None
    level3_id: Optional[str] = None
    level1_name: Optional[str] = None
    level2_name: Optional[str] = None
    level3_name: Optional[str] = None
    service_code: str
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    remark: Optional[str] = None
    service_time_start: Optional[str] = None
    service_time_end: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: str
    has_update: Optional[bool] = None
    title: str
    description: Optional[str]
    customer_id: str
    service_time: datetime
    service_start_time: Optional[datetime]
    service_end_time: Optional[datetime]
    status: TaskStatus
    assigned_employee_id: Optional[str]
    assigned_employee_name: Optional[str] = None
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]
    reject_reason: Optional[str]
    questionnaire_id: Optional[str] = None
    questionnaire_data: Optional[Dict[str, Any]]
    incident_template_id: Optional[str] = None
    task_record_template_id: Optional[str] = None
    signature_image_url: Optional[str]
    photo_urls: Optional[List[str]]
    service_code: Optional[str]
    service_duration_hours: Optional[str]
    latest_claim_time: Optional[datetime] = None
    service_plans: Optional[List[Dict[str, Any]]] = None
    service_items: Optional[List[TaskServiceItemResponse]] = None
    employee_note: Optional[str] = None
    employee_remark: Optional[str] = None
    created_at: datetime
    
    @field_serializer(
        "service_time",
        "service_start_time",
        "service_end_time",
        "assigned_at",
        "completed_at",
        "latest_claim_time",
        "created_at",
    )
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class LocationTrackCreate(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    altitude: Optional[float] = None
    recorded_at: Optional[datetime] = None


class LocationTrackResponse(BaseModel):
    id: str
    task_id: str
    latitude: float
    longitude: float
    address: Optional[str]
    accuracy: Optional[float]
    speed: Optional[float]
    altitude: Optional[float]
    recorded_at: datetime
    created_at: datetime
    
    @field_serializer("recorded_at", "created_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True
