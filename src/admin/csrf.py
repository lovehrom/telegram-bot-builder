"""
CSRF Protection для Admin API.

Использует double-submit cookie pattern:
- Сервер генерирует CSRF токен, кладёт в cookie и возвращает в ответе
- Клиент отправляет токен в заголовке X-CSRF-Token при POST/PUT/DELETE
- Сервер сравнивает токен из cookie с токеном из заголовка
"""
import os
import secrets
import hashlib
import hmac
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_SECRET = os.getenv("CSRF_SECRET", "")


def generate_csrf_token(session_id: str) -> str:
    """Генерирует CSRF токен на основе session_id и секрета."""
    if not CSRF_SECRET:
        # Fallback: простой random token (менее безопасно)
        return secrets.token_hex(32)
    msg = f"{session_id}:{CSRF_SECRET}".encode()
    return hmac.new(CSRF_SECRET.encode(), msg, hashlib.sha256).hexdigest()


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware для проверки CSRF токена на mutating requests."""

    # Путь, которые не требуют CSRF проверки
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    EXEMPT_PATHS = {"/admin/login", "/api/auth/login", "/docs", "/openapi.json"}

    async def dispatch(self, request, call_next):
        path = request.url.path

        # Пропускаем safe methods
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # Пропускаем exempt paths
        if any(path.startswith(p) for p in self.EXEMPT_PATHS):
            return await call_next(request)

        # Пропускаем запросы с API token (server-to-server, нет cookies)
        if request.headers.get("X-API-Token") or request.headers.get("Authorization", "").startswith("Bearer "):
            return await call_next(request)

        # Для API запросов проверяем CSRF токен
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            logger.warning(f"CSRF tokens missing for {request.method} {path}")
            return JSONResponse(status_code=403, content={"detail": "CSRF token missing"})

        if not hmac.compare_digest(cookie_token, header_token):
            logger.warning(f"CSRF token mismatch for {request.method} {path}")
            return JSONResponse(status_code=403, content={"detail": "CSRF token invalid"})

        return await call_next(request)
