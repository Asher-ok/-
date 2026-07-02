"""
CORS 中间件配置
"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from core.config import settings


def setup_cors(app: FastAPI):
    """配置 CORS 中间件 - 支持国外部署和VPN环境"""
    import os
    
    # 从环境变量获取允许的来源，如果没有则使用默认值
    # 支持通过环境变量配置，方便在不同环境部署
    cors_origins_env = os.getenv("CORS_ORIGINS", "")
    
    if cors_origins_env:
        # 从环境变量读取，支持多个来源用逗号分隔
        allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    else:
        # 默认允许的来源列表（开发和生产环境）
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",  # Vite默认端口
            "http://127.0.0.1:5173",
            # 支持HTTPS
            "https://localhost:3000",
            "https://127.0.0.1:3000",
            # 生产环境前端地址（如果需要）
            "http://176.97.68.115:3000",
            "https://176.97.68.115:3000",
        ]
    
    # 如果是开发环境或允许所有来源（通过环境变量控制）
    allow_all = os.getenv("CORS_ALLOW_ALL", "false").lower() == "true"
    
    if allow_all:
        # 开发/调试模式：允许所有来源（但credentials必须为False）
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,  # 必须为False当allow_origins为["*"]
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            allow_headers=["*"],
            expose_headers=["*"],
            max_age=7200,  # 增加预检请求缓存时间到2小时，减少VPN环境下的请求
        )
    else:
        # 生产环境：明确列出允许的来源
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,  # 允许发送认证信息（Authorization头）
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            allow_headers=["*"],  # 允许所有请求头（包括Authorization, Content-Type等）
            expose_headers=["*"],  # 暴露所有响应头
            max_age=7200,  # 增加预检请求缓存时间到2小时，减少VPN环境下的请求
        )
