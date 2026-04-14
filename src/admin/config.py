import os
import secrets
from dotenv import load_dotenv

load_dotenv()


class AdminConfig:
    """Конфигурация админ-панели с валидацией"""

    def __init__(self):
        # Admin credentials - ОБЯЗАТЕЛЬНЫЕ параметры без дефолтных значений
        self.ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "")
        self.ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

        # Secret key for sessions - ОБЯЗАТЕЛЬНЫЙ параметр
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "")

        # Web server configuration
        self.WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
        self.WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))

        # Validate required credentials
        self._validate_credentials()

    def _validate_credentials(self):
        """Проверка наличия и корректности креденшлов"""
        if not self.ADMIN_USERNAME:
            raise ValueError(
                "ADMIN_USERNAME not set! Please set ADMIN_USERNAME in .env file. "
                "See .env.example for reference."
            )
        if not self.ADMIN_PASSWORD:
            raise ValueError(
                "ADMIN_PASSWORD not set! Please set ADMIN_PASSWORD in .env file. "
                "See .env.example for reference."
            )
        if len(self.ADMIN_PASSWORD) < 8:
            raise ValueError(
                "ADMIN_PASSWORD must be at least 8 characters long! "
                "Current length: {} characters. Please use a stronger password.".format(
                    len(self.ADMIN_PASSWORD)
                )
            )
        if not self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY not set! Please generate a secure key using:\n"
                "python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
                "Then add it to .env file as SECRET_KEY=<generated_key>"
            )
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long for security! "
                "Current length: {} characters.".format(len(self.SECRET_KEY))
            )


config = AdminConfig()
