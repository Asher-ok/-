"""事故报告 API（后台管理）"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import json
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db
from shared.models import IncidentReport, Task, Customer, Employee, Questionnaire, IncidentTemplate
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/houtai/incident-reports", tags=["管理-事故报告"])


class IncidentReportUpsert(BaseModel):
    task_id: str
    incident_type: str | None = None
    description: str | None = None
    occurred_at: datetime | None = None
    template_id: str | None = None
    report_data: dict | None = None


def _parse_report_data(raw):
    if not raw:
        return None
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return None


def _serialize_report(r: IncidentReport):
    return {
        "id": r.id,
        "task_id": r.task_id,
        "customer_id": r.customer_id,
        "employee_id": r.employee_id,
        "incident_type": r.incident_type,
        "description": r.description,
        "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
        "template_id": getattr(r, "template_id", None),
        "report_data": _parse_report_data(r.report_data),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("")
async def list_incident_reports(
    task_id: str | None = Query(None),
    customer_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """事故报告列表，支持按 task_id、customer_id 筛选"""
    q = db.query(IncidentReport)
    if task_id:
        q = q.filter(IncidentReport.task_id == task_id)
    if customer_id:
        q = q.filter(IncidentReport.customer_id == customer_id)
    reports = q.order_by(IncidentReport.created_at.desc()).all()
    return [_serialize_report(r) for r in reports]


@router.get("/submissions")
async def list_incident_report_submissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order_desc = str(sort).lower() != "asc"
    base = (
        db.query(
            IncidentReport,
            Task.title.label("task_title"),
            Customer.name.label("customer_name"),
            Employee.name.label("employee_name"),
            Questionnaire.title.label("questionnaire_title"),
            IncidentTemplate.title.label("template_title"),
        )
        .join(Task, Task.id == IncidentReport.task_id)
        .join(Customer, Customer.id == Task.customer_id)
        .outerjoin(Employee, Employee.id == IncidentReport.employee_id)
        .outerjoin(Questionnaire, Questionnaire.id == Task.questionnaire_id)
        .outerjoin(IncidentTemplate, IncidentTemplate.id == IncidentReport.template_id)
    )
    total = base.count()
    q = base.order_by(
        IncidentReport.created_at.desc() if order_desc else IncidentReport.created_at.asc()
    )
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for r, task_title, customer_name, employee_name, questionnaire_title, template_title in rows:
        items.append({
            "id": r.id,
            "template_id": getattr(r, "template_id", None),
            "template_title": template_title or "",
            "questionnaire_title": questionnaire_title or "",
            "customer_id": r.customer_id,
            "customer_name": customer_name or "",
            "employee_id": r.employee_id,
            "employee_name": employee_name or "",
            "task_id": r.task_id,
            "task_title": task_title or "",
            "submitted_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
        })
    return {"items": items, "total": total}


@router.get("/submissions/{report_id}")
async def get_incident_report_submission(
    report_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    task = db.query(Task).filter(Task.id == report.task_id).first()
    customer = db.query(Customer).filter(Customer.id == report.customer_id).first()
    employee = db.query(Employee).filter(Employee.id == report.employee_id).first() if report.employee_id else None
    template = db.query(IncidentTemplate).filter(IncidentTemplate.id == getattr(report, "template_id", None)).first() if getattr(report, "template_id", None) else None
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == getattr(task, "questionnaire_id", None)).first() if task and getattr(task, "questionnaire_id", None) else None
    return {
        "id": report.id,
        "template_id": getattr(report, "template_id", None),
        "template_title": template.title if template else "",
        "questionnaire_title": questionnaire.title if questionnaire else "",
        "customer_id": report.customer_id,
        "customer_name": customer.name if customer else "",
        "employee_id": report.employee_id,
        "employee_name": employee.name if employee else "",
        "task_id": report.task_id,
        "task_title": task.title if task else "",
        "submitted_at": report.created_at.isoformat() if getattr(report, "created_at", None) else None,
        "incident_type": report.incident_type,
        "description": report.description,
        "occurred_at": report.occurred_at.isoformat() if report.occurred_at else None,
        "report_data": _parse_report_data(report.report_data),
    }


@router.post("")
async def create_incident_report(
    body: IncidentReportUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == body.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    report = IncidentReport(
        task_id=body.task_id,
        customer_id=task.customer_id,
        employee_id=task.assigned_employee_id,
        incident_type=body.incident_type,
        description=body.description,
        occurred_at=body.occurred_at,
        template_id=body.template_id,
        report_data=json.dumps(body.report_data, ensure_ascii=False) if body.report_data else None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _serialize_report(report)


@router.put("/{report_id}")
async def update_incident_report(
    report_id: str,
    body: IncidentReportUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="事故报告不存在")
    task = db.query(Task).filter(Task.id == body.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    report.task_id = body.task_id
    report.customer_id = task.customer_id
    report.employee_id = task.assigned_employee_id
    report.incident_type = body.incident_type
    report.description = body.description
    report.occurred_at = body.occurred_at
    report.template_id = body.template_id
    report.report_data = json.dumps(body.report_data, ensure_ascii=False) if body.report_data else None
    db.commit()
    db.refresh(report)
    return _serialize_report(report)


@router.delete("/{report_id}")
async def delete_incident_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="事故报告不存在")
    db.delete(report)
    db.commit()
    return {"message": "事故报告已删除"}
