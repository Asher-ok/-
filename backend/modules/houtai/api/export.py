from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from core.database import get_db
from shared.models import Task, TaskPhoto
from ..dependencies import get_current_user
from core.utils.file_utils import ensure_upload_dir
import zipfile
import json
import os
from pathlib import Path
from datetime import datetime
import base64
import re

router = APIRouter(prefix="/api/houtai/export", tags=["管理-导出"])


@router.get("/task/{task_id}/materials")
async def export_task_materials(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """导出任务的所有审核资料（ZIP文件）"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 创建临时ZIP文件
    upload_dir = ensure_upload_dir()
    zip_filename = f"task_{task_id}_materials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = upload_dir / zip_filename
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加问卷数据
        if task.questionnaire_data:
            questionnaire_json = json.dumps(task.questionnaire_data, ensure_ascii=False, indent=2)
            zipf.writestr("questionnaire.json", questionnaire_json.encode('utf-8'))
        
        # 添加签名图片
        if task.signature_blob:
            zipf.writestr("signature.png", task.signature_blob)
        elif task.signature_image_url and isinstance(task.signature_image_url, str):
            if task.signature_image_url.startswith("data:image"):
                match = re.match(r"^data:(.+?);base64,(.+)$", task.signature_image_url)
                if match:
                    zipf.writestr("signature.png", base64.b64decode(match.group(2)))
            else:
                signature_path = Path(task.signature_image_url)
                if signature_path.exists():
                    zipf.write(signature_path, "signature.png")
        
        # 添加照片
        if task.photos:
            for idx, photo in enumerate(task.photos):
                zipf.writestr(f"photo_{idx + 1}.jpg", photo.photo_blob)
        elif task.photo_urls:
            for idx, photo_url in enumerate(task.photo_urls):
                photo_path = Path(photo_url)
                if photo_path.exists():
                    zipf.write(photo_path, f"photo_{idx + 1}.jpg")
        
        # 添加任务信息
        task_info = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "service_time": task.service_time.isoformat() if task.service_time else None,
            "status": task.status.value,
            "customer": {
                "name": task.customer.name,
                "phone": task.customer.phone,
                "address": task.customer.address
            } if task.customer else None
        }
        task_json = json.dumps(task_info, ensure_ascii=False, indent=2)
        zipf.writestr("task_info.json", task_json.encode('utf-8'))
    
    return FileResponse(
        str(zip_path),
        filename=zip_filename,
        media_type="application/zip"
    )

