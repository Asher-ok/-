"""修改审批请求 API（App 员工端）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any

from core.database import get_db
from shared.models import CorrectionRequest, Task
from ..dependencies import get_current_employee
from shared.models import Employee


router = APIRouter(prefix="/api/app", tags=["App-修改审批"])


class CorrectionRequestCreate(BaseModel):
    task_id: str
    original_data: Optional[dict] = None
    corrected_data: Optional[dict] = None
    reason: Optional[str] = None


@router.post("/correction-requests")
async def create_correction_request(
    body: CorrectionRequestCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """员工提交修改申请"""
    task = db.query(Task).filter(Task.id == body.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权申请修改该任务")
    import json
    req = CorrectionRequest(
        task_id=body.task_id,
        requested_by=current_employee.id,
        original_data=json.dumps(body.original_data, ensure_ascii=False) if body.original_data else None,
        corrected_data=json.dumps(body.corrected_data, ensure_ascii=False) if body.corrected_data else None,
        reason=body.reason,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return {"id": req.id, "message": "修改申请已提交"}
