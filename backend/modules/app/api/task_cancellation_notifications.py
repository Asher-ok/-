from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from core.database import get_db
from shared.models import TaskCancellationNotification, Task, Customer, Employee
from ..schemas.task_cancellation_notification import TaskCancellationNotificationResponse
from ..dependencies import get_current_employee
from datetime import datetime

router = APIRouter(prefix="/api/app/task-cancellation-notifications", tags=["任务取消通知"])


@router.get("", response_model=List[TaskCancellationNotificationResponse])
async def get_cancellation_notifications(
    is_confirmed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取员工的任务取消通知列表"""
    query = db.query(TaskCancellationNotification).options(
        joinedload(TaskCancellationNotification.task).joinedload(Task.customer)
    ).filter(
        TaskCancellationNotification.employee_id == current_employee.id
    ).order_by(TaskCancellationNotification.created_at.desc())
    
    if is_confirmed is not None:
        query = query.filter(TaskCancellationNotification.is_confirmed == is_confirmed)
    
    notifications = query.all()
    
    return [
        TaskCancellationNotificationResponse(
            id=n.id,
            task_id=n.task_id,
            task_title=n.task.title if n.task else "",
            customer_name=n.task.customer.name if n.task and n.task.customer else "",
            service_time=n.task.service_time if n.task else datetime.utcnow(),
            cancel_reason=n.cancel_reason,
            is_confirmed=n.is_confirmed,
            confirmed_at=n.confirmed_at,
            created_at=n.created_at
        )
        for n in notifications
    ]


@router.get("/unconfirmed-count")
async def get_unconfirmed_count(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取未确认的取消通知数量"""
    count = db.query(TaskCancellationNotification).filter(
        TaskCancellationNotification.employee_id == current_employee.id,
        TaskCancellationNotification.is_confirmed == False
    ).count()
    
    return {"count": count}


@router.get("/{notification_id}", response_model=TaskCancellationNotificationResponse)
async def get_cancellation_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """获取单条取消通知详情"""
    notification = db.query(TaskCancellationNotification).options(
        joinedload(TaskCancellationNotification.task).joinedload(Task.customer)
    ).filter(
        TaskCancellationNotification.id == notification_id,
        TaskCancellationNotification.employee_id == current_employee.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    return TaskCancellationNotificationResponse(
        id=notification.id,
        task_id=notification.task_id,
        task_title=notification.task.title if notification.task else "",
        customer_name=notification.task.customer.name if notification.task and notification.task.customer else "",
        service_time=notification.task.service_time if notification.task else datetime.utcnow(),
        cancel_reason=notification.cancel_reason,
        is_confirmed=notification.is_confirmed,
        confirmed_at=notification.confirmed_at,
        created_at=notification.created_at
    )


@router.post("/{notification_id}/confirm", response_model=TaskCancellationNotificationResponse)
async def confirm_cancellation_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """确认取消通知"""
    notification = db.query(TaskCancellationNotification).options(
        joinedload(TaskCancellationNotification.task).joinedload(Task.customer)
    ).filter(
        TaskCancellationNotification.id == notification_id,
        TaskCancellationNotification.employee_id == current_employee.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    if notification.is_confirmed:
        raise HTTPException(status_code=400, detail="该通知已确认")
    
    notification.is_confirmed = True
    notification.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    
    return TaskCancellationNotificationResponse(
        id=notification.id,
        task_id=notification.task_id,
        task_title=notification.task.title if notification.task else "",
        customer_name=notification.task.customer.name if notification.task and notification.task.customer else "",
        service_time=notification.task.service_time if notification.task else datetime.utcnow(),
        cancel_reason=notification.cancel_reason,
        is_confirmed=notification.is_confirmed,
        confirmed_at=notification.confirmed_at,
        created_at=notification.created_at
    )
