from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from shared.models import Employee, User
from core.auth import verify_password, get_password_hash, create_access_token
from ..schemas.user import UserLogin, Token, EmployeePasswordResetRequest, EmployeePasswordResetConfirm
from datetime import timedelta, datetime, timezone
from core.config import settings
from core.utils.email import send_contact_email
import secrets
from pydantic import TypeAdapter, EmailStr, ValidationError
from pydantic import BaseModel
from typing import List, Optional

from ..dependencies import get_current_admin_user

router = APIRouter(prefix="/api/app/auth", tags=["认证"])


@router.post("/employee/login", response_model=Token)
async def employee_login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """员工登录（仅邮箱+密码）"""
    raw_email = (login_data.username or "").strip()
    if "@" not in raw_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    email_adapter = TypeAdapter(EmailStr)
    try:
        normalized_email = str(email_adapter.validate_python(raw_email)).strip().lower()
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    matched = db.query(Employee).filter(
        func.lower(func.trim(Employee.email)) == normalized_email
    ).all()
    employee = None
    if len(matched) == 1:
        employee = matched[0]
    elif len(matched) > 1:
        password_matched = [
            emp for emp in matched
            if verify_password(login_data.password, getattr(emp, "password_hash", "") or "")
        ]
        if len(password_matched) == 1:
            employee = password_matched[0]
        elif len(password_matched) > 1:
            raise HTTPException(status_code=400, detail="该邮箱绑定多个账号，请联系管理员处理重复邮箱")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(login_data.password, employee.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": employee.id, "type": "employee"},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/employee/password-reset/request")
async def request_employee_password_reset(
    body: EmployeePasswordResetRequest,
    db: Session = Depends(get_db),
):
    raw_email = (str(body.email) or "").strip()
    email_adapter = TypeAdapter(EmailStr)
    try:
        email = str(email_adapter.validate_python(raw_email)).strip().lower()
    except ValidationError:
        raise HTTPException(status_code=400, detail="邮箱无效，请重新输入")

    matched = db.query(Employee).filter(func.lower(func.trim(Employee.email)) == email).all()
    if not matched:
        raise HTTPException(status_code=400, detail="邮箱无效，请重新输入")
    if len(matched) > 1:
        raise HTTPException(status_code=400, detail="该邮箱绑定多个账号，请联系管理员")
    employee = matched[0]

    now = datetime.now(timezone.utc)
    sent_at = getattr(employee, "reset_password_code_sent_at", None)
    if sent_at is not None:
        try:
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=timezone.utc)
        except Exception:
            sent_at = None
    if sent_at is not None and (now - sent_at).total_seconds() < 60:
        raise HTTPException(status_code=429, detail="验证码发送过于频繁，请稍后再试")

    code = f"{secrets.randbelow(100000):05d}"
    expires_at = now + timedelta(minutes=5)

    subject = "Password Reset Verification Code"
    html_body = f"""
<div style="font-family:Arial,Helvetica,sans-serif;line-height:1.6">
  <p>Hello,</p>
  <p>You requested to reset your password. Your verification code is:</p>
  <p style="font-size:20px;font-weight:bold;letter-spacing:2px">{code}</p>
  <p>This code is valid for 5 minutes. If you did not request this, please ignore this email.</p>
</div>
""".strip()
    plain_body = f"Your password reset verification code is: {code} (valid for 5 minutes)."

    try:
        send_contact_email(
            subject=subject,
            html_body=html_body,
            plain_body=plain_body,
            to_emails=[email],
            from_email="enquiry@empowerhub.com.au",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送验证码失败: {str(e)}")

    employee.reset_password_code_hash = get_password_hash(code)
    employee.reset_password_code_expires_at = expires_at
    employee.reset_password_code_sent_at = now
    employee.reset_password_code_attempts = 0
    db.commit()

    return {"message": "验证码已发送"}


@router.post("/employee/password-reset/confirm")
async def confirm_employee_password_reset(
    body: EmployeePasswordResetConfirm,
    db: Session = Depends(get_db),
):
    raw_email = (str(body.email) or "").strip()
    email_adapter = TypeAdapter(EmailStr)
    try:
        email = str(email_adapter.validate_python(raw_email)).strip().lower()
    except ValidationError:
        raise HTTPException(status_code=400, detail="邮箱无效，请重新输入")

    matched = db.query(Employee).filter(func.lower(func.trim(Employee.email)) == email).all()
    if not matched:
        raise HTTPException(status_code=400, detail="邮箱无效，请重新输入")
    if len(matched) > 1:
        raise HTTPException(status_code=400, detail="该邮箱绑定多个账号，请联系管理员处理重复邮箱")
    employee = matched[0]

    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="两次密码不一致")

    code_hash = getattr(employee, "reset_password_code_hash", None)
    expires_at = getattr(employee, "reset_password_code_expires_at", None)
    if not code_hash or not expires_at:
        raise HTTPException(status_code=400, detail="验证码已失效，请重新获取")

    now = datetime.now(timezone.utc)
    try:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    if expires_at < now:
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")

    attempts = int(getattr(employee, "reset_password_code_attempts", 0) or 0)
    if attempts >= 5:
        raise HTTPException(status_code=400, detail="验证码已失效，请重新获取")

    if not verify_password(body.code.strip(), code_hash):
        employee.reset_password_code_attempts = attempts + 1
        db.commit()
        raise HTTPException(status_code=400, detail="验证码错误")

    employee.password_hash = get_password_hash(body.new_password)
    employee.reset_password_code_hash = None
    employee.reset_password_code_expires_at = None
    employee.reset_password_code_sent_at = None
    employee.reset_password_code_attempts = None
    db.commit()

    return {"message": "密码修改成功"}


@router.post("/admin/login", response_model=Token)
async def admin_login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """管理员登录"""
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id, "type": "admin"},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


class AdminEmployeeOption(BaseModel):
    id: str
    name: str
    employee_number: str
    email: Optional[str] = None
    department: Optional[str] = None


class AdminImpersonateRequest(BaseModel):
    employee_id: str


@router.get("/admin/employees", response_model=List[AdminEmployeeOption])
async def admin_list_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    employees = (
        db.query(Employee)
        .order_by(func.lower(func.trim(Employee.name)))
        .all()
    )
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


@router.post("/admin/impersonate", response_model=Token)
async def admin_impersonate_employee(
    body: AdminImpersonateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    employee = db.query(Employee).filter(Employee.id == body.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": employee.id,
            "type": "employee",
            "impersonated_by": current_user.id,
        },
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
