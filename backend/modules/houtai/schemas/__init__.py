"""
后台模块 Schemas
"""
from .employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, QualificationCreate, QualificationResponse, TrainingRecordCreate, TrainingRecordUpdate, TrainingRecordResponse
from .customer import CustomerCreate, CustomerUpdate, CustomerResponse
from .task import TaskCreate, TaskUpdate, TaskResponse, TaskStatus
from .questionnaire import (
    QuestionnaireCreate, QuestionnaireUpdate, QuestionnaireResponse,
    QuestionCreate, QuestionUpdate, QuestionResponse,
    QuestionnaireSubmissionListItem, QuestionnaireSubmissionDetail
)
from .document import DocumentCreate, DocumentResponse
from .invoice import InvoiceCreate, InvoiceResponse, InvoiceItemCreate, InvoiceItemResponse, InvoiceGenerateRequest
from .user import UserCreate, UserLogin, UserResponse, Token

__all__ = [
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "QualificationCreate",
    "QualificationResponse",
    "TrainingRecordCreate",
    "TrainingRecordUpdate",
    "TrainingRecordResponse",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskStatus",
    "QuestionnaireCreate",
    "QuestionnaireUpdate",
    "QuestionnaireResponse",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "QuestionnaireSubmissionListItem",
    "QuestionnaireSubmissionDetail",
    "DocumentCreate",
    "DocumentResponse",
    "InvoiceCreate",
    "InvoiceResponse",
    "InvoiceItemCreate",
    "InvoiceItemResponse",
    "InvoiceGenerateRequest",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
]
