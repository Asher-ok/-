"""公开 API 模块（无需登录）"""
from fastapi import APIRouter
from .document_sign import router as document_sign_router
from .employee_contract_sign import router as employee_contract_sign_router


def init_public_module() -> APIRouter:
    router = APIRouter()
    router.include_router(document_sign_router)
    router.include_router(employee_contract_sign_router)
    return router
