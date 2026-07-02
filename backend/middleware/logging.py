"""
日志中间件
"""
import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_host = request.client.host if request.client else 'unknown'
        
        # 记录请求信息
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {client_host}"
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"Response: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            # 添加处理时间头
            response.headers["X-Process-Time"] = str(process_time)
            
            # 添加 Connection 头，明确连接管理
            # 如果客户端断开连接，服务器应该能够检测到并清理连接
            if "Connection" not in response.headers:
                response.headers["Connection"] = "keep-alive"
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} - "
                f"Time: {process_time:.3f}s - "
                f"Error: {str(e)}",
                exc_info=True
            )
            raise
