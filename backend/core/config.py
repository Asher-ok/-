from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    # 数据库配置
    _base_dir = Path(__file__).resolve().parent.parent
    database_url: str = f"sqlite:///{_base_dir / 'aozhou.db'}"
    
    # 应用配置
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    init_db_on_startup: bool = False

    sign_frontend_base_url: Optional[str] = None
    
    # 文件存储
    upload_dir: str = "./uploads"
    max_upload_size: int = 10485760  # 10MB

    # LibreOffice（Word 转 PDF）
    SOFFICE_PATH: Optional[str] = "/usr/bin/soffice"
    # SOFFICE_PATH: Optional[str] = "D:/develop/libreoffice/program/soffice.com"
    
    # 邮件配置
    smtp_host: Optional[str] = "176.97.68.115"
    # 使用465端口（SSL加密）
    smtp_port: int = 465
    smtp_user: Optional[str] = "enquiry@empowerhub.com.au"
    # 确认这是正确的邮箱密码/授权码（如果发送失败，先核对这个）
    smtp_password: Optional[str] = "Zhuyu12345."
    smtp_from_email: Optional[str] = "enquiry@empowerhub.com.au"
    smtp_save_to_sent: bool = True
    imap_host: Optional[str] = None
    imap_port: int = 993
    imap_use_ssl: bool = True
    imap_sent_folder: Optional[str] = None

    contact_to_emails: str = "enquiry@empowerhub.com.au"
    contact_cc_emails: Optional[str] = None
    
    # 发票配置
    invoice_company_name: str = "EMPOWER HUB"
    invoice_abn: str = "42 679 637 426"
    invoice_address: str = "UNIT FGL-Office, 1/385 Sherwood Rd, ROCKLEA, QLD 4106"
    invoice_phone: str = "0406 888 667"
    invoice_email: str = "Zhaohmei22@hotmail.com"
    invoice_bank_name: str = "Australia and New Zealand Banking Group Limited (ANZ Bank)"
    invoice_bank_branch: str = "Sh 1 Underwood Market Place, Underwood, QLD 4119"
    invoice_account_name: str = "EMPOWER HUB PTY LTD"
    invoice_bsb: str = "014-257"
    invoice_account_number: str = "664012151"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
