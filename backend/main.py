"""
应用主入口
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import base64
import re
import mimetypes

from core.database import Base, engine, close_db_connections
from core.config import settings

# 导入模块初始化函数
from modules.guanwang import init_guanwang_module
from modules.app import init_app_module
from modules.houtai import init_houtai_module
from modules.public_api import init_public_module

# 导入中间件
from middleware import (
    setup_cors,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
    LoggingMiddleware,
    ApiPrefixRewriteMiddleware
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def ensure_employee_password_column():
    """确保员工表包含密码列，并为历史数据补默认密码"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(employees)")).fetchall()
            has_password = any(col[1] == "password_hash" for col in columns)
            if not has_password:
                conn.execute(text("ALTER TABLE employees ADD COLUMN password_hash VARCHAR"))

            from core.auth import get_password_hash
            default_hash = get_password_hash("123456")
            conn.execute(
                text(
                    "UPDATE employees SET password_hash = :password_hash "
                    "WHERE password_hash IS NULL OR password_hash = ''"
                ),
                {"password_hash": default_hash}
            )
            conn.commit()
            if not has_password:
                logger.info("已补充 employees.password_hash 字段并设置默认密码")
    except Exception as e:
        logger.error(f"修复员工密码字段失败: {e}")


def ensure_employee_password_reset_columns():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(employees)")).fetchall()
            existing = {col[1] for col in columns}

            if "reset_password_code_hash" not in existing:
                conn.execute(text("ALTER TABLE employees ADD COLUMN reset_password_code_hash VARCHAR"))
            if "reset_password_code_expires_at" not in existing:
                conn.execute(text("ALTER TABLE employees ADD COLUMN reset_password_code_expires_at DATETIME"))
            if "reset_password_code_sent_at" not in existing:
                conn.execute(text("ALTER TABLE employees ADD COLUMN reset_password_code_sent_at DATETIME"))
            if "reset_password_code_attempts" not in existing:
                conn.execute(text("ALTER TABLE employees ADD COLUMN reset_password_code_attempts INTEGER"))

            conn.commit()
    except Exception as e:
        logger.error(f"修复员工忘记密码字段失败: {e}")


def ensure_employee_account_status_column():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(employees)")).fetchall()
            existing = {col[1] for col in columns}
            if "account_status" not in existing:
                conn.execute(text("ALTER TABLE employees ADD COLUMN account_status VARCHAR"))

            conn.execute(
                text(
                    "UPDATE employees SET account_status = :account_status "
                    "WHERE account_status IS NULL OR account_status = ''"
                ),
                {"account_status": "normal"},
            )
            conn.commit()
    except Exception as e:
        logger.error(f"修复员工账号状态字段失败: {e}")


def ensure_employee_email_unique_index():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
            ).fetchone()
            if not table:
                return

            try:
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ux_employees_email_norm "
                        "ON employees (lower(trim(email))) "
                        "WHERE email IS NOT NULL AND trim(email) <> ''"
                    )
                )
                conn.commit()
            except Exception as index_exc:
                logger.error(f"创建员工邮箱唯一索引失败（可能存在重复邮箱脏数据）: {index_exc}")
    except Exception as e:
        logger.error(f"修复员工邮箱唯一索引失败: {e}")

def migrate_customers_schema():
    """迁移客户表字段：增加 introduction，移除 participant_name"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(customers)")).fetchall()
            has_introduction = any(col[1] == "introduction" for col in columns)
            has_participant = any(col[1] == "participant_name" for col in columns)

            if has_participant:
                conn.execute(text("PRAGMA foreign_keys=OFF"))
                conn.execute(text("""
                    CREATE TABLE customers_new (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        address TEXT NOT NULL,
                        email TEXT,
                        notes TEXT,
                        ndis_number TEXT,
                        introduction TEXT,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
                if has_introduction:
                    conn.execute(text("""
                        INSERT INTO customers_new (
                            id, name, phone, address, email, notes, ndis_number, introduction, created_at, updated_at
                        )
                        SELECT id, name, phone, address, email, notes, ndis_number, introduction, created_at, updated_at
                        FROM customers
                    """))
                else:
                    conn.execute(text("""
                        INSERT INTO customers_new (
                            id, name, phone, address, email, notes, ndis_number, introduction, created_at, updated_at
                        )
                        SELECT id, name, phone, address, email, notes, ndis_number, NULL, created_at, updated_at
                        FROM customers
                    """))
                conn.execute(text("DROP TABLE customers"))
                conn.execute(text("ALTER TABLE customers_new RENAME TO customers"))
                conn.execute(text("PRAGMA foreign_keys=ON"))
                conn.commit()
                logger.info("已移除 customers.participant_name 字段并补充 introduction")
                return

            if not has_introduction:
                conn.execute(text("ALTER TABLE customers ADD COLUMN introduction TEXT"))
                conn.commit()
                logger.info("已补充 customers.introduction 字段")
    except Exception as e:
        logger.error(f"迁移客户字段失败: {e}")


def ensure_customer_extra_columns():
    """确保客户表包含类型/编号/残疾类型/附件字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(customers)")).fetchall()
            has_code = any(col[1] == "customer_code" for col in columns)
            has_type = any(col[1] == "customer_type" for col in columns)
            has_gender = any(col[1] == "gender" for col in columns)
            has_age = any(col[1] == "age" for col in columns)
            has_disability = any(col[1] == "disability_type" for col in columns)
            has_attachments = any(col[1] == "attachments" for col in columns)
            has_ndis_plan = any(col[1] == "ndis_plan_copy_path" for col in columns)
            if not has_code:
                conn.execute(text("ALTER TABLE customers ADD COLUMN customer_code TEXT"))
            if not has_type:
                conn.execute(text("ALTER TABLE customers ADD COLUMN customer_type TEXT"))
            if not has_gender:
                conn.execute(text("ALTER TABLE customers ADD COLUMN gender TEXT"))
            if not has_age:
                conn.execute(text("ALTER TABLE customers ADD COLUMN age INTEGER"))
            if not has_disability:
                conn.execute(text("ALTER TABLE customers ADD COLUMN disability_type TEXT"))
            if not has_attachments:
                conn.execute(text("ALTER TABLE customers ADD COLUMN attachments TEXT"))
            if not has_ndis_plan:
                conn.execute(text("ALTER TABLE customers ADD COLUMN ndis_plan_copy_path TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移客户扩展字段失败: {e}")


def ensure_customer_m1_columns():
    """M1 NDIS 档案扩展：原住民、资金类型、Medicare、私立医保、发票接收人"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(customers)")).fetchall()
            col_names = [c[1] for c in columns]
            m1_cols = [
                ("aboriginal_torres_strait", "INTEGER"),
                ("ndis_funding_type", "TEXT"),
                ("medicare_number", "TEXT"),
                ("medicare_expiry", "TEXT"),
                ("private_health_fund", "TEXT"),
                ("private_policy_number", "TEXT"),
                ("invoice_receiver_name", "TEXT"),
                ("invoice_receiver_phone", "TEXT"),
                ("invoice_receiver_email", "TEXT"),
                ("invoice_receiver_address", "TEXT"),
            ]
            for name, col_type in m1_cols:
                if name not in col_names:
                    conn.execute(text(f"ALTER TABLE customers ADD COLUMN {name} {col_type}"))
            conn.commit()
            logger.info("已补充 M1 客户 NDIS 档案扩展字段")
    except Exception as e:
        logger.error(f"迁移 M1 客户字段失败: {e}")


def ensure_customer_emergency_contact_columns():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(customers)")).fetchall()
            col_names = {c[1] for c in columns}
            cols = [
                ("emergency_contact1_name", "TEXT"),
                ("emergency_contact1_phone", "TEXT"),
                ("emergency_contact1_email", "TEXT"),
                ("emergency_contact2_name", "TEXT"),
                ("emergency_contact2_phone", "TEXT"),
                ("emergency_contact2_email", "TEXT"),
            ]
            for name, col_type in cols:
                if name not in col_names:
                    conn.execute(text(f"ALTER TABLE customers ADD COLUMN {name} {col_type}"))
            conn.commit()
            logger.info("已补充 customers 紧急联系人字段")
    except Exception as e:
        logger.error(f"迁移 customers 紧急联系人字段失败: {e}")


def ensure_customer_status_column():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(customers)")).fetchall()
            has_status = any(col[1] == "customer_status" for col in columns)
            if not has_status:
                conn.execute(text("ALTER TABLE customers ADD COLUMN customer_status TEXT"))
            conn.execute(
                text(
                    "UPDATE customers SET customer_status = :status "
                    "WHERE customer_status IS NULL OR customer_status = ''"
                ),
                {"status": "已建档"},
            )
            conn.commit()
    except Exception as e:
        logger.error(f"迁移 customers.customer_status 字段失败: {e}")


def ensure_customer_weekly_hours_columns():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(customers)")).fetchall()
            col_names = {c[1] for c in columns}
            if "weekly_service_hours" not in col_names:
                conn.execute(text("ALTER TABLE customers ADD COLUMN weekly_service_hours REAL"))
            if "weekly_served_hours" not in col_names:
                conn.execute(text("ALTER TABLE customers ADD COLUMN weekly_served_hours REAL DEFAULT 0"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移 customers 周服务时长字段失败: {e}")


def ensure_customer_codes():
    """为历史客户补充客户编号"""
    from core.database import SessionLocal
    from shared.models import Customer
    import uuid

    db = SessionLocal()
    try:
        customers = db.query(Customer).all()
        for customer in customers:
            if not customer.customer_code:
                customer.customer_code = uuid.uuid4().hex[:6].upper()
        db.commit()
    except Exception as e:
        logger.error(f"生成客户编号失败: {e}")
        db.rollback()
    finally:
        db.close()


def ensure_customer_documents_table():
    """确保客户文档表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_documents'")
            ).fetchone()
            if table:
                return

            conn.execute(text("""
                CREATE TABLE customer_documents (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    file_type TEXT,
                    file_url TEXT,
                    form_data TEXT,
                    status TEXT,
                    signed_at DATETIME,
                    signed_file_url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """))
            conn.commit()
            logger.info("已创建 customer_documents 表")
    except Exception as e:
        logger.error(f"创建客户文档表失败: {e}")


def ensure_document_sign_requests_table():
    """确保文档签字请求表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='document_sign_requests'")
            ).fetchone()
            if table:
                return

            conn.execute(text("""
                CREATE TABLE document_sign_requests (
                    id TEXT PRIMARY KEY,
                    token TEXT UNIQUE NOT NULL,
                    customer_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    expires_at DATETIME NOT NULL,
                    signed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            logger.info("已创建 document_sign_requests 表")
    except Exception as e:
        logger.error(f"创建文档签字请求表失败: {e}")


def ensure_employee_contract_sign_requests_table():
    """确保员工合同签字请求表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='employee_contract_sign_requests'")
            ).fetchone()
            if table:
                return

            conn.execute(text("""
                CREATE TABLE employee_contract_sign_requests (
                    id TEXT PRIMARY KEY,
                    token TEXT UNIQUE NOT NULL,
                    employee_id TEXT NOT NULL,
                    contract_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    expires_at DATETIME NOT NULL,
                    signed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            logger.info("已创建 employee_contract_sign_requests 表")
    except Exception as e:
        logger.error(f"创建员工合同签字请求表失败: {e}")


def ensure_leave_requests_table():
    """确保请假请求表存在"""
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='leave_requests'")).fetchone():
                return
            conn.execute(text("""
                CREATE TABLE leave_requests (
                    id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL,
                    approver_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            logger.info("已创建 leave_requests 表")
    except Exception as e:
        logger.error(f"创建请假请求表失败: {e}")


def ensure_incident_reports_table():
    """确保事故报告表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='incident_reports'")
            ).fetchone()
            if table:
                columns = conn.execute(text("PRAGMA table_info(incident_reports)")).fetchall()
                col_names = {c[1] for c in columns}
                if "template_id" not in col_names:
                    conn.execute(text("ALTER TABLE incident_reports ADD COLUMN template_id TEXT"))
                    conn.commit()
                    logger.info("已补充 incident_reports.template_id 字段")
                return

            conn.execute(text("""
                CREATE TABLE incident_reports (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    employee_id TEXT NOT NULL,
                    incident_type TEXT,
                    description TEXT,
                    occurred_at DATETIME,
                    template_id TEXT,
                    report_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            logger.info("已创建 incident_reports 表")
    except Exception as e:
        logger.error(f"创建事故报告表失败: {e}")


def ensure_incident_templates_table():
    """确保事故报告模板表存在"""
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='incident_templates'")
            ).fetchone()
            if not exists:
                conn.execute(text("""
                    CREATE TABLE incident_templates (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        title_i18n JSON,
                        description TEXT,
                        description_i18n JSON,
                        schema_json JSON,
                        style_json JSON,
                        is_active INTEGER DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME
                    )
                """))
                conn.commit()
                logger.info("已创建 incident_templates 表")
    except Exception as e:
        logger.error(f"创建 incident_templates 表失败: {e}")


def ensure_task_record_templates_table():
    """确保任务记录模板表存在"""
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_record_templates'")
            ).fetchone()
            if not exists:
                conn.execute(text("""
                    CREATE TABLE task_record_templates (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        title_i18n JSON,
                        description TEXT,
                        description_i18n JSON,
                        schema_json JSON,
                        style_json JSON,
                        is_active INTEGER DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME
                    )
                """))
                conn.commit()
                logger.info("已创建 task_record_templates 表")
    except Exception as e:
        logger.error(f"创建 task_record_templates 表失败: {e}")


def ensure_task_records_table():
    """确保任务记录数据表存在"""
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_records'")
            ).fetchone()
            if not exists:
                conn.execute(text("""
                    CREATE TABLE task_records (
                        id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        customer_id TEXT NOT NULL,
                        employee_id TEXT NOT NULL,
                        template_id TEXT,
                        record_data TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME
                    )
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_task_records_task_id ON task_records(task_id)"))
                conn.commit()
                logger.info("已创建 task_records 表")
    except Exception as e:
        logger.error(f"创建 task_records 表失败: {e}")


def ensure_update_notifications_table():
    """确保状态更新红点表存在"""
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='update_notifications'")).fetchone():
                return
            conn.execute(text("""
                CREATE TABLE update_notifications (
                    id TEXT PRIMARY KEY,
                    audience_type TEXT NOT NULL,
                    audience_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    event_type TEXT,
                    payload TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    read_at DATETIME
                )
            """))
            conn.execute(text("""
                CREATE INDEX idx_update_notifications_audience_unread
                ON update_notifications (audience_type, audience_id, read_at)
            """))
            conn.execute(text("""
                CREATE INDEX idx_update_notifications_entity
                ON update_notifications (entity_type, entity_id)
            """))
            conn.commit()
            logger.info("已创建 update_notifications 表")
    except Exception as e:
        logger.error(f"创建状态更新红点表失败: {e}")


def ensure_business_unread_table():
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='business_unread'")
            ).fetchone()
            if not exists:
                conn.execute(text("""
                    CREATE TABLE business_unread (
                        id TEXT PRIMARY KEY,
                        business_code TEXT NOT NULL,
                        data_id TEXT,
                        scope_id TEXT,
                        receiver_user_id TEXT NOT NULL,
                        trigger_user_id TEXT,
                        is_unread INTEGER NOT NULL DEFAULT 1,
                        triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                logger.info("已创建 business_unread 表")

            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_business_unread_receiver ON business_unread(receiver_user_id, is_unread)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_business_unread_code_scope ON business_unread(business_code, scope_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_business_unread_code_data ON business_unread(business_code, data_id)"))

            has_update_notifications = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='update_notifications'")
            ).fetchone()
            if has_update_notifications:
                conn.execute(text("""
                    INSERT INTO business_unread (
                        id,
                        business_code,
                        data_id,
                        scope_id,
                        receiver_user_id,
                        trigger_user_id,
                        is_unread,
                        triggered_at
                    )
                    SELECT
                        lower(hex(randomblob(16))) AS id,
                        un.entity_type AS business_code,
                        un.entity_id AS data_id,
                        CASE WHEN un.entity_type = 'employee' THEN un.entity_id ELSE NULL END AS scope_id,
                        un.audience_id AS receiver_user_id,
                        NULL AS trigger_user_id,
                        1 AS is_unread,
                        un.created_at AS triggered_at
                    FROM update_notifications un
                    WHERE un.read_at IS NULL
                      AND NOT EXISTS (
                        SELECT 1
                        FROM business_unread bu
                        WHERE bu.receiver_user_id = un.audience_id
                          AND bu.business_code = un.entity_type
                          AND (
                            (bu.data_id IS NULL AND un.entity_id IS NULL)
                            OR bu.data_id = un.entity_id
                          )
                      )
                """))

            conn.commit()
    except Exception as e:
        logger.error(f"创建 business_unread 表失败: {e}")


def ensure_template_files_table():
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='template_files'")
            ).fetchone()
            if exists:
                return
            conn.execute(text("""
                CREATE TABLE template_files (
                    id TEXT PRIMARY KEY,
                    template_name TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_url TEXT NOT NULL,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_time DATETIME
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_template_files_create_time ON template_files(create_time)"))
            conn.commit()
            logger.info("已创建 template_files 表")
    except Exception as e:
        logger.error(f"创建 template_files 表失败: {e}")


def ensure_questionnaire_customer_type():
    """问卷表增加 customer_type 用于按客户类型选择模板"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='questionnaires'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(questionnaires)")).fetchall()
            has_ct = any(c[1] == "customer_type" for c in columns)
            if not has_ct:
                conn.execute(text("ALTER TABLE questionnaires ADD COLUMN customer_type TEXT"))
                conn.commit()
                logger.info("已补充 questionnaires.customer_type 字段")
    except Exception as e:
        logger.error(f"迁移 questionnaire customer_type 失败: {e}")


def ensure_questionnaire_i18n_columns():
    """确保 questionnaires 表包含多语言字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='questionnaires'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(questionnaires)")).fetchall()
            col_names = {c[1] for c in columns}
            changed = False
            if "title_i18n" not in col_names:
                conn.execute(text("ALTER TABLE questionnaires ADD COLUMN title_i18n JSON"))
                changed = True
            if "description_i18n" not in col_names:
                conn.execute(text("ALTER TABLE questionnaires ADD COLUMN description_i18n JSON"))
                changed = True
            if changed:
                conn.commit()
                logger.info("已补充 questionnaires.title_i18n、description_i18n 字段")
    except Exception as e:
        logger.error(f"迁移 questionnaires 多语言字段失败: {e}")


def ensure_questionnaire_responses_table():
    """确保问卷提交记录表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='questionnaire_responses'")
            ).fetchone()
            if table:
                return

            conn.execute(text("""
                CREATE TABLE questionnaire_responses (
                    id TEXT PRIMARY KEY,
                    questionnaire_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    employee_id TEXT NOT NULL,
                    answers JSON NOT NULL,
                    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(questionnaire_id) REFERENCES questionnaires(id),
                    FOREIGN KEY(task_id) REFERENCES tasks(id),
                    FOREIGN KEY(customer_id) REFERENCES customers(id),
                    FOREIGN KEY(employee_id) REFERENCES employees(id)
                )
            """))
            conn.commit()
            logger.info("已创建 questionnaire_responses 表")
    except Exception as e:
        logger.error(f"创建问卷提交记录表失败: {e}")


def ensure_task_questionnaires_is_filled_column():
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_questionnaires'")
            ).fetchone()
            if not table:
                return
            columns = conn.execute(text("PRAGMA table_info(task_questionnaires)")).fetchall()
            col_names = {c[1] for c in columns}
            if "is_filled" in col_names:
                return
            conn.execute(text("ALTER TABLE task_questionnaires ADD COLUMN is_filled INTEGER DEFAULT 0"))
            conn.commit()
            logger.info("已补充 task_questionnaires.is_filled 字段")
    except Exception as e:
        logger.error(f"迁移 task_questionnaires is_filled 失败: {e}")


def ensure_questions_conditional_columns():
    """确保 questions 表包含 conditional_required、depends_on 字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(questions)")).fetchall()
            col_names = [c[1] for c in columns]
            if "conditional_required" not in col_names:
                conn.execute(text("ALTER TABLE questions ADD COLUMN conditional_required INTEGER DEFAULT 0"))
            if "depends_on" not in col_names:
                conn.execute(text("ALTER TABLE questions ADD COLUMN depends_on TEXT"))
            conn.commit()
            logger.info("已补充 questions conditional_required、depends_on 字段")
    except Exception as e:
        logger.error(f"迁移 questions 条件必填字段失败: {e}")


def ensure_questions_i18n_columns():
    """确保 questions 表包含多语言字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(questions)")).fetchall()
            col_names = {c[1] for c in columns}
            if "title_i18n" not in col_names:
                conn.execute(text("ALTER TABLE questions ADD COLUMN title_i18n JSON"))
                conn.commit()
                logger.info("已补充 questions.title_i18n 字段")
    except Exception as e:
        logger.error(f"迁移 questions 多语言字段失败: {e}")


def ensure_task_media_columns():
    """确保任务表包含签名二进制字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            has_signature_blob = any(col[1] == "signature_blob" for col in columns)
            has_signature_mime = any(col[1] == "signature_mime" for col in columns)
            if not has_signature_blob:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN signature_blob BLOB"))
            if not has_signature_mime:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN signature_mime TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移任务签名字段失败: {e}")


def ensure_task_service_time_columns():
    """确保任务表包含服务开始/结束时间字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            has_start = any(col[1] == "service_start_time" for col in columns)
            has_end = any(col[1] == "service_end_time" for col in columns)
            if not has_start:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN service_start_time DATETIME"))
            if not has_end:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN service_end_time DATETIME"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移任务服务时间字段失败: {e}")


def ensure_task_latest_claim_time_column():
    """确保任务表包含最晚领取时间字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            has_latest_claim_time = any(col[1] == "latest_claim_time" for col in columns)
            if not has_latest_claim_time:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN latest_claim_time DATETIME"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移任务最晚领取时间字段失败: {e}")

def ensure_task_service_plans_column():
    """确保任务表包含服务计划JSON字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            has_service_plans = any(col[1] == "service_plans" for col in columns)
            if not has_service_plans:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN service_plans JSON"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移任务服务计划字段失败: {e}")

def ensure_task_employee_note_column():
    """确保任务表包含员工备注字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            has_employee_note = any(col[1] == "employee_note" for col in columns)
            if not has_employee_note:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN employee_note TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移任务员工备注字段失败: {e}")


def ensure_task_employee_remark_column():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            has_employee_remark = any(col[1] == "employee_remark" for col in columns)
            if not has_employee_remark:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN employee_remark TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移任务 employee_remark 字段失败: {e}")


def ensure_task_questionnaire_id_column():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            has_questionnaire_id = any(col[1] == "questionnaire_id" for col in columns)
            if not has_questionnaire_id:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN questionnaire_id TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移任务 questionnaire_id 字段失败: {e}")


def ensure_task_template_columns():
    """确保任务表包含事故模板与任务记录模板字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            col_names = {c[1] for c in columns}
            if "incident_template_id" not in col_names:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN incident_template_id TEXT"))
            if "task_record_template_id" not in col_names:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN task_record_template_id TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移 tasks 模板字段失败: {e}")


def ensure_task_recurrence_columns():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            col_names = {c[1] for c in columns}
            if "recurrence_rule" not in col_names:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN recurrence_rule TEXT"))
            if "recurrence_months" not in col_names:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN recurrence_months INTEGER"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移 tasks 重复规则字段失败: {e}")


def ensure_task_assigned_employee_column():
    """确保任务表包含指派员工字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
            has_assigned = any(col[1] == "assigned_employee_id" for col in columns)
            if not has_assigned:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN assigned_employee_id TEXT"))
                conn.commit()
                logger.info("已补充 tasks.assigned_employee_id 字段")
    except Exception as e:
        logger.error(f"迁移任务指派员工字段失败: {e}")


def ensure_training_record_status_column():
    """确保培训记录表包含状态字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='training_records'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(training_records)")).fetchall()
            has_status = any(col[1] == "status" for col in columns)
            if not has_status:
                conn.execute(text("ALTER TABLE training_records ADD COLUMN status TEXT"))
                conn.execute(text("UPDATE training_records SET status = 'rejected' WHERE status IS NULL OR status = ''"))
                conn.commit()
                logger.info("已补充 training_records.status 字段并初始化默认值")
    except Exception as e:
        logger.error(f"迁移培训记录状态字段失败: {e}")


def ensure_training_record_extra_columns():
    """确保培训记录表包含证书编号与培训机构字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='training_records'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(training_records)")).fetchall()
            has_certificate_number = any(col[1] == "certificate_number" for col in columns)
            has_training_institution = any(col[1] == "training_institution" for col in columns)
            if not has_certificate_number:
                conn.execute(text("ALTER TABLE training_records ADD COLUMN certificate_number TEXT"))
            if not has_training_institution:
                conn.execute(text("ALTER TABLE training_records ADD COLUMN training_institution TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移培训记录扩展字段失败: {e}")


def ensure_training_record_certificate_flag():
    """确保培训记录表包含是否发证字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='training_records'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(training_records)")).fetchall()
            has_flag = any(col[1] == "has_certificate" for col in columns)
            if not has_flag:
                conn.execute(text("ALTER TABLE training_records ADD COLUMN has_certificate INTEGER DEFAULT 0"))
                conn.execute(text("UPDATE training_records SET has_certificate = 0 WHERE has_certificate IS NULL"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移培训记录发证字段失败: {e}")


def ensure_training_record_category_fields():
    """确保培训记录表包含分类和证书日期字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='training_records'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(training_records)")).fetchall()
            column_names = [col[1] for col in columns]
            
            # 添加category字段
            if "category" not in column_names:
                conn.execute(text("ALTER TABLE training_records ADD COLUMN category TEXT"))
            
            # 添加证书日期字段
            if "certificate_obtained_date" not in column_names:
                conn.execute(text("ALTER TABLE training_records ADD COLUMN certificate_obtained_date TIMESTAMP"))
            
            if "certificate_expiry_date" not in column_names:
                conn.execute(text("ALTER TABLE training_records ADD COLUMN certificate_expiry_date TIMESTAMP"))
            
            conn.commit()
    except Exception as e:
        logger.error(f"迁移培训记录分类和证书日期字段失败: {e}")


def ensure_training_record_created_by_column():
    """确保培训记录表包含created_by字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='training_records'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(training_records)")).fetchall()
            has_created_by = any(col[1] == "created_by" for col in columns)
            if not has_created_by:
                conn.execute(text("ALTER TABLE training_records ADD COLUMN created_by TEXT"))
                # 为现有记录设置默认值：假设都是管理员创建的
                conn.execute(text("UPDATE training_records SET created_by = 'admin' WHERE created_by IS NULL"))
                conn.commit()
                logger.info("已补充 training_records.created_by 字段并初始化默认值")
    except Exception as e:
        logger.error(f"迁移培训记录created_by字段失败: {e}")


def ensure_task_photos_table():
    """确保任务照片表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_photos'")
            ).fetchone()
            if table:
                return

            conn.execute(text("""
                CREATE TABLE task_photos (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    photo_blob BLOB NOT NULL,
                    photo_mime TEXT NOT NULL,
                    shot_at DATETIME,
                    latitude REAL,
                    longitude REAL,
                    address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
            """))
            conn.commit()
            logger.info("已创建 task_photos 表")
    except Exception as e:
        logger.error(f"创建任务照片表失败: {e}")


def ensure_task_photo_metadata_columns():
    """确保任务照片表包含拍照元数据字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_photos'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(task_photos)")).fetchall()
            has_shot_at = any(col[1] == "shot_at" for col in columns)
            has_latitude = any(col[1] == "latitude" for col in columns)
            has_longitude = any(col[1] == "longitude" for col in columns)
            has_address = any(col[1] == "address" for col in columns)
            if not has_shot_at:
                conn.execute(text("ALTER TABLE task_photos ADD COLUMN shot_at DATETIME"))
            if not has_latitude:
                conn.execute(text("ALTER TABLE task_photos ADD COLUMN latitude REAL"))
            if not has_longitude:
                conn.execute(text("ALTER TABLE task_photos ADD COLUMN longitude REAL"))
            if not has_address:
                conn.execute(text("ALTER TABLE task_photos ADD COLUMN address TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移任务照片元数据字段失败: {e}")


def ensure_task_location_tracks_table():
    """确保任务轨迹表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_location_tracks'")
            ).fetchone()
            if table:
                return

            conn.execute(text("""
                CREATE TABLE task_location_tracks (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    address TEXT,
                    accuracy REAL,
                    speed REAL,
                    altitude REAL,
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
            """))
            conn.commit()
            logger.info("已创建 task_location_tracks 表")
    except Exception as e:
        logger.error(f"创建任务轨迹表失败: {e}")


def ensure_task_cancellation_notifications_table():
    """确保任务取消通知表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_cancellation_notifications'")
            ).fetchone()
            if table:
                return

            conn.execute(text("""
                CREATE TABLE task_cancellation_notifications (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    employee_id TEXT NOT NULL,
                    cancel_reason TEXT,
                    is_confirmed INTEGER DEFAULT 0,
                    confirmed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(task_id) REFERENCES tasks(id),
                    FOREIGN KEY(employee_id) REFERENCES employees(id)
                )
            """))
            conn.commit()
            logger.info("已创建 task_cancellation_notifications 表")
    except Exception as e:
        logger.error(f"创建任务取消通知表失败: {e}")


def ensure_qualification_blob_columns():
    """确保资质表包含证书二进制字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='qualifications'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(qualifications)")).fetchall()
            has_certificate_blob = any(col[1] == "certificate_blob" for col in columns)
            has_certificate_mime = any(col[1] == "certificate_mime" for col in columns)
            if not has_certificate_blob:
                conn.execute(text("ALTER TABLE qualifications ADD COLUMN certificate_blob BLOB"))
            if not has_certificate_mime:
                conn.execute(text("ALTER TABLE qualifications ADD COLUMN certificate_mime TEXT"))
            conn.commit()
    except Exception as e:
        logger.error(f"迁移资质证书字段失败: {e}")


def migrate_media_to_db():
    """将已有签名/照片/证书迁移到数据库"""
    from core.database import SessionLocal
    from shared.models import Task, TaskPhoto, Qualification
    from pathlib import Path

    def parse_data_url(data_url: str):
        match = re.match(r"^data:(.+?);base64,(.+)$", data_url)
        if not match:
            return None, None
        mime_type = match.group(1)
        data = base64.b64decode(match.group(2))
        return mime_type, data

    def guess_mime(path: str):
        mime, _ = mimetypes.guess_type(path)
        return mime or "application/octet-stream"

    db = SessionLocal()
    try:
        tasks = db.query(Task).all()
        for task in tasks:
            if task.signature_image_url and not task.signature_blob:
                mime_type, blob = None, None
                if task.signature_image_url.startswith("data:image"):
                    mime_type, blob = parse_data_url(task.signature_image_url)
                else:
                    path = Path(task.signature_image_url)
                    if path.exists():
                        blob = path.read_bytes()
                        mime_type = guess_mime(str(path))
                if blob:
                    task.signature_blob = blob
                    task.signature_mime = mime_type or "image/png"
                    task.signature_image_url = f"/api/app/tasks/{task.id}/signature/image"

            if task.photo_urls:
                try:
                    urls = task.photo_urls if isinstance(task.photo_urls, list) else []
                except Exception:
                    urls = []
                new_urls = []
                for url in urls:
                    mime_type, blob = None, None
                    if isinstance(url, str) and url.startswith("data:image"):
                        mime_type, blob = parse_data_url(url)
                    else:
                        path = Path(url)
                        if path.exists():
                            blob = path.read_bytes()
                            mime_type = guess_mime(str(path))
                    if blob:
                        photo = TaskPhoto(
                            task_id=task.id,
                            photo_blob=blob,
                            photo_mime=mime_type or "image/jpeg"
                        )
                        db.add(photo)
                        db.flush()
                        new_urls.append(f"/api/app/tasks/{task.id}/photos/{photo.id}")
                    else:
                        new_urls.append(url)
                task.photo_urls = new_urls

        qualifications = db.query(Qualification).all()
        for qualification in qualifications:
            if qualification.certificate_url and not qualification.certificate_blob:
                path = Path(qualification.certificate_url)
                if path.exists():
                    qualification.certificate_blob = path.read_bytes()
                    qualification.certificate_mime = guess_mime(str(path))
                    qualification.certificate_url = f"/api/houtai/qualifications/{qualification.id}/certificate"

        db.commit()
    except Exception as e:
        logger.error(f"迁移媒体文件失败: {e}")
        db.rollback()
    finally:
        db.close()
def ensure_qualification_certificate_url():
    """确保资质表包含证书文件路径列"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='qualifications'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(qualifications)")).fetchall()
            has_certificate_url = any(col[1] == "certificate_url" for col in columns)
            if not has_certificate_url:
                conn.execute(text("ALTER TABLE qualifications ADD COLUMN certificate_url TEXT"))
                conn.commit()
                logger.info("已补充 qualifications.certificate_url 字段")
    except Exception as e:
        logger.error(f"迁移资质证书字段失败: {e}")


def ensure_system_settings_table():
    """确保系统设置表存在"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'")
            ).fetchone()
            if table:
                return

            conn.execute(text("""
                CREATE TABLE system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """))
            conn.commit()
            logger.info("已创建 system_settings 表")
    except Exception as e:
        logger.error(f"创建 system_settings 表失败: {e}")


def ensure_invoice_catalog_tables():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            has_invoices_table = bool(conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")).fetchone())
            if not conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_item_categories'")).fetchone():
                conn.execute(text("""
                    CREATE TABLE invoice_item_categories (
                        id TEXT PRIMARY KEY,
                        parent_id TEXT,
                        name TEXT NOT NULL,
                        code TEXT,
                        level INTEGER NOT NULL DEFAULT 1,
                        path TEXT NOT NULL,
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        is_active INTEGER NOT NULL DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME,
                        FOREIGN KEY(parent_id) REFERENCES invoice_item_categories(id)
                    )
                """))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_cat_parent_name ON invoice_item_categories(parent_id, name)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_cat_parent ON invoice_item_categories(parent_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_cat_path ON invoice_item_categories(path)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_cat_active ON invoice_item_categories(is_active)"))

            if not conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_item_dict'")).fetchone():
                if has_invoices_table:
                    conn.execute(text("""
                        CREATE TABLE invoice_item_dict (
                            id TEXT PRIMARY KEY,
                            category_id TEXT NOT NULL,
                            item_code TEXT NOT NULL,
                            item_name TEXT NOT NULL,
                            spec_default TEXT,
                            unit_default TEXT,
                            price_default NUMERIC,
                            tax_rate_default NUMERIC NOT NULL DEFAULT 0,
                            is_active INTEGER NOT NULL DEFAULT 1,
                            created_from_invoice_id TEXT,
                            created_by TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME,
                            FOREIGN KEY(category_id) REFERENCES invoice_item_categories(id),
                            FOREIGN KEY(created_from_invoice_id) REFERENCES invoices(id)
                        )
                    """))
                else:
                    conn.execute(text("""
                        CREATE TABLE invoice_item_dict (
                            id TEXT PRIMARY KEY,
                            category_id TEXT NOT NULL,
                            item_code TEXT NOT NULL,
                            item_name TEXT NOT NULL,
                            spec_default TEXT,
                            unit_default TEXT,
                            price_default NUMERIC,
                            tax_rate_default NUMERIC NOT NULL DEFAULT 0,
                            is_active INTEGER NOT NULL DEFAULT 1,
                            created_from_invoice_id TEXT,
                            created_by TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME,
                            FOREIGN KEY(category_id) REFERENCES invoice_item_categories(id)
                        )
                    """))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_item_code ON invoice_item_dict(item_code)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_item_cat ON invoice_item_dict(category_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_item_active ON invoice_item_dict(is_active)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_item_name ON invoice_item_dict(item_name)"))

            if not conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_item_dict_versions'")).fetchone():
                conn.execute(text("""
                    CREATE TABLE invoice_item_dict_versions (
                        id TEXT PRIMARY KEY,
                        item_id TEXT NOT NULL,
                        version_no INTEGER NOT NULL,
                        item_code TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        spec_default TEXT,
                        unit_default TEXT,
                        price_default NUMERIC,
                        tax_rate_default NUMERIC NOT NULL,
                        changed_by TEXT,
                        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(item_id) REFERENCES invoice_item_dict(id)
                    )
                """))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_item_ver ON invoice_item_dict_versions(item_id, version_no)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_item_ver_item ON invoice_item_dict_versions(item_id)"))

            if not conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_audit_logs'")).fetchone():
                if has_invoices_table:
                    conn.execute(text("""
                        CREATE TABLE invoice_audit_logs (
                            id TEXT PRIMARY KEY,
                            invoice_id TEXT NOT NULL,
                            action TEXT NOT NULL,
                            actor_id TEXT,
                            actor_type TEXT,
                            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            before_json TEXT,
                            after_json TEXT,
                            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
                        )
                    """))
                else:
                    conn.execute(text("""
                        CREATE TABLE invoice_audit_logs (
                            id TEXT PRIMARY KEY,
                            invoice_id TEXT NOT NULL,
                            action TEXT NOT NULL,
                            actor_id TEXT,
                            actor_type TEXT,
                            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            before_json TEXT,
                            after_json TEXT
                        )
                    """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_audit_invoice_time ON invoice_audit_logs(invoice_id, changed_at)"))

            conn.commit()
    except Exception as e:
        logger.error(f"创建发票项目字典相关表失败: {e}")


def ensure_invoice_service_catalog_v2_tables():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS invoice_service_level1 (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS invoice_service_level2 (
                    id TEXT PRIMARY KEY,
                    level1_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY(level1_id) REFERENCES invoice_service_level1(id)
                )
            """))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_svc_l2_l1_name ON invoice_service_level2(level1_id, name)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l2_l1 ON invoice_service_level2(level1_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l2_active ON invoice_service_level2(is_active)"))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS invoice_service_level3 (
                    id TEXT PRIMARY KEY,
                    level1_id TEXT NOT NULL,
                    level2_id TEXT,
                    name TEXT NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY(level1_id) REFERENCES invoice_service_level1(id),
                    FOREIGN KEY(level2_id) REFERENCES invoice_service_level2(id)
                )
            """))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_svc_l3_key ON invoice_service_level3(level1_id, level2_id, name)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l3_l1 ON invoice_service_level3(level1_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l3_l2 ON invoice_service_level3(level2_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l3_active ON invoice_service_level3(is_active)"))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS invoice_service_codes (
                    id TEXT PRIMARY KEY,
                    level3_id TEXT NOT NULL,
                    code TEXT NOT NULL UNIQUE,
                    price NUMERIC,
                    unit TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY(level3_id) REFERENCES invoice_service_level3(id)
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_code_l3 ON invoice_service_codes(level3_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_code_active ON invoice_service_codes(is_active)"))

            conn.commit()
    except Exception as e:
        logger.error(f"创建发票服务目录 v2 表失败: {e}")


def ensure_customer_service_level1_table():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_service_level1'")
            ).fetchone()
            if exists:
                return

            conn.execute(text("""
                CREATE TABLE customer_service_level1 (
                    customer_id TEXT NOT NULL,
                    level1_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    PRIMARY KEY(customer_id, level1_id),
                    FOREIGN KEY(customer_id) REFERENCES customers(id),
                    FOREIGN KEY(level1_id) REFERENCES invoice_service_level1(id)
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cust_svc_l1_customer ON customer_service_level1(customer_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cust_svc_l1_level1 ON customer_service_level1(level1_id)"))
            conn.commit()
            logger.info("已创建 customer_service_level1 表")
    except Exception as e:
        logger.error(f"创建 customer_service_level1 表失败: {e}")


def seed_invoice_service_catalog_v2_if_empty():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT COUNT(1) FROM invoice_service_level1")).fetchone()
            total = row[0] if row else 0
            if total and int(total) > 0:
                return
    except Exception:
        pass

    try:
        from scripts.seed_invoice_service_catalog_v2 import seed as seed_v2
        seed_v2()
        logger.info("已初始化发票服务目录 v2 数据")
    except Exception as e:
        logger.error(f"初始化发票服务目录 v2 数据失败: {e}")


def ensure_invoice_schema_v2_columns():
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")).fetchone():
                columns = conn.execute(text("PRAGMA table_info(invoices)")).fetchall()
                col_names = [c[1] for c in columns]
                if "paid_at" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN paid_at DATETIME"))
                if "voided_at" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN voided_at DATETIME"))
                if "void_reason" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN void_reason TEXT"))
                if "currency" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN currency TEXT"))
                    conn.execute(text("UPDATE invoices SET currency = 'AUD' WHERE currency IS NULL OR currency = ''"))
                if "buyer_name" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN buyer_name TEXT"))
                if "buyer_phone" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN buyer_phone TEXT"))
                if "buyer_email" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN buyer_email TEXT"))
                if "buyer_address" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN buyer_address TEXT"))
                if "total_excl_tax" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN total_excl_tax NUMERIC"))
                if "total_tax" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN total_tax NUMERIC"))
                if "total_incl_tax" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN total_incl_tax NUMERIC"))
                if "created_by" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN created_by TEXT"))
                if "updated_by" not in col_names:
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN updated_by TEXT"))

                conn.execute(text("""
                    UPDATE invoices
                    SET
                        total_incl_tax = COALESCE(total_incl_tax, total_amount),
                        total_excl_tax = COALESCE(total_excl_tax, total_amount),
                        total_tax = COALESCE(total_tax, 0)
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_customer_date ON invoices(customer_id, invoice_date)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_status_date ON invoices(status, invoice_date)"))

            if conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_items'")).fetchone():
                columns = conn.execute(text("PRAGMA table_info(invoice_items)")).fetchall()
                col_names = [c[1] for c in columns]
                if "line_no" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN line_no INTEGER"))
                if "item_id" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN item_id TEXT"))
                if "category_id" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN category_id TEXT"))
                if "item_code" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN item_code TEXT"))
                if "item_name" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN item_name TEXT"))
                if "specification" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN specification TEXT"))
                if "unit" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN unit TEXT"))
                if "unit_price" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN unit_price NUMERIC"))
                if "amount_excl_tax" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN amount_excl_tax NUMERIC"))
                if "tax_rate" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN tax_rate NUMERIC"))
                if "tax_amount" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN tax_amount NUMERIC"))
                if "amount_incl_tax" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN amount_incl_tax NUMERIC"))
                if "source_task_id" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN source_task_id TEXT"))
                if "remark" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN remark TEXT"))
                if "updated_at" not in col_names:
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN updated_at DATETIME"))

                conn.execute(text("""
                    UPDATE invoice_items
                    SET
                        item_code = COALESCE(item_code, service_code),
                        item_name = COALESCE(item_name, description),
                        unit_price = COALESCE(unit_price, price),
                        amount_excl_tax = COALESCE(amount_excl_tax, amount),
                        tax_rate = COALESCE(tax_rate, 0),
                        tax_amount = COALESCE(tax_amount, 0),
                        amount_incl_tax = COALESCE(amount_incl_tax, amount),
                        source_task_id = COALESCE(source_task_id, task_id)
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_line_invoice ON invoice_items(invoice_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_line_item_code ON invoice_items(item_code)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_line_task ON invoice_items(source_task_id)"))

            conn.commit()
    except Exception as e:
        logger.error(f"迁移发票表字段失败: {e}")


def seed_ndis_supports_in_employment_items():
    if engine.dialect.name != "sqlite":
        return

    import uuid as _uuid

    def _get_or_create_category(conn, parent_id, name: str):
        row = conn.execute(
            text("""
                SELECT id, path, level
                FROM invoice_item_categories
                WHERE name = :name
                  AND (
                    (parent_id = :pid) OR (parent_id IS NULL AND :pid IS NULL)
                  )
                LIMIT 1
            """),
            {"pid": parent_id, "name": name},
        ).fetchone()
        if row:
            return row[0], row[1], row[2]

        new_id = str(_uuid.uuid4())
        if parent_id:
            parent = conn.execute(
                text("SELECT path, level FROM invoice_item_categories WHERE id = :id LIMIT 1"),
                {"id": parent_id},
            ).fetchone()
            parent_path = parent[0] if parent else "/"
            parent_level = parent[1] if parent else 0
        else:
            parent_path = "/"
            parent_level = 0

        path = f"{parent_path}{new_id}/"
        level = parent_level + 1
        conn.execute(
            text("""
                INSERT INTO invoice_item_categories (
                    id, parent_id, name, code, level, path, sort_order, is_active, created_at
                ) VALUES (
                    :id, :parent_id, :name, NULL, :level, :path, 0, 1, CURRENT_TIMESTAMP
                )
            """),
            {"id": new_id, "parent_id": parent_id, "name": name, "level": level, "path": path},
        )
        return new_id, path, level

    def _upsert_item(conn, category_id: str, item_code: str, item_name: str, price_default: str):
        existing = conn.execute(
            text("SELECT id FROM invoice_item_dict WHERE item_code = :code LIMIT 1"),
            {"code": item_code},
        ).fetchone()
        if existing:
            item_id = existing[0]
            conn.execute(
                text("""
                    UPDATE invoice_item_dict
                    SET
                        category_id = :category_id,
                        item_name = :item_name,
                        price_default = :price_default,
                        tax_rate_default = 0,
                        unit_default = COALESCE(unit_default, 'Hour'),
                        is_active = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"id": item_id, "category_id": category_id, "item_name": item_name, "price_default": price_default},
            )
        else:
            item_id = str(_uuid.uuid4())
            conn.execute(
                text("""
                    INSERT INTO invoice_item_dict (
                        id, category_id, item_code, item_name, spec_default, unit_default,
                        price_default, tax_rate_default, is_active, created_at
                    ) VALUES (
                        :id, :category_id, :item_code, :item_name, NULL, 'Hour',
                        :price_default, 0, 1, CURRENT_TIMESTAMP
                    )
                """),
                {"id": item_id, "category_id": category_id, "item_code": item_code, "item_name": item_name, "price_default": price_default},
            )

        ver = conn.execute(
            text("SELECT MAX(version_no) FROM invoice_item_dict_versions WHERE item_id = :item_id"),
            {"item_id": item_id},
        ).fetchone()
        max_ver = ver[0] if ver and ver[0] is not None else 0
        if max_ver == 0:
            conn.execute(
                text("""
                    INSERT INTO invoice_item_dict_versions (
                        id, item_id, version_no, item_code, item_name, spec_default, unit_default,
                        price_default, tax_rate_default, changed_at
                    ) VALUES (
                        :id, :item_id, 1, :item_code, :item_name, NULL, 'Hour',
                        :price_default, 0, CURRENT_TIMESTAMP
                    )
                """),
                {"id": str(_uuid.uuid4()), "item_id": item_id, "item_code": item_code, "item_name": item_name, "price_default": price_default},
            )

    try:
        with engine.connect() as conn:
            if not conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_item_categories'")).fetchone():
                return
            if not conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_item_dict'")).fetchone():
                return

            root_id, _, _ = _get_or_create_category(conn, None, "NDIS")
            cat1_id, _, _ = _get_or_create_category(conn, root_id, "Assistance with Social, Economic and Community Participation")
            cat2_id, _, _ = _get_or_create_category(conn, cat1_id, "Specialised Supported Employment (0133)")
            cat3_id, _, _ = _get_or_create_category(conn, cat2_id, "Supports in Employment")

            _upsert_item(conn, cat3_id, "04_801_0133_5_1", "Supports in Employment - Weekday Daytime", "70.23")
            _upsert_item(conn, cat3_id, "04_802_0133_5_1", "Supports in Employment - Weekday Evening", "77.38")
            _upsert_item(conn, cat3_id, "04_803_0133_5_1", "Supports in Employment - Saturday", "98.83")
            _upsert_item(conn, cat3_id, "04_804_0133_5_1", "Supports in Employment - Sunday", "127.43")
            _upsert_item(conn, cat3_id, "04_805_0133_5_1", "Supports in Employment - Public Holiday", "156.03")

            conn.commit()
    except Exception as e:
        logger.error(f"初始化 NDIS 项目字典失败: {e}")


def ensure_contract_signature_columns():
    """确保员工文档表包含合同签字相关字段"""
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='employee_documents'")
            ).fetchone()
            if not table:
                return

            columns = conn.execute(text("PRAGMA table_info(employee_documents)")).fetchall()
            column_names = [col[1] for col in columns]
            
            # 添加员工签字相关字段
            if "employee_signature_blob" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN employee_signature_blob BLOB"))
            if "employee_signature_mime" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN employee_signature_mime TEXT"))
            if "employee_signed_at" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN employee_signed_at DATETIME"))
            if "employee_signature_x" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN employee_signature_x REAL"))
            if "employee_signature_y" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN employee_signature_y REAL"))
            if "employee_signature_width" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN employee_signature_width REAL"))
            if "employee_signature_height" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN employee_signature_height REAL"))
            if "employee_signature_page" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN employee_signature_page INTEGER"))
            
            # 添加管理员签字相关字段
            if "admin_signature_blob" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signature_blob BLOB"))
            if "admin_signature_mime" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signature_mime TEXT"))
            if "admin_signed_at" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signed_at DATETIME"))
            if "admin_signed_by" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signed_by TEXT"))
            if "admin_signature_x" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signature_x REAL"))
            if "admin_signature_y" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signature_y REAL"))
            if "admin_signature_width" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signature_width REAL"))
            if "admin_signature_height" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signature_height REAL"))
            if "admin_signature_page" not in column_names:
                conn.execute(text("ALTER TABLE employee_documents ADD COLUMN admin_signature_page INTEGER"))
            
            conn.commit()
            logger.info("已补充 employee_documents 合同签字相关字段")
    except Exception as e:
        logger.error(f"迁移合同签字字段失败: {e}")

def ensure_service_questionnaire_template():
    """确保存在与 app 服务问卷一致的模板"""
    from core.database import SessionLocal
    from shared.models import Questionnaire, Question

    db = SessionLocal()
    try:
        existing = None
        for title in ("服务过程问卷调查", "Service Process Survey", "Service Questionnaire"):
            existing = db.query(Questionnaire).filter(Questionnaire.title == title).first()
            if existing:
                break
        if existing:
            desired_placeholder = "Please provide your comments or suggestions."
            candidates = db.query(Question).filter(
                Question.questionnaire_id == existing.id,
                Question.type == "text",
            ).all()
            updated = False
            for q in candidates:
                current = (q.placeholder or "").strip()
                should_update = (
                    not current
                    or "请输入" in current
                    or "意见" in current
                    or "建议" in current
                    or q.title in ("Other Comments or Suggestions", "其他意见或建议")
                )
                if should_update:
                    if q.placeholder != desired_placeholder:
                        q.placeholder = desired_placeholder
                        updated = True
            if updated:
                db.commit()
            return

        questionnaire = Questionnaire(
            title="服务过程问卷调查",
            description="请如实填写以下问卷，帮助我们改进服务质量。",
            is_active=True
        )
        db.add(questionnaire)
        db.flush()

        questions = [
            {
                "title": "服务态度如何？",
                "type": "single_choice",
                "required": True,
                "options": [
                    {"id": "opt1", "text": "非常满意"},
                    {"id": "opt2", "text": "满意"},
                    {"id": "opt3", "text": "一般"},
                    {"id": "opt4", "text": "不满意"}
                ]
            },
            {
                "title": "服务效率如何？",
                "type": "single_choice",
                "required": True,
                "options": [
                    {"id": "opt1", "text": "很快"},
                    {"id": "opt2", "text": "正常"},
                    {"id": "opt3", "text": "较慢"}
                ]
            },
            {
                "title": "您对哪些方面满意？（可多选）",
                "type": "multiple_choice",
                "required": False,
                "options": [
                    {"id": "opt1", "text": "服务态度"},
                    {"id": "opt2", "text": "专业技能"},
                    {"id": "opt3", "text": "响应速度"},
                    {"id": "opt4", "text": "问题解决"}
                ]
            },
            {
                "title": "其他意见或建议",
                "type": "text",
                "required": False,
                "options": None,
                "placeholder": "Please provide your comments or suggestions."
            }
        ]

        for idx, data in enumerate(questions):
            question = Question(
                questionnaire_id=questionnaire.id,
                order_index=idx,
                title=data["title"],
                type=data["type"],
                required=data["required"],
                options=data.get("options"),
                placeholder=data.get("placeholder")
            )
            db.add(question)

        db.commit()
        logger.info("已创建服务问卷模板")
    except Exception as e:
        logger.error(f"创建服务问卷模板失败: {e}")
        db.rollback()
    finally:
        db.close()


def ensure_progress_notes_templates():
    """创建 Progress Notes - Aged Care 与 Progress Notes - NDIS 双模板"""
    from core.database import SessionLocal
    from shared.models import Questionnaire, Question

    db = SessionLocal()
    try:
        aged = db.query(Questionnaire).filter(
            Questionnaire.title == "Progress Notes - Aged Care"
        ).first()
        if not aged:
            aged = Questionnaire(
                title="Progress Notes - Aged Care",
                description="养老院工作日志",
                is_active=True,
                customer_type="养老"
            )
            db.add(aged)
            db.flush()
            for idx, d in enumerate(_progress_notes_questions()):
                q = Question(questionnaire_id=aged.id, order_index=idx, **d)
                db.add(q)
            logger.info("已创建 Progress Notes - Aged Care 模板")

        ndis = db.query(Questionnaire).filter(
            Questionnaire.title == "Progress Notes - NDIS"
        ).first()
        if not ndis:
            ndis = Questionnaire(
                title="Progress Notes - NDIS",
                description="NDIS Progress Notes",
                is_active=True,
                customer_type="NDIS"
            )
            db.add(ndis)
            db.flush()
            for idx, d in enumerate(_progress_notes_questions()):
                q = Question(questionnaire_id=ndis.id, order_index=idx, **d)
                db.add(q)
            logger.info("已创建 Progress Notes - NDIS 模板")

        db.commit()
    except Exception as e:
        logger.error(f"创建 Progress Notes 模板失败: {e}")
        db.rollback()


def ensure_default_incident_template():
    from core.database import SessionLocal
    from shared.models import IncidentTemplate

    db = SessionLocal()
    try:
        existing = db.query(IncidentTemplate).first()
        if existing:
            return
        t = IncidentTemplate(
            title="Accident Report",
            title_i18n={"zh": "事故报告", "en": "Accident Report"},
            description="",
            description_i18n={"zh": "", "en": ""},
            schema_json={"questions": []},
            style_json={"preset": "default"},
            is_active=True,
        )
        db.add(t)
        db.commit()
        logger.info("已创建默认事故模板")
    except Exception as e:
        logger.error(f"创建默认事故模板失败: {e}")
        db.rollback()
    finally:
        db.close()


def ensure_default_task_record_template():
    from core.database import SessionLocal
    from shared.models import TaskRecordTemplate

    db = SessionLocal()
    try:
        existing = db.query(TaskRecordTemplate).first()
        if existing:
            return
        t = TaskRecordTemplate(
            title="Task Record",
            title_i18n={"zh": "任务记录", "en": "Task Record"},
            description="",
            description_i18n={"zh": "", "en": ""},
            schema_json={"questions": []},
            style_json={"preset": "default"},
            is_active=True,
        )
        db.add(t)
        db.commit()
        logger.info("已创建默认任务记录模板")
    except Exception as e:
        logger.error(f"创建默认任务记录模板失败: {e}")
        db.rollback()
    finally:
        db.close()


def _progress_notes_questions():
    """Progress Notes 通用题目（不含 depends_on，需创建后通过 UI 配置）"""
    return [
        {"title": "完成 (Done)", "type": "single_choice", "required": False, "options": [{"id": "yes", "text": "是"}, {"id": "no", "text": "否"}]},
        {"title": "开始时间", "type": "text", "required": False, "placeholder": "HH:mm"},
        {"title": "结束时间", "type": "text", "required": False, "placeholder": "HH:mm"},
        {"title": "餐饮协助", "type": "single_choice", "required": False, "options": [{"id": "yes", "text": "是"}, {"id": "no", "text": "否"}]},
        {"title": "食物名称（若提供餐饮协助）", "type": "text", "required": False, "placeholder": "食物名称"},
        {"title": "药物管理", "type": "single_choice", "required": False, "options": [{"id": "yes", "text": "是"}, {"id": "no", "text": "否"}]},
        {"title": "药物名称及剂量（若提供药物管理）", "type": "text", "required": False, "placeholder": "药物名称、剂量"},
        {"title": "社交/家务活动", "type": "single_choice", "required": False, "options": [{"id": "yes", "text": "是"}, {"id": "no", "text": "否"}]},
        {"title": "活动内容（若提供社交/家务）", "type": "text", "required": False, "placeholder": "活动描述"},
        {"title": "跌倒/差点跌倒", "type": "multiple_choice", "required": False, "options": [{"id": "fall", "text": "跌倒"}, {"id": "near_fall", "text": "差点跌倒"}, {"id": "none", "text": "无"}]},
        {"title": "备注", "type": "text", "required": False, "placeholder": "其他说明"},
    ]

# 初始化数据库（创建表和默认用户）
def init_db():
    """初始化数据库"""
    from core.database import SessionLocal
    from shared.models import User
    from core.auth import get_password_hash

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建成功！")

    # 创建默认管理员账户（如果不存在）
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info("默认管理员账户已创建：用户名=admin, 密码=admin123")
        else:
            logger.info("管理员账户已存在")
    except Exception as e:
        logger.error(f"初始化数据库时出错: {e}")
        db.rollback()
    finally:
        db.close()


def _should_bootstrap_db() -> bool:
    if engine.dialect.name != "sqlite":
        return False
    try:
        with engine.connect() as conn:
            users_table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            ).fetchone()
            return users_table is None
    except Exception:
        return False


# 根据配置决定是否初始化数据库
if settings.init_db_on_startup or _should_bootstrap_db():
    init_db()
    logger.info("数据库初始化完成")
else:
    logger.info("跳过数据库初始化（init_db_on_startup=False）")

# 轻量迁移：保证员工密码列存在
ensure_employee_password_column()
ensure_employee_password_reset_columns()
ensure_employee_account_status_column()
ensure_employee_email_unique_index()
migrate_customers_schema()
ensure_customer_extra_columns()
ensure_customer_m1_columns()
ensure_customer_emergency_contact_columns()
ensure_customer_status_column()
ensure_customer_weekly_hours_columns()
ensure_customer_codes()
ensure_customer_documents_table()
ensure_document_sign_requests_table()
ensure_employee_contract_sign_requests_table()
ensure_leave_requests_table()
ensure_incident_reports_table()
ensure_incident_templates_table()
ensure_task_record_templates_table()
ensure_task_records_table()
ensure_update_notifications_table()
ensure_business_unread_table()
ensure_template_files_table()
ensure_questionnaire_customer_type()
ensure_questionnaire_i18n_columns()
ensure_questionnaire_responses_table()
ensure_task_questionnaires_is_filled_column()
ensure_questions_conditional_columns()
ensure_questions_i18n_columns()
ensure_service_questionnaire_template()
ensure_progress_notes_templates()
ensure_default_incident_template()
ensure_default_task_record_template()
ensure_qualification_certificate_url()
ensure_task_media_columns()
ensure_task_service_time_columns()
ensure_task_latest_claim_time_column()
ensure_task_service_plans_column()
ensure_task_employee_note_column()
ensure_task_employee_remark_column()
ensure_task_questionnaire_id_column()
ensure_task_template_columns()
ensure_task_recurrence_columns()
ensure_task_assigned_employee_column()
ensure_training_record_status_column()
ensure_training_record_extra_columns()
ensure_training_record_certificate_flag()
ensure_training_record_category_fields()
ensure_training_record_created_by_column()
ensure_task_photos_table()
ensure_task_photo_metadata_columns()
ensure_task_location_tracks_table()
ensure_task_cancellation_notifications_table()
ensure_qualification_blob_columns()
migrate_media_to_db()
ensure_invoice_catalog_tables()
ensure_invoice_service_catalog_v2_tables()
seed_invoice_service_catalog_v2_if_empty()
ensure_invoice_schema_v2_columns()
def ensure_invoice_item_task_service_item_column():
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            cols = conn.execute(
                text("PRAGMA table_info('invoice_items')")
            ).fetchall()
            names = {row[1] for row in cols}
            if "task_service_item_id" in names:
                return
            conn.execute(text("ALTER TABLE invoice_items ADD COLUMN task_service_item_id TEXT"))
            conn.commit()
            logger.info("已为 invoice_items 增加 task_service_item_id 列")
    except Exception as e:
        logger.error(f"增加 task_service_item_id 列失败: {e}")
ensure_invoice_item_task_service_item_column()
seed_ndis_supports_in_employment_items()
ensure_system_settings_table()
ensure_contract_signature_columns()
ensure_customer_service_level1_table()
def ensure_task_questionnaires_table():
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_questionnaires'")
            ).fetchone()
            if table:
                return
            conn.execute(text("""
                CREATE TABLE task_questionnaires (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    questionnaire_id TEXT NOT NULL,
                    is_required INTEGER NOT NULL DEFAULT 1,
                    order_index INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(task_id) REFERENCES tasks(id),
                    FOREIGN KEY(questionnaire_id) REFERENCES questionnaires(id)
                )
            """))
            conn.execute(text("""
                CREATE INDEX idx_task_questionnaires_task_id
                ON task_questionnaires (task_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_task_questionnaires_questionnaire_id
                ON task_questionnaires (questionnaire_id)
            """))
            conn.commit()
            logger.info("已创建 task_questionnaires 表")
    except Exception as e:
        logger.error(f"创建 task_questionnaires 表失败: {e}")


ensure_task_questionnaires_table()
def ensure_task_service_items_table():
    if engine.dialect.name != "sqlite":
        return
    try:
        with engine.connect() as conn:
            table = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='task_service_items'")
            ).fetchone()
            if table:
                return
            conn.execute(text("""
                CREATE TABLE task_service_items (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    level1_id TEXT,
                    level2_id TEXT,
                    level3_id TEXT,
                    service_code TEXT NOT NULL,
                    unit TEXT,
                    unit_price NUMERIC(10,2) NOT NULL DEFAULT 0,
                    quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
                    amount NUMERIC(10,2) NOT NULL DEFAULT 0,
                    remark TEXT,
                    service_time_start TEXT,
                    service_time_end TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
            """))
            conn.commit()
            logger.info("已创建 task_service_items 表")
    except Exception as e:
        logger.error(f"创建 task_service_items 表失败: {e}")
ensure_task_service_items_table()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    处理启动和关闭事件
    """
    # 启动时执行
    logger.info("应用启动中...")
    reset_task = None
    try:
        # 可以在这里初始化其他资源
        import asyncio
        from datetime import datetime, timedelta, time as dt_time
        from core.database import SessionLocal

        async def _weekly_reset_customer_served_hours_loop():
            while True:
                now = datetime.now()
                today = now.date()
                next_monday = today + timedelta(days=(7 - today.weekday()) % 7)
                if next_monday == today and now.time() >= dt_time(0, 0):
                    next_monday = today + timedelta(days=7)
                next_reset = datetime.combine(next_monday, dt_time(0, 0))
                wait_seconds = max(1, int((next_reset - now).total_seconds()))
                await asyncio.sleep(wait_seconds)

                db = SessionLocal()
                try:
                    db.execute(text("UPDATE customers SET weekly_served_hours = 0"))
                    db.commit()
                except Exception as e:
                    logger.error(f"每周清零 customers.weekly_served_hours 失败: {e}")
                    db.rollback()
                finally:
                    db.close()

        reset_task = asyncio.create_task(_weekly_reset_customer_served_hours_loop())
        logger.info("应用启动完成")
        yield
    finally:
        # 关闭时执行
        logger.info("应用关闭中，正在清理资源...")
        try:
            if reset_task is not None:
                reset_task.cancel()
            # 关闭数据库连接池
            close_db_connections()
            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"关闭时清理资源失败: {e}", exc_info=True)


# 创建 FastAPI 应用
app = FastAPI(
    title="澳州项目后端API",
    description="官网、移动应用和管理后台统一后端API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
setup_cors(app)

_uploads_path = Path(settings.upload_dir).resolve()
_uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_path)), name="uploads")

# 添加日志中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(ApiPrefixRewriteMiddleware)

# 注册全局异常处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 初始化并注册三个模块的路由
app.include_router(init_guanwang_module())
app.include_router(init_app_module())
app.include_router(init_houtai_module())
app.include_router(init_public_module())

_ADMIN_DIST_DIR = os.getenv("ADMIN_DIST_DIR") or os.getenv("ADMIN_STATIC_DIR")
_admin_dist_path = Path(_ADMIN_DIST_DIR).resolve() if _ADMIN_DIST_DIR else None


@app.get("/api/openapi.json", include_in_schema=False)
async def openapi_json():
    return JSONResponse(
        get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
    )


@app.get("/api/docs", include_in_schema=False)
async def swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - Swagger UI",
    )


@app.get("/api/redoc", include_in_schema=False)
async def redoc():
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - ReDoc",
    )


@app.api_route("/admin/api", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
@app.api_route("/admin/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
async def admin_api_redirect(request: Request, path: str = ""):
    target = f"/api/{path}".rstrip("/")
    return RedirectResponse(url=target or "/api", status_code=307)


@app.api_route("/api/task", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
@app.api_route("/api/task/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
@app.api_route("/api/tasks", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
@app.api_route("/api/tasks/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
async def api_task_compat_redirect(request: Request, path: str = ""):
    suffix = f"/{path}" if path else ""
    return RedirectResponse(url=f"/api/app/tasks{suffix}", status_code=307)


@app.api_route("/api/auth/employee/login", methods=["POST", "OPTIONS"], include_in_schema=False)
@app.api_route("/api/auth/admin/login", methods=["POST", "OPTIONS"], include_in_schema=False)
async def api_auth_compat_redirect(request: Request):
    target = request.url.path.replace("/api/auth/", "/api/app/auth/", 1)
    return RedirectResponse(url=target, status_code=307)


@app.api_route("/api/api", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
@app.api_route("/api/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
async def api_double_api_prefix_redirect(request: Request, path: str = ""):
    target = f"/api/{path}".rstrip("/")
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return RedirectResponse(url=target or "/api", status_code=307)


@app.get("/admin", include_in_schema=False)
@app.get("/admin/{path:path}", include_in_schema=False)
async def admin_spa(path: str = ""):
    if not _admin_dist_path:
        raise HTTPException(status_code=404, detail="admin frontend not configured")
    if not _admin_dist_path.exists() or not _admin_dist_path.is_dir():
        raise HTTPException(status_code=404, detail="admin frontend not found on server")

    clean = (path or "").lstrip("/")
    target = (_admin_dist_path / clean).resolve()
    if target != _admin_dist_path and _admin_dist_path not in target.parents:
        raise HTTPException(status_code=404, detail="invalid path")

    if clean and target.exists() and target.is_file():
        media_type, _ = mimetypes.guess_type(str(target))
        return FileResponse(str(target), media_type=media_type or "application/octet-stream")

    index_path = _admin_dist_path / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="admin index.html not found on server")
    return FileResponse(str(index_path), media_type="text/html; charset=utf-8")


@app.get("/sign", include_in_schema=False)
@app.get("/sign/{path:path}", include_in_schema=False)
async def sign_page_redirect(request: Request, path: str = ""):
    suffix = f"/{path}" if path else ""
    target = f"/admin/sign{suffix}".rstrip("/")
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return RedirectResponse(url=target or "/admin", status_code=307)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "澳州项目后端API",
        "docs": "/docs",
        "version": "1.0.0",
        "modules": {
            "guanwang": "/api/guanwang",
            "app": "/api/app",
            "houtai": "/api/houtai"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    try:
        # uvicorn 已经内置了信号处理机制，会自动处理 SIGTERM 和 SIGINT
        # 不需要自定义信号处理器，让它自己处理可以确保优雅关闭
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8000,
            timeout_keep_alive=30,  # Keep-alive 超时时间（秒）
            timeout_graceful_shutdown=30,  # 优雅关闭超时
            limit_concurrency=1000,  # 最大并发连接数
            limit_max_requests=10000,  # 最大请求数（防止内存泄漏）
            backlog=2048,  # 连接队列大小
        )
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在关闭...")
    except Exception as e:
        logger.error(f"应用运行错误: {e}", exc_info=True)
    finally:
        # 确保资源被清理
        close_db_connections()
        logger.info("应用已关闭")
