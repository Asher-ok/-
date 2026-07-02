from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import or_
from pydantic import BaseModel
from core.database import get_db
from shared.models import Qualification, Employee, SystemSetting
from ..dependencies import get_current_user
from ..schemas.employee import QualificationListItem, QualificationUpdate, QualificationResponse

router = APIRouter(prefix="/api/houtai/qualifications", tags=["管理-资质"])

EXPIRING_SETTING_KEY = "qualification_expiring_days"
DEFAULT_EXPIRING_DAYS = 30


class ExpiringSettingPayload(BaseModel):
    days: int


def get_expiring_days(db: Session) -> int:
    setting = db.query(SystemSetting).filter(SystemSetting.key == EXPIRING_SETTING_KEY).first()
    if setting and setting.value.isdigit():
        return max(int(setting.value), 1)
    return DEFAULT_EXPIRING_DAYS


def to_list_item(qualification: Qualification, employee: Employee) -> QualificationListItem:
    return QualificationListItem(
        id=qualification.id,
        employee_id=employee.id,
        employee_name=employee.name,
        employee_number=employee.employee_number,
        name=qualification.name,
        certificate_number=qualification.certificate_number,
        certificate_url=qualification.certificate_url,
        obtained_date=qualification.obtained_date,
        expiry_date=qualification.expiry_date,
        issuing_authority=qualification.issuing_authority
    )


@router.get("/expiring", response_model=List[QualificationListItem])
async def get_expiring_qualifications(
    days: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取即将到期的资质（默认30天内）"""
    effective_days = days if days is not None else get_expiring_days(db)
    cutoff_date = datetime.utcnow() + timedelta(days=effective_days)
    rows = db.query(Qualification, Employee).join(Employee, Qualification.employee_id == Employee.id).filter(
        Qualification.expiry_date.isnot(None),
        Qualification.expiry_date <= cutoff_date,
        Qualification.expiry_date >= datetime.utcnow()
    ).order_by(Qualification.expiry_date.asc()).all()
    return [to_list_item(qualification, employee) for qualification, employee in rows]


@router.get("/expired", response_model=List[QualificationListItem])
async def get_expired_qualifications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取已过期的资质"""
    rows = db.query(Qualification, Employee).join(Employee, Qualification.employee_id == Employee.id).filter(
        Qualification.expiry_date.isnot(None),
        Qualification.expiry_date < datetime.utcnow()
    ).order_by(Qualification.expiry_date.desc()).all()
    return [to_list_item(qualification, employee) for qualification, employee in rows]


@router.get("/expiring-settings")
async def get_expiring_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取到期提醒设置"""
    return {"days": get_expiring_days(db)}


@router.put("/expiring-settings")
async def update_expiring_settings(
    payload: ExpiringSettingPayload,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新到期提醒设置"""
    if payload.days <= 0:
        raise HTTPException(status_code=400, detail="提醒天数必须大于0")
    setting = db.query(SystemSetting).filter(SystemSetting.key == EXPIRING_SETTING_KEY).first()
    if setting:
        setting.value = str(payload.days)
    else:
        setting = SystemSetting(key=EXPIRING_SETTING_KEY, value=str(payload.days))
        db.add(setting)
    db.commit()
    return {"days": payload.days}


@router.get("", response_model=List[QualificationListItem])
async def get_all_qualifications(
    field: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取所有资质，支持单条件模糊搜索"""
    query = db.query(Qualification, Employee).join(Employee, Qualification.employee_id == Employee.id)
    keyword_value = (keyword or "").strip()
    if keyword_value:
        like_value = f"%{keyword_value}%"
        if field == "employee_name":
            query = query.filter(Employee.name.ilike(like_value))
        elif field == "qualification_name":
            query = query.filter(Qualification.name.ilike(like_value))
        elif field == "certificate_number":
            query = query.filter(Qualification.certificate_number.ilike(like_value))
        elif field == "employee_number":
            query = query.filter(Employee.employee_number.ilike(like_value))
        else:
            query = query.filter(
                or_(
                    Employee.name.ilike(like_value),
                    Employee.employee_number.ilike(like_value),
                    Qualification.name.ilike(like_value),
                    Qualification.certificate_number.ilike(like_value)
                )
            )
    rows = query.order_by(Qualification.created_at.desc()).all()
    return [to_list_item(qualification, employee) for qualification, employee in rows]


@router.post("/upload")
async def upload_qualification(
    employee_id: str = Form(...),
    name: str = Form(...),
    certificate_number: str = Form(None),
    obtained_date: str = Form(...),
    expiry_date: str = Form(None),
    issuing_authority: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """上传员工证书并创建资质记录"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    file_content = await file.read()
    file_mime = file.content_type or "application/octet-stream"

    qualification = Qualification(
        employee_id=employee_id,
        name=name,
        certificate_number=certificate_number,
        certificate_blob=file_content,
        certificate_mime=file_mime,
        obtained_date=datetime.fromisoformat(obtained_date),
        expiry_date=datetime.fromisoformat(expiry_date) if expiry_date else None,
        issuing_authority=issuing_authority
    )
    db.add(qualification)
    db.commit()
    db.refresh(qualification)
    qualification.certificate_url = f"/api/houtai/qualifications/{qualification.id}/certificate"
    db.commit()
    return qualification


@router.put("/{qualification_id}", response_model=QualificationListItem)
async def update_qualification(
    qualification_id: str,
    payload: QualificationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新资质信息（不更换文件）"""
    qualification = db.query(Qualification).filter(Qualification.id == qualification_id).first()
    if not qualification:
        raise HTTPException(status_code=404, detail="资质不存在")
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(qualification, key, value)
    db.commit()
    db.refresh(qualification)
    employee = db.query(Employee).filter(Employee.id == qualification.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    return to_list_item(qualification, employee)


@router.delete("/{qualification_id}", status_code=204)
async def delete_qualification(
    qualification_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除资质"""
    qualification = db.query(Qualification).filter(Qualification.id == qualification_id).first()
    if not qualification:
        raise HTTPException(status_code=404, detail="资质不存在")
    db.delete(qualification)
    db.commit()
    return None


@router.get("/{qualification_id}/certificate")
async def get_qualification_certificate(
    qualification_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取证书文件"""
    qualification = db.query(Qualification).filter(Qualification.id == qualification_id).first()
    if not qualification or not qualification.certificate_blob:
        raise HTTPException(status_code=404, detail="证书不存在")
    return Response(
        content=qualification.certificate_blob,
        media_type=qualification.certificate_mime or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename=certificate_{qualification_id}"
        }
    )

