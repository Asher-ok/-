"""请假请求 API（App 员工端）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional
from datetime import date

from core.database import get_db
from shared.models import LeaveRequest, User, BusinessUnread
from shared.models.update_notification import touch_business_unread
from ..dependencies import get_current_employee
from shared.models import Employee


router = APIRouter(prefix="/api/app", tags=["App-请假"])


class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: Optional[str] = None


@router.get("/leave-requests")
async def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """员工查询自己的请假记录"""
    unread_ids = {
        (r.data_id or "")
        for r in db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_employee.id),
            BusinessUnread.business_code == "leave_request",
            BusinessUnread.is_unread == 1,
        )
        .all()
    }
    items = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == current_employee.id
    ).order_by(LeaveRequest.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "start_date": r.start_date.isoformat() if r.start_date else None,
            "end_date": r.end_date.isoformat() if r.end_date else None,
            "reason": r.reason,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "has_update": str(r.id) in unread_ids,
        }
        for r in items
    ]


@router.post("/leave-requests")
async def create_leave_request(
    body: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """员工提交请假"""
    if body.end_date < body.start_date:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")
    req = LeaveRequest(
        employee_id=current_employee.id,
        start_date=body.start_date,
        end_date=body.end_date,
        reason=body.reason,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    try:
        admin_users = db.query(User).filter(or_(User.is_active == True, User.is_active.is_(None))).all()
        for u in admin_users:
            touch_business_unread(
                db,
                business_code="leave_request",
                receiver_user_id=str(u.id),
                data_id=str(req.id),
                trigger_user_id=str(current_employee.id),
            )
        db.commit()
    except Exception:
        db.rollback()

    return {"id": req.id, "message": "请假申请已提交"}
