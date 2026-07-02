import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from core.database import Base


class TemplateFile(Base):
    __tablename__ = "template_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_name = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    update_time = Column(DateTime(timezone=True), onupdate=func.now())
