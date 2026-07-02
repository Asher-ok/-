from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class ApiPrefixRewriteMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = str(request.scope.get("path") or "")
        if path.startswith("/api/") or path == "/api":
            return await call_next(request)

        if path == "/docs":
            request.scope["path"] = "/api/docs"
        elif path == "/redoc":
            request.scope["path"] = "/api/redoc"
        elif path == "/openapi.json":
            request.scope["path"] = "/api/openapi.json"
        elif path == "/app" or path.startswith("/app/"):
            request.scope["path"] = f"/api{path}"
        elif path == "/houtai" or path.startswith("/houtai/"):
            request.scope["path"] = f"/api{path}"
        elif path == "/guanwang" or path.startswith("/guanwang/"):
            request.scope["path"] = f"/api{path}"

        return await call_next(request)
