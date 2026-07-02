from pydantic import BaseModel, field_validator, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


class CustomerCreate(BaseModel):
    name: str
    phone: str
    address: str
    email: Optional[str] = None
    introduction: Optional[str] = None
    notes: Optional[str] = None
    customer_type: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    disability_type: Optional[str] = None
    weekly_service_hours: Optional[float] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    introduction: Optional[str] = None
    notes: Optional[str] = None
    customer_type: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    disability_type: Optional[str] = None
    weekly_service_hours: Optional[float] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class CustomerResponse(BaseModel):
    id: str
    customer_code: Optional[str] = None
    customer_status: Optional[str] = None
    name: str
    phone: str
    address: str
    email: Optional[str]
    introduction: Optional[str]
    notes: Optional[str]
    customer_type: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    disability_type: Optional[str] = None
    emergency_contact1_name: Optional[str] = None
    emergency_contact1_phone: Optional[str] = None
    emergency_contact1_email: Optional[str] = None
    emergency_contact2_name: Optional[str] = None
    emergency_contact2_phone: Optional[str] = None
    emergency_contact2_email: Optional[str] = None
    weekly_service_hours: Optional[float] = None
    weekly_served_hours: Optional[float] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    
    @field_serializer("created_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True

    @field_validator("attachments", mode="before")
    def normalize_attachments(cls, value: Any):
        if value is None:
            return None
        if isinstance(value, list):
            normalized = []
            for item in value:
                if isinstance(item, dict) and "url" not in item:
                    item = {**item, "url": ""}
                normalized.append(item)
            return normalized
        if isinstance(value, str):
            try:
                data = json.loads(value)
                if isinstance(data, list):
                    normalized = []
                    for item in data:
                        if isinstance(item, dict) and "url" not in item:
                            item = {**item, "url": ""}
                        normalized.append(item)
                    return normalized
                return []
            except Exception:
                return []
        return []
