"""
官网模块初始化
"""
from fastapi import APIRouter
from .api import routes as guanwang_routes


def init_guanwang_module() -> APIRouter:
    """
    初始化官网模块
    返回配置好的 APIRouter
    """
    router = guanwang_routes.router
    return router
