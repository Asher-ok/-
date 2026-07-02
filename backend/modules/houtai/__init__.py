"""
后台模块初始化（管理后台后端）
"""
from fastapi import APIRouter
from .api import (
    admin_impersonation,
    employees,
    customers,
    customer_documents,
    template_files,
    incident_reports,
    incident_templates,
    leave_requests,
    updates,
    tasks,
    questionnaires,
    qualifications,
    task_record_templates,
    task_records,
    export,
    invoices
)


def init_houtai_module() -> APIRouter:
    """
    初始化后台模块
    返回配置好的 APIRouter
    """
    # 创建主路由，各个子路由已经包含 /api/houtai 前缀
    router = APIRouter()
    
    # 注册后台模块路由
    router.include_router(admin_impersonation.router)
    router.include_router(employees.router)
    router.include_router(customers.router)
    router.include_router(customer_documents.router)
    router.include_router(template_files.router)
    router.include_router(incident_reports.router)
    router.include_router(incident_templates.router)
    router.include_router(leave_requests.router)
    router.include_router(updates.router)
    router.include_router(tasks.router)
    router.include_router(questionnaires.router)
    router.include_router(qualifications.router)
    router.include_router(task_record_templates.router)
    router.include_router(task_records.router)
    router.include_router(export.router)
    router.include_router(invoices.router)

    return router
