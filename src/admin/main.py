import os
import contextlib
import logging
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from src.admin.csrf import CSRFMiddleware
from sqladmin import Admin
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from src.database.session import engine
from src.database.models import User
from src.admin.config import config
from src.admin.auth.backend import AdminAuthBackend
from src.admin.views.payment_settings_view import PaymentSettingsAdmin
from src.admin.views.media_library_view import MediaLibraryView
from src.admin.views.admin_users_view import AdminUserView
from src.admin.api import users, dashboard, flows, media, templates as templates_api, global_menu, flow_import_export

templates = Jinja2Templates(directory="src/admin/templates")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async context manager для жизненного цикла приложения"""
    print("Admin Panel запущена")
    yield
    await engine.dispose()


# Создаем FastAPI приложение
app = FastAPI(title="Bot Constructor Admin Panel", lifespan=lifespan)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Обработчик превышения лимита запросов"""
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Слишком много запросов. Пожалуйста, подождите перед следующей попыткой.",
            "retry_after": str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"
        }
    )


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware для проверки аутентификации на админских роутах"""

    async def dispatch(self, request: Request, call_next):
        # Пути которые требуют аутентификации
        protected_paths = ["/admin", "/dashboard", "/editor"]
        # Исключения - пути для логина и статических файлов
        excluded_paths = ["/admin/login", "/static", "/api", "/editor/assets"]

        path = request.url.path

        # Проверяем если это защищённый путь
        if any(path.startswith(p) for p in protected_paths):
            # Исключаем статические файлы и API
            if not any(path.startswith(e) for e in excluded_paths):
                # Проверяем аутентификацию
                if not request.session.get("admin"):
                    # Не авторизован - редирект на логин
                    return RedirectResponse(url="/admin/login?next=" + path, status_code=302)

        response = await call_next(request)
        return response


class NavigationMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления кнопки навигации и премиум темы на SQLAdmin и Swagger страницы"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path

        # Исключаем пути где не нужна кнопка
        excluded_paths = ["/admin/login"]
        if any(path.startswith(e) for e in excluded_paths):
            return response

        # Добавляем навигацию на /admin/tables, /docs и все подпути
        if "/admin/tables" in path or path.startswith("/docs"):
            # Премиум тёмная тема + кнопка "Назад"
            premium_theme_html = '''
            <link rel="stylesheet" href="/static/css/admin_custom.css">
            
            <a href="/admin" class="admin-nav-back" style="
                position: fixed !important;
                top: 1.5rem !important;
                left: 1.5rem !important;
                z-index: 99999 !important;
                background: #111111 !important;
                padding: 0.5rem 1rem !important;
                border-radius: 8px !important;
                box-shadow: none !important;
                text-decoration: none !important;
                color: #A1A1AA !important;
                font-weight: 500 !important;
                font-size: 0.875rem !important;
                display: block !important;
                transition: all 0.2s !important;
                border: 1px solid #27272A !important;
            " onmouseover="this.style.background='#1A1A1A'; this.style.color='#FFFFFF'; this.style.borderColor='#3F3F46'" onmouseout="this.style.background='#111111'; this.style.color='#A1A1AA'; this.style.borderColor='#27272A'">
            ← Вернуться
            </a>
            '''

            # Пропускаем gzip/compressed ответы — модификация сломает кодировку
            if response.headers.get('content-encoding', '').lower() in ('gzip', 'br', 'deflate'):
                return response

            if hasattr(response, 'body') and response.body:
                try:
                    content = response.body.decode()
                    # Проверяем что это HTML
                    if '<body>' in content:
                        # Добавляем CSS в head
                        if '</head>' in content:
                            content = content.replace('</head>', premium_theme_html + '</head>')
                        else:
                            # Если нет </head>, добавляем в body
                            content = content.replace('<body>', '<body>' + premium_theme_html)
                        response.body = content.encode()
                        if 'content-length' in response.headers:
                            response.headers['content-length'] = str(len(content))
                except Exception:
                    pass  # Если не можем декодировать - пропускаем

        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования API-запросов в аудит-лог."""
    EXCLUDED_PREFIXES = ("/static", "/editor")

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in self.EXCLUDED_PREFIXES):
            return await call_next(request)

        response = await call_next(request)

        # Логируем только API запросы
        if request.url.path.startswith("/api"):
            from src.admin.services.audit_service import add_entry
            user_id = getattr(request.state, "user_id", None) or request.session.get("admin_username")
            add_entry(
                user_id=str(user_id) if user_id else None,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                client_ip=request.client.host if request.client else "",
            )

        return response


@app.get("/api/audit-logs", tags=["audit"])
async def get_audit_logs(limit: int = 100):
    """Получить последние записи аудит-лога."""
    from src.admin.services.audit_service import get_entries
    return {"entries": get_entries(limit=min(limit, 1000)), "total": len(get_entries())}



# CORS middleware - добавляем ПЕРВЫМ (выполняется ПОСЛЕДНИМ)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-ID", "X-CSRF-Token"],
)

# CSRF protection для mutating API requests
app.add_middleware(CSRFMiddleware)
# AuditMiddleware для логирования API запросов
app.add_middleware(AuditMiddleware)
# AuthMiddleware добавляем ВТОРЫМ
app.add_middleware(AuthMiddleware)
# NavigationMiddleware для кнопки "Назад"
app.add_middleware(NavigationMiddleware)
# SessionMiddleware добавляем ТРЕТЬИМ (выполняется ПЕРВЫМ)
# Добавляем max_age для сессии (30 минут = 1800 секунд)
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    max_age=1800,  # 30 минут
    https_only=os.getenv("ENABLE_HTTPS", "false").lower() == "true",  # true для production с HTTPS
    same_site="lax"  # Защита от CSRF атак
)

# Создаем backend аутентификации
authentication_backend = AdminAuthBackend(secret_key=config.SECRET_KEY)

# Создаем админ-панель с аутентификацией
admin = Admin(
    app,
    engine,
    authentication_backend=authentication_backend,
    base_url="/admin/tables"  # SQLAdmin будет доступен на /admin/tables
)

# Регистрируем модели (legacy Lesson/Question/UserProgress views removed)
admin.add_view(AdminUserView)  # Управление пользователями с is_admin
admin.add_view(MediaLibraryView)  # Библиотека медиа файлов
admin.add_view(PaymentSettingsAdmin)  # Настройки оплаты

# Регистрируем API routers (legacy lessons router removed)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(flows.router)
app.include_router(media.router)
app.include_router(templates_api.router)
app.include_router(global_menu.router)
app.include_router(flow_import_export.router)

# Rate limiting на все API endpoints (кроме login, где уже есть отдельный лимит)
from slowapi.middleware import SlowAPIMiddleware
app.add_middleware(SlowAPIMiddleware)

# Mount static files with no-cache for development
from starlette.responses import Response

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, Response):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.mount("/static", NoCacheStaticFiles(directory="src/admin/static"), name="static")

# Mount frontend static files
app.mount("/editor", StaticFiles(directory="src/admin/frontend/dist", html=True), name="editor")


@app.get("/")
async def root():
    """Корневой маршрут"""
    return {"message": "Bot Constructor Admin Panel"}


@app.get("/dashboard")
async def dashboard_page(request: Request):
    """Визуальный дашборд с графиками и воронкой"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/admin")
async def admin_home(request: Request):
    """Главная страница админки с навигацией"""
    return templates.TemplateResponse("admin_home.html", {
        "request": request,
    })


@app.get("/admin/login")
async def admin_login(request: Request):
    """Страница входа в админку"""
    return templates.TemplateResponse("login.html", {
        "request": request,
    })


@app.post("/admin/login")
@limiter.limit("5/minute")  # Максимум 5 попыток входа в минуту
async def admin_login_post(request: Request):
    """Обработка формы входа с rate limiting"""
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    next_url = form.get("next", "/admin")

    from src.admin.auth.dependencies import authenticate_admin

    if authenticate_admin(username, password):
        # При успешной аутентификации обновляем сессию и время последней активности
        request.session.update({
            "admin": True,
            "last_activity": datetime.utcnow().isoformat()
        })
        logger.info(f"Admin '{username}' logged in successfully from {request.client.host}")
        return RedirectResponse(url=next_url, status_code=302)
    else:
        logger.warning(f"Failed login attempt for '{username}' from {request.client.host}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверный логин или пароль"
        })


@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Выход из админки"""
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.admin.main:app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        reload=True
    )
