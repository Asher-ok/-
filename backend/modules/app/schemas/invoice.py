from pydantic import BaseModel, field_serializer
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


class InvoiceItemCreate(BaseModel):
    task_id: Optional[str] = None
    description: str
    service_code: Optional[str] = None
    price: Decimal
    quantity: Decimal = Decimal("1")
    service_date: Optional[datetime] = None
    service_time_start: Optional[str] = None
    service_time_end: Optional[str] = None


class InvoiceItemResponse(BaseModel):
    id: str
    description: str
    service_code: Optional[str]
    price: Decimal
    quantity: Decimal
    amount: Decimal
    service_date: Optional[datetime]
    service_time_start: Optional[str]
    service_time_end: Optional[str]
    
    @field_serializer("service_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    customer_id: str
    invoice_date: datetime
    items: List[InvoiceItemCreate]


class InvoiceGenerateRequest(BaseModel):
    """发票生成请求：选择审核通过的任务"""
    customer_id: str
    task_ids: List[str]  # 要生成发票的任务ID列表
    invoice_date: Optional[datetime] = None  # 如果不提供，使用当前日期


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    customer_id: str
    invoice_date: datetime
    total_amount: Decimal
    status: str
    sent_at: Optional[datetime]
    email: Optional[str]
    pdf_url: Optional[str]
    items: List[InvoiceItemResponse] = []
    created_at: datetime
    
    @field_serializer("invoice_date", "sent_at", "created_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True
