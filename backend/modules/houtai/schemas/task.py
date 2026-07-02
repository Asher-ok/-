from pydantic import BaseModel, computed_field, field_serializer, field_validator, model_validator, Field, AliasChoices
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from .customer import CustomerResponse
from shared.models.task import TaskServiceItem
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


def _parse_datetime_or_date(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            try:
                d = datetime.strptime(s, "%Y-%m-%d")
                return d
            except Exception:
                return None
        try:
            return datetime.fromisoformat(s.replace(" ", "T"))
        except Exception:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                continue
    return None


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"
    approved = "approved"
    cancelled = "cancelled"


class TaskServiceLineCreate(BaseModel):
    level1_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("level1_id", "level1Id"))
    level2_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("level2_id", "level2Id"))
    level3_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("level3_id", "level3Id"))
    service_code: str = Field(validation_alias=AliasChoices("service_code", "serviceCode"))
    duration_hours: Decimal = Field(validation_alias=AliasChoices("duration_hours", "durationHours", "duration"))
    unit_price_override: Optional[Decimal] = Field(default=None, validation_alias=AliasChoices("unit_price_override", "unitPriceOverride", "unit_price"))
    remark: Optional[str] = None
    service_time_start: Optional[str] = Field(default=None, validation_alias=AliasChoices("service_time_start", "serviceTimeStart"))
    service_time_end: Optional[str] = Field(default=None, validation_alias=AliasChoices("service_time_end", "serviceTimeEnd"))


class TaskQuestionnaireLineCreate(BaseModel):
    questionnaire_id: str = Field(validation_alias=AliasChoices("questionnaire_id", "questionnaireId", "id"))
    is_required: bool = Field(default=True, validation_alias=AliasChoices("is_required", "isRequired", "required"))
    order_index: int = Field(default=0, validation_alias=AliasChoices("order_index", "orderIndex", "order"))


class TaskServiceItemResponse(BaseModel):
    id: str
    level1_id: Optional[str] = None
    level2_id: Optional[str] = None
    level3_id: Optional[str] = None
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


class TaskQuestionnaireResponse(BaseModel):
    id: str
    questionnaire_id: str
    title: Optional[str] = None
    is_required: bool = True
    is_filled: bool = False
    order_index: int = 0

    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    customer_id: str = Field(validation_alias=AliasChoices("customer_id", "customerId"))
    service_time: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("service_time", "serviceTime"))
    service_start_time: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("service_start_time", "serviceStartTime"))
    service_end_time: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("service_end_time", "serviceEndTime"))
    assigned_employee_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("assigned_employee_id", "assignedEmployeeId"))
    questionnaire_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("questionnaire_id", "questionnaireId"))
    incident_template_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("incident_template_id", "incidentTemplateId"))
    task_record_template_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("task_record_template_id", "taskRecordTemplateId"))
    service_code: Optional[str] = None
    service_duration_hours: Optional[str] = None
    unit_price: Optional[Decimal] = None
    latest_claim_time: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("latest_claim_time", "latestClaimTime"))
    repeat_rule: Optional[str] = Field(default=None, validation_alias=AliasChoices("repeat_rule", "repeatRule"))
    repeat_months: Optional[int] = Field(default=None, validation_alias=AliasChoices("repeat_months", "repeatMonths"))
    services: Optional[List[TaskServiceLineCreate]] = None
    questionnaires: Optional[List[TaskQuestionnaireLineCreate]] = None

    @field_validator("service_time", "service_start_time", "service_end_time", "latest_claim_time", mode="before")
    @classmethod
    def _coerce_datetimes(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        parsed = _parse_datetime_or_date(v)
        return parsed if parsed is not None else v

    @model_validator(mode="after")
    def _derive_times(self):
        if self.service_start_time is None and self.services:
            starts: list[datetime] = []
            for s in self.services:
                dt = _parse_datetime_or_date(getattr(s, "service_time_start", None))
                if dt is not None:
                    starts.append(dt)
            if starts:
                self.service_start_time = min(starts)
        if self.service_end_time is None and self.services:
            ends: list[datetime] = []
            for s in self.services:
                dt = _parse_datetime_or_date(getattr(s, "service_time_end", None))
                if dt is not None:
                    ends.append(dt)
            if ends:
                self.service_end_time = max(ends)
        if self.service_time is None and self.service_start_time is not None:
            self.service_time = self.service_start_time
        if self.service_time is None and self.service_start_time is None:
            raise ValueError("service_time/service_start_time 不能为空")
        return self


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    service_time: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("service_time", "serviceTime"))
    service_start_time: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("service_start_time", "serviceStartTime"))
    service_end_time: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("service_end_time", "serviceEndTime"))
    assigned_employee_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("assigned_employee_id", "assignedEmployeeId"))
    status: Optional[TaskStatus] = None
    reject_reason: Optional[str] = None
    questionnaire_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("questionnaire_id", "questionnaireId"))
    incident_template_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("incident_template_id", "incidentTemplateId"))
    task_record_template_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("task_record_template_id", "taskRecordTemplateId"))
    service_code: Optional[str] = None
    service_duration_hours: Optional[str] = None
    unit_price: Optional[Decimal] = None
    latest_claim_time: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("latest_claim_time", "latestClaimTime"))
    repeat_rule: Optional[str] = Field(default=None, validation_alias=AliasChoices("repeat_rule", "repeatRule"))
    repeat_months: Optional[int] = Field(default=None, validation_alias=AliasChoices("repeat_months", "repeatMonths"))
    services: Optional[List[TaskServiceLineCreate]] = None
    service_plans: Optional[List[Dict[str, Any]]] = None
    questionnaires: Optional[List[TaskQuestionnaireLineCreate]] = None

    @field_validator("service_time", "service_start_time", "service_end_time", "latest_claim_time", mode="before")
    @classmethod
    def _coerce_datetimes(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        parsed = _parse_datetime_or_date(v)
        return parsed if parsed is not None else v


class TaskResponse(BaseModel):
    id: str
    has_update: bool = False
    title: str
    description: Optional[str]
    customer_id: str
    customer: Optional[CustomerResponse] = None
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
    unit_price: Optional[Decimal] = None
    latest_claim_time: Optional[datetime] = None
    repeat_rule: Optional[str] = None
    repeat_months: Optional[int] = None
    service_items: Optional[List[TaskServiceItemResponse]] = None
    task_questionnaires: Optional[List[TaskQuestionnaireResponse]] = None
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
    
    @computed_field
    @property
    def overdue_duration(self) -> Optional[str]:
        """计算超时时长，仅当状态为pending且已超时时返回"""
        if self.status != TaskStatus.pending:
            return None
        if not self.latest_claim_time:
            return None
        
        now = datetime.now(timezone.utc)
        # 确保 latest_claim_time 有时区信息
        claim_time = self.latest_claim_time
        if claim_time.tzinfo is None:
            claim_time = claim_time.replace(tzinfo=timezone.utc)
        
        if claim_time >= now:
            return None  # 未超时
        
        diff = now - claim_time
        total_seconds = int(diff.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        
        if days > 0:
            return f"已超时 {days}天{hours}小时"
        elif hours > 0:
            return f"已超时 {hours}小时{minutes}分钟"
        else:
            return f"已超时 {minutes}分钟"
    
    class Config:
        from_attributes = True
