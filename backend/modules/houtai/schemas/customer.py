from pydantic import BaseModel, field_validator, model_validator, field_serializer
from typing import Optional, List, Any
from datetime import datetime, date
import json
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


def _validate_medical_card(has_medical_card, medical_card_number):
    """当 has_medical_card 为 True 时，medical_card_number 必填"""
    if has_medical_card is True:
        if not medical_card_number or not str(medical_card_number).strip():
            raise ValueError("选择「是」时，医疗卡号必填")


class CustomerAttachment(BaseModel):
    name: str
    url: Optional[str] = None
    path: Optional[str] = None


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
    ndis_number: Optional[str] = None
    aboriginal_torres_strait: Optional[bool] = None
    ndis_funding_type: Optional[str] = None
    medicare_number: Optional[str] = None
    medicare_expiry: Optional[date] = None
    has_medical_card: Optional[bool] = None
    medical_card_number: Optional[str] = None
    private_health_fund: Optional[str] = None
    private_policy_number: Optional[str] = None
    invoice_receiver_name: Optional[str] = None
    invoice_receiver_phone: Optional[str] = None
    invoice_receiver_email: Optional[str] = None
    invoice_receiver_address: Optional[str] = None
    emergency_contact1_name: Optional[str] = None
    emergency_contact1_phone: Optional[str] = None
    emergency_contact1_email: Optional[str] = None
    emergency_contact2_name: Optional[str] = None
    emergency_contact2_phone: Optional[str] = None
    emergency_contact2_email: Optional[str] = None
    weekly_service_hours: float
    attachments: Optional[List[CustomerAttachment]] = None
    accepted_service_level1_ids: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_medical_card_required(self):
        _validate_medical_card(self.has_medical_card, self.medical_card_number)
        return self


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
    ndis_number: Optional[str] = None
    aboriginal_torres_strait: Optional[bool] = None
    ndis_funding_type: Optional[str] = None
    medicare_number: Optional[str] = None
    medicare_expiry: Optional[date] = None
    has_medical_card: Optional[bool] = None
    medical_card_number: Optional[str] = None
    private_health_fund: Optional[str] = None
    private_policy_number: Optional[str] = None
    invoice_receiver_name: Optional[str] = None
    invoice_receiver_phone: Optional[str] = None
    invoice_receiver_email: Optional[str] = None
    invoice_receiver_address: Optional[str] = None
    emergency_contact1_name: Optional[str] = None
    emergency_contact1_phone: Optional[str] = None
    emergency_contact1_email: Optional[str] = None
    emergency_contact2_name: Optional[str] = None
    emergency_contact2_phone: Optional[str] = None
    emergency_contact2_email: Optional[str] = None
    weekly_service_hours: Optional[float] = None
    attachments: Optional[List[CustomerAttachment]] = None
    accepted_service_level1_ids: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_medical_card_required(self):
        _validate_medical_card(self.has_medical_card, self.medical_card_number)
        return self


class CustomerResponse(BaseModel):
    id: str
    has_update: bool = False
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
    ndis_number: Optional[str] = None
    ndis_plan_copy_path: Optional[str] = None
    aboriginal_torres_strait: Optional[bool] = None
    ndis_funding_type: Optional[str] = None
    medicare_number: Optional[str] = None
    medicare_expiry: Optional[date] = None
    has_medical_card: Optional[bool] = None
    medical_card_number: Optional[str] = None
    private_health_fund: Optional[str] = None
    private_policy_number: Optional[str] = None
    invoice_receiver_name: Optional[str] = None
    invoice_receiver_phone: Optional[str] = None
    invoice_receiver_email: Optional[str] = None
    invoice_receiver_address: Optional[str] = None
    emergency_contact1_name: Optional[str] = None
    emergency_contact1_phone: Optional[str] = None
    emergency_contact1_email: Optional[str] = None
    emergency_contact2_name: Optional[str] = None
    emergency_contact2_phone: Optional[str] = None
    emergency_contact2_email: Optional[str] = None
    weekly_service_hours: Optional[float] = None
    weekly_served_hours: Optional[float] = None
    attachments: Optional[List[CustomerAttachment]] = None
    accepted_service_level1_ids: Optional[List[str]] = None
    accepted_service_level1_names: Optional[List[str]] = None
    service_count: Optional[int] = None
    last_service_time: Optional[datetime] = None
    created_at: datetime
    
    @field_serializer("last_service_time", "created_at")
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
