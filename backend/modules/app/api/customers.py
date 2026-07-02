from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from shared.models import Customer, Employee
from ..schemas.customer import CustomerResponse
from ..dependencies import get_current_employee

router = APIRouter(prefix="/api/app/customers", tags=["客户"])


@router.get("", response_model=List[CustomerResponse])
async def get_customers(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取客户列表"""
    customers = db.query(Customer).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取客户详情"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer
