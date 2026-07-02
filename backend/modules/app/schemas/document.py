from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


class DocumentCreate(BaseModel):
    task_id: str
    file_type: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    task_id: str
    file_url: str
    file_type: Optional[str]
    uploaded_at: datetime
    uploaded_by: Optional[str]
    
    @field_serializer("uploaded_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True
