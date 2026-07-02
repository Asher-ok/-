from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import timedelta

from core.database import get_db
from core.config import settings
from core.auth import create_access_token
from shared.models import Employee
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/houtai/admin", tags=["管理-代登录"])


class AdminEmployeeOption(BaseModel):
  id: str
  name: str
  employee_number: str
  email: Optional[str] = None
  department: Optional[str] = None


class AdminImpersonateRequest(BaseModel):
  employee_id: str


class Token(BaseModel):
  access_token: str
  token_type: str = "bearer"


@router.get("/employees", response_model=List[AdminEmployeeOption])
async def admin_list_employees(
  db: Session = Depends(get_db),
  current_user=Depends(get_current_user),
):
  employees = db.query(Employee).order_by(func.lower(func.trim(Employee.name))).all()
  return [
    AdminEmployeeOption(
      id=str(e.id),
      name=e.name,
      employee_number=e.employee_number,
      email=e.email,
      department=getattr(e, "department", None),
    )
    for e in employees
  ]


@router.post("/impersonate", response_model=Token)
async def admin_impersonate_employee(
  body: AdminImpersonateRequest,
  db: Session = Depends(get_db),
  current_user=Depends(get_current_user),
):
  employee = db.query(Employee).filter(Employee.id == body.employee_id).first()
  if not employee:
    raise HTTPException(status_code=404, detail="员工不存在")

  access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
  access_token = create_access_token(
    data={
      "sub": employee.id,
      "type": "employee",
      "impersonated_by": getattr(current_user, "id", None),
    },
    expires_delta=access_token_expires,
  )
  return {"access_token": access_token, "token_type": "bearer"}

