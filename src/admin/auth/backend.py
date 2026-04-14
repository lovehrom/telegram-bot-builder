from starlette.requests import Request
from sqladmin.authentication import AuthenticationBackend
from src.admin.auth.dependencies import authenticate_admin, ADMIN_SESSION_TTL
import time


class AdminAuthBackend(AuthenticationBackend):
    """Authentication backend for SQLAdmin"""

    async def login(self, request: Request) -> bool:
        """Handle admin login"""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if authenticate_admin(username, password):
            # Store session с timestamp
            request.session.update({"admin": True, "login_time": time.time()})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        """Handle admin logout"""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """#8: Проверка авторизации с TTL (4 часа)"""
        if not request.session.get("admin", False):
            return False
        login_time = request.session.get("login_time")
        if login_time is None:
            return False
        # Проверяем TTL
        if time.time() - login_time > ADMIN_SESSION_TTL:
            request.session.clear()
            return False
        return True
