"""请假请求 API（后台管理）"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from pydantic import BaseModel

from core.database import get_db
from shared.models import LeaveRequest, Employee, BusinessUnread
from shared.models.update_notification import touch_business_unread
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/houtai/leave-requests", tags=["管理-请假"])


class LeaveApproveReject(BaseModel):
    reason: str | None = None


@router.get("")
async def list_leave_requests(
    status: str | None = Query(None),
    employee_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """请假列表"""
    unread_ids = {
        (r.data_id or "")
        for r in db.query(BusinessUnread)
        .filter(
            BusinessUnread.receiver_user_id == str(current_user.id),
            BusinessUnread.business_code == "leave_request",
            BusinessUnread.is_unread == 1,
        )
        .all()
    }
    q = db.query(LeaveRequest)
    if status:
        q = q.filter(LeaveRequest.status == status)
    if employee_id:
        q = q.filter(LeaveRequest.employee_id == employee_id)
    items = q.order_by(LeaveRequest.created_at.desc()).all()
    result = []
    for r in items:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
        result.append({
            "id": r.id,
            "employee_id": r.employee_id,
            "employee_name": emp.name if emp else None,
            "start_date": r.start_date.isoformat() if r.start_date else None,
            "end_date": r.end_date.isoformat() if r.end_date else None,
            "reason": r.reason,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "has_update": str(r.id) in unread_ids,
        })
    return result


@router.post("/{request_id}/approve")
async def approve_leave(
    request_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """批准请假"""
    req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="请假请求不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="该请求已处理")
    req.status = "approved"
    req.approver_id = current_user.id
    db.commit()
    try:
        touch_business_unread(
            db,
            business_code="leave_request",
            receiver_user_id=str(req.employee_id),
            data_id=str(req.id),
            trigger_user_id=str(current_user.id),
        )
        db.commit()
    except Exception:
        db.rollback()
    return {"message": "已批准"}


@router.post("/{request_id}/reject")
async def reject_leave(
    request_id: str,
    body: LeaveApproveReject | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """拒绝请假"""
    req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="请假请求不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="该请求已处理")
    req.status = "rejected"
    req.approver_id = current_user.id
    if body and body.reason:
        req.reason = (req.reason or "") + "\n[拒绝原因] " + str(body.reason)
    db.commit()
    try:
        touch_business_unread(
            db,
            business_code="leave_request",
            receiver_user_id=str(req.employee_id),
            data_id=str(req.id),
            trigger_user_id=str(current_user.id),
        )
        db.commit()
    except Exception:
        db.rollback()
    return {"message": "已拒绝"}
