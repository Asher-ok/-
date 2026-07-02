"""
全局中间件模块
"""
from .cors import setup_cors
from .error_handler import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)
from .logging import LoggingMiddleware
from .path_rewrite import ApiPrefixRewriteMiddleware

__all__ = [
    "setup_cors",
    "validation_exception_handler",
    "sqlalchemy_exception_handler",
    "general_exception_handler",
    "LoggingMiddleware",
    "ApiPrefixRewriteMiddleware",
]
