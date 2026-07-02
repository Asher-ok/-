from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from core.database import Base
import uuid


class IncidentTemplate(Base):
    __tablename__ = "incident_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, default="")
    title_i18n = Column(JSON)
    description = Column(Text)
    description_i18n = Column(JSON)
    schema_json = Column(JSON)
    style_json = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
