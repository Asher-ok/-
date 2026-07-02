"""客户文档 Schema"""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from pydantic import field_serializer
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


DOCUMENT_TYPES = [
    "easy_read",
    "intake_form",
    "consent_form",
    "handbook",
    "service_agreement",
    "support_plan",
    "emergency_plan",
    "home_safety",
    "risk_assessment",
    "feedback",
    "review_form",
    "exit_form",
]


class CustomerDocumentCreate(BaseModel):
    document_type: str
    name: str
    file_type: Optional[str] = None
    form_data: Optional[dict] = None


class CustomerDocumentUpdate(BaseModel):
    name: Optional[str] = None
    form_data: Optional[dict] = None


class CustomerDocumentResponse(BaseModel):
    id: str
    customer_id: str
    document_type: str
    name: str
    file_type: Optional[str] = None
    file_url: Optional[str] = None
    form_data: Optional[dict] = None
    status: Optional[str] = None
    signed_at: Optional[datetime] = None
    signed_file_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_serializer("signed_at", "created_at", "updated_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)

    class Config:
        from_attributes = True
