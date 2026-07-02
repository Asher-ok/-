from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


class TaskCancellationNotificationResponse(BaseModel):
    id: str
    task_id: str
    task_title: str
    customer_name: str
    service_time: datetime
    cancel_reason: Optional[str]
    is_confirmed: bool
    confirmed_at: Optional[datetime]
    created_at: datetime
    
    @field_serializer("service_time", "confirmed_at", "created_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)

    class Config:
        from_attributes = True
