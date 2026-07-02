"""NDIS 报告 API - 服务使用报告、财务报告"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pathlib import Path

from core.database import get_db
from core.utils.file_utils import ensure_upload_dir
from ..dependencies import get_current_user
from ..services.ndis_report_service import (
    generate_service_usage_report,
    generate_financial_report,
    get_service_usage_data,
    get_financial_data,
)

router = APIRouter(prefix="/api/houtai/ndis-reports", tags=["管理-NDIS报告"])


def _parse_date(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        date_part = val.split("T")[0] if "T" in val else val[:10]
        return datetime.strptime(date_part, "%Y-%m-%d")
    except Exception:
        return None


@router.get("/service-usage/data")
async def get_service_usage_data_api(
    customer_id: Optional[str] = Query(None, description="客户ID"),
    date_start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    ndis_only: bool = Query(True, description="仅NDIS客户"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取服务使用报告数据（JSON）"""
    date_start_dt = _parse_date(date_start)
    date_end_dt = _parse_date(date_end)
    if date_end_dt:
        date_end_dt = datetime(
            date_end_dt.year, date_end_dt.month, date_end_dt.day, 23, 59, 59
        )
    rows, summary = get_service_usage_data(
        db=db,
        customer_id=customer_id,
        date_start=date_start_dt,
        date_end=date_end_dt,
        ndis_only=ndis_only
    )
    return {"rows": rows, "summary": summary}


@router.get("/service-usage")
async def download_service_usage_report(
    customer_id: Optional[str] = Query(None, description="客户ID"),
    date_start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    ndis_only: bool = Query(True, description="仅NDIS客户"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """生成并下载服务使用报告 Excel"""
    date_start_dt = _parse_date(date_start)
    date_end_dt = _parse_date(date_end)
    if date_end_dt:
        date_end_dt = datetime(
            date_end_dt.year, date_end_dt.month, date_end_dt.day, 23, 59, 59
        )

    upload_dir = ensure_upload_dir()
    report_dir = upload_dir / "ndis_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    filename = f"NDIS_Service_Usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = report_dir / filename

    generate_service_usage_report(
        db=db,
        output_path=str(path),
        customer_id=customer_id,
        date_start=date_start_dt,
        date_end=date_end_dt,
        ndis_only=ndis_only
    )
    return FileResponse(
        str(path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/financial/data")
async def get_financial_data_api(
    customer_id: Optional[str] = Query(None, description="客户ID"),
    date_start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    ndis_only: bool = Query(True, description="仅NDIS客户"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取财务报告数据（JSON）"""
    date_start_dt = _parse_date(date_start)
    date_end_dt = _parse_date(date_end)
    if date_end_dt:
        date_end_dt = datetime(
            date_end_dt.year, date_end_dt.month, date_end_dt.day, 23, 59, 59
        )
    rows, summary = get_financial_data(
        db=db,
        customer_id=customer_id,
        date_start=date_start_dt,
        date_end=date_end_dt,
        ndis_only=ndis_only
    )
    return {"rows": rows, "summary": summary}


@router.get("/financial")
async def download_financial_report(
    customer_id: Optional[str] = Query(None, description="客户ID"),
    date_start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    ndis_only: bool = Query(True, description="仅NDIS客户"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """生成并下载财务报告 Excel"""
    date_start_dt = _parse_date(date_start)
    date_end_dt = _parse_date(date_end)
    if date_end_dt:
        date_end_dt = datetime(
            date_end_dt.year, date_end_dt.month, date_end_dt.day, 23, 59, 59
        )

    upload_dir = ensure_upload_dir()
    report_dir = upload_dir / "ndis_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    filename = f"NDIS_Financial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = report_dir / filename

    generate_financial_report(
        db=db,
        output_path=str(path),
        customer_id=customer_id,
        date_start=date_start_dt,
        date_end=date_end_dt,
        ndis_only=ndis_only
    )
    return FileResponse(
        str(path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
