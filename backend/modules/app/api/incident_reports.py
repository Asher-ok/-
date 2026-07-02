"""事故报告 API（App 员工端）"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import json

from core.database import get_db
from shared.models import IncidentReport, Task, IncidentTemplate
from ..dependencies import get_current_employee
from shared.models import Employee


router = APIRouter(prefix="/api/app", tags=["App-事故报告"])


class IncidentReportCreate(BaseModel):
    task_id: str
    incident_type: Optional[str] = None
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None
    template_id: Optional[str] = None
    report_data: Optional[dict] = None


@router.get("/tasks/{task_id}/incident-report")
async def get_task_incident_report(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """查询任务是否已有事故报告"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看该任务")
    report = db.query(IncidentReport).filter(IncidentReport.task_id == task_id).first()
    if not report:
        return None
    return {
        "id": report.id,
        "task_id": report.task_id,
        "incident_type": report.incident_type,
        "description": report.description,
        "occurred_at": report.occurred_at.isoformat() if report.occurred_at else None,
        "template_id": getattr(report, "template_id", None),
        "report_data": json.loads(report.report_data) if report.report_data else None,
    }


@router.get("/tasks/{task_id}/incident-report/template")
async def get_task_incident_report_template(
    task_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权查看该任务")

    chosen_id = getattr(task, "incident_template_id", None)
    template = None
    if chosen_id:
        template = db.query(IncidentTemplate).filter(
            IncidentTemplate.id == chosen_id, IncidentTemplate.is_active == True
        ).first()
    if not template:
        template = db.query(IncidentTemplate).filter(IncidentTemplate.is_active == True).first()
    if not template:
        return None
    return {
        "id": template.id,
        "title": template.title,
        "title_i18n": template.title_i18n,
        "description": template.description,
        "description_i18n": template.description_i18n,
        "schema_json": template.schema_json,
        "style_json": template.style_json,
        "is_active": bool(template.is_active),
    }


@router.post("/incident-reports")
async def create_incident_report(
    body: IncidentReportCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    """员工提交事故报告"""
    task = db.query(Task).filter(Task.id == body.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.assigned_employee_id and task.assigned_employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="无权提交该任务事故报告")

    template_id = body.template_id or getattr(task, "incident_template_id", None)
    template = None
    if template_id:
        template = db.query(IncidentTemplate).filter(
            IncidentTemplate.id == template_id, IncidentTemplate.is_active == True
        ).first()
    if not template:
        template = db.query(IncidentTemplate).filter(IncidentTemplate.is_active == True).first()

    report = IncidentReport(
        task_id=body.task_id,
        customer_id=task.customer_id,
        employee_id=current_employee.id,
        incident_type=body.incident_type,
        description=body.description,
        occurred_at=body.occurred_at,
        template_id=template.id if template else None,
        report_data=json.dumps(body.report_data, ensure_ascii=False) if body.report_data else None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "template_id": getattr(report, "template_id", None), "message": "事故报告已提交"}
