from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmployeePasswordResetRequest(BaseModel):
    email: str


class EmployeePasswordResetConfirm(BaseModel):
    email: str
    code: str = Field(min_length=4, max_length=12)
    new_password: str = Field(min_length=6, max_length=64)
    confirm_password: str = Field(min_length=6, max_length=64)


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True
