from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


class TaskQuestionnaire(Base):
    __tablename__ = "task_questionnaires"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    questionnaire_id = Column(String, ForeignKey("questionnaires.id"), nullable=False)
    is_required = Column(Boolean, default=True)
    is_filled = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", backref="task_questionnaires")
    questionnaire = relationship("Questionnaire")


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    title_i18n = Column(JSON)
    description = Column(Text)
    description_i18n = Column(JSON)
    is_active = Column(Boolean, default=True)
    customer_type = Column(String)
    created_at = Column(String, server_default=func.now())
    updated_at = Column(String, onupdate=func.now())

    questions = relationship(
        "Question",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    questionnaire_id = Column(String, ForeignKey("questionnaires.id"), nullable=False)
    title = Column(String, nullable=False)
    title_i18n = Column(JSON)
    type = Column(String, nullable=False)
    required = Column(Boolean, default=False)
    conditional_required = Column(Boolean, default=False)
    depends_on = Column(Text)
    options = Column(JSON)
    placeholder = Column(String)
    hint = Column(String)
    order_index = Column(Integer, default=0)
    created_at = Column(String, server_default=func.now())

    questionnaire = relationship("Questionnaire", back_populates="questions")


class QuestionnaireResponse(Base):
    __tablename__ = "questionnaire_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    questionnaire_id = Column(String, ForeignKey("questionnaires.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    answers = Column(JSON, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    questionnaire = relationship("Questionnaire")
    task = relationship("Task")
    customer = relationship("Customer")
    employee = relationship("Employee")
