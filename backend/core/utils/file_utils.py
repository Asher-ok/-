import os
import aiofiles
from pathlib import Path
from typing import Optional
import re
import unicodedata
from urllib.parse import quote
from urllib.parse import urlparse, unquote
from core.config import settings


def ensure_upload_dir():
    """确保上传目录存在"""
    upload_path = Path(settings.upload_dir)
    if not upload_path.is_absolute():
        base_dir = getattr(settings, "_base_dir", None)
        project_root = Path(base_dir).resolve() if base_dir else Path(__file__).resolve().parents[2]
        upload_path = (project_root / upload_path).resolve()
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


async def save_upload_file(file_content: bytes, filename: str, subfolder: str = "") -> str:
    """保存上传的文件"""
    upload_path = ensure_upload_dir()
    if subfolder:
        folder_path = upload_path / subfolder
        folder_path.mkdir(parents=True, exist_ok=True)
    else:
        folder_path = upload_path
    
    file_path = folder_path / filename
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    # 返回完整路径，避免因当前工作目录变化导致失败
    return str(file_path)


def delete_file(file_path: str) -> bool:
    """删除文件"""
    try:
        full_path = Path(file_path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_path(relative_path: str) -> Optional[Path]:
    """获取文件的完整路径"""
    if relative_path is None:
        return None
    value = str(relative_path).strip()
    if not value:
        return None

    value = value.split("#", 1)[0].split("?", 1)[0].strip()
    if not value:
        return None

    is_windows_drive = bool(re.match(r"^[A-Za-z]:[\\/]", value))
    is_unc_path = value.startswith("\\\\")
    if not is_windows_drive and not is_unc_path:
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            value = parsed.path or ""
            value = value.split("#", 1)[0].split("?", 1)[0].strip()

    value = unquote(value).strip()
    if not value:
        return None

    direct = Path(value)
    if direct.is_absolute() and direct.exists():
        return direct
    if direct.exists():
        return direct

    upload_dir = ensure_upload_dir()
    normalized = value.replace("\\", "/").lstrip("/")
    if normalized.lower().startswith("uploads/"):
        normalized = normalized[len("uploads/") :]
    candidate = (upload_dir / normalized).resolve()
    if candidate.exists():
        return candidate

    base_dir = getattr(settings, "_base_dir", None)
    project_root = Path(base_dir).resolve() if base_dir else Path(__file__).resolve().parents[2]
    candidate2 = (project_root / direct).resolve()
    if candidate2.exists():
        return candidate2

    return None


def to_ascii_filename(filename: str | None, default: str = "file") -> str:
    value = (filename or "").replace("\r", "").replace("\n", "").strip()
    if not value:
        return default

    value = value.replace("\\", "_").replace("/", "_")
    suffix = Path(value).suffix

    try:
        value.encode("ascii")
        return value
    except UnicodeEncodeError:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_value = re.sub(r'[^A-Za-z0-9._ -]+', "_", ascii_value).strip(" .")
        if not ascii_value:
            return f"{default}{suffix}" if suffix else default
        if suffix and not ascii_value.lower().endswith(suffix.lower()):
            ascii_value = f"{ascii_value}{suffix}"
        return ascii_value


def build_content_disposition(filename: str, disposition: str = "inline") -> str:
    safe_disposition = "attachment" if disposition == "attachment" else "inline"
    ascii_name = to_ascii_filename(filename, default="file")
    utf8_name = (filename or "").replace("\r", "").replace("\n", "").strip()
    if not utf8_name:
        return f'{safe_disposition}; filename="{ascii_name}"'
    encoded = quote(utf8_name, safe="")
    return f'{safe_disposition}; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded}'
