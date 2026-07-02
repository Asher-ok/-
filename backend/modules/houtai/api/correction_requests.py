"""修改审批请求 API（后台管理）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from core.database import get_db
from shared.models import CorrectionRequest, Task
from ..dependencies import get_current_user
from .tasks import recalc_customer_weekly_served_hours

router = APIRouter(prefix="/api/houtai/correction-requests", tags=["管理-修改审批"])


@router.get("")
async def list_correction_requests(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """修改审批列表"""
    q = db.query(CorrectionRequest)
    if status:
        q = q.filter(CorrectionRequest.status == status)
    items = q.order_by(CorrectionRequest.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "task_id": r.task_id,
            "requested_by": r.requested_by,
            "reason": r.reason,
            "status": r.status,
            "original_data": json.loads(r.original_data) if r.original_data else None,
            "corrected_data": json.loads(r.corrected_data) if r.corrected_data else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in items
    ]


@router.post("/{request_id}/approve")
async def approve_correction(
    request_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """批准修改"""
    from shared.models.task import TaskServiceItem
    req = db.query(CorrectionRequest).filter(CorrectionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="修改请求不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="该请求已处理")
    task = db.query(Task).filter(Task.id == req.task_id).first()
    if task and req.corrected_data:
        try:
            data = json.loads(req.corrected_data)
        except Exception:
            data = None
        if isinstance(data, dict):
            if "service_plans" in data:
                task.service_plans = data.get("service_plans")
            if "service_items" in data:
                # Replace existing service items
                db.query(TaskServiceItem).filter(TaskServiceItem.task_id == task.id).delete()
                db.flush()
                for item_data in data.get("service_items"):
                    new_item = TaskServiceItem(
                        task_id=task.id,
                        level1_id=item_data.get("level1_id"),
                        level2_id=item_data.get("level2_id"),
                        level3_id=item_data.get("level3_id"),
                        service_code=item_data.get("service_code"),
                        unit=item_data.get("unit"),
                        unit_price=item_data.get("unit_price") or 0,
                        quantity=item_data.get("quantity") or 0,
                        amount=item_data.get("amount") or 0,
                        remark=item_data.get("remark"),
                        service_time_start=item_data.get("service_time_start"),
                        service_time_end=item_data.get("service_time_end"),
                    )
                    db.add(new_item)
            if "employee_note" in data:
                task.employee_note = data.get("employee_note")
            if "questionnaire_data" in data:
                task.questionnaire_data = data.get("questionnaire_data")
        else:
            task.questionnaire_data = json.loads(req.corrected_data)
    req.status = "approved"
    req.approver_id = current_user.id
    db.commit()
    if task:
        try:
            recalc_customer_weekly_served_hours(db, task.customer_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error recalculating weekly served hours in correction_requests: {e}", exc_info=True)
    return {"message": "已批准"}


@router.post("/{request_id}/reject")
async def reject_correction(
    request_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """拒绝修改"""
    req = db.query(CorrectionRequest).filter(CorrectionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="修改请求不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="该请求已处理")
    req.status = "rejected"
    req.approver_id = current_user.id
    db.commit()
    return {"message": "已拒绝"}
