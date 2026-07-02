"""
应用模块初始化（移动应用后端）
"""
from fastapi import APIRouter
from .api import auth, employees, tasks, customers, questionnaires, incident_reports, leave_requests, task_cancellation_notifications, updates, task_records


def init_app_module() -> APIRouter:
    """
    初始化应用模块
    返回配置好的 APIRouter
    """
    # 创建主路由，各个子路由已经包含 /api/app 前缀
    router = APIRouter()
    
    # 注册应用模块路由
    router.include_router(auth.router)
    router.include_router(employees.router)
    router.include_router(tasks.router)
    router.include_router(customers.router)
    router.include_router(questionnaires.router)
    router.include_router(incident_reports.router)
    router.include_router(task_records.router)
    router.include_router(leave_requests.router)
    router.include_router(task_cancellation_notifications.router)
    router.include_router(updates.router)

    return router
