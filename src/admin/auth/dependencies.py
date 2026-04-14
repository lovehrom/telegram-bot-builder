import os
import hmac
import time
import logging
from typing import Optional
from fastapi import HTTPException, Request
from passlib.context import CryptContext
from src.admin.config import config

logger = logging.getLogger(__name__)

# #8: TTL сессии админки (4 часа)
ADMIN_SESSION_TTL = 4 * 60 * 60  # секунды

# Контекст для хеширования паролей с использованием bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля против хеша

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль

    Returns:
        bool: True если пароль совпадает, иначе False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хеширование пароля

    Args:
        password: Пароль в открытом виде

    Returns:
        str: Хешированный пароль
    """
    return pwd_context.hash(password)


def authenticate_admin(username: str, password: str) -> bool:
    """
    Проверка логина и пароля админа с поддержкой bcrypt

    Поддерживает два режима:
    1. Если пароль в конфиге начинается с '$2b$' (bcrypt hash) - сверяет с хешем
    2. Если пароль в конфиге в открытом виде - сравнивает напрямую
       (для обратной совместимости, рекомендуется мигрировать на хеши)

    Args:
        username: Имя пользователя
        password: Пароль в открытом виде

    Returns:
        bool: True если аутентификация успешна, иначе False
    """
    # Проверка имени пользователя
    if username != config.ADMIN_USERNAME:
        logger.warning(f"Admin login failed: invalid username '{username}'")
        return False

    # Проверка пароля
    stored_password = config.ADMIN_PASSWORD

    # Если пароль уже хеширован (bcrypt hash начинается с $2b$)
    if stored_password.startswith('$2b$'):
        success = verify_password(password, stored_password)
        if success:
            logger.info(f"Admin login successful: username='{username}' (with bcrypt)")
        else:
            logger.warning(f"Admin login failed: invalid password for username '{username}'")
        return success
    else:
        # Обратная совместимость: пароль в открытом виде
        # ⚠️  Рекомендуется мигрировать на bcrypt хеши!
        success = password == stored_password
        if success:
            logger.info(f"Admin login successful: username='{username}' (PLAIN TEXT - migrating to bcrypt!)")
            # #12: Автоматическое хеширование plaintext пароля при первом успешном логине
            try:
                hashed = get_password_hash(stored_password)
                config.ADMIN_PASSWORD = hashed
                logger.info(f"Пароль админа автоматически мигрирован в bcrypt hash")
            except Exception as e:
                logger.error(f"Не удалось захешировать пароль при авто-миграции: {e}")
        else:
            logger.warning(f"Admin login failed: invalid password for username '{username}'")
        return success


def hash_admin_password(plain_password: str) -> str:
    """
    Вспомогательная функция для генерации bcrypt хеша пароля админа

    Использование:
        python -c "from src.admin.auth.dependencies import hash_admin_password; print(hash_admin_password('your_password'))"

    Args:
        plain_password: Пароль в открытом виде

    Returns:
        str: bcrypt хеш пароля
    """
    return get_password_hash(plain_password)


# ===========================
# API Token Authentication
# ===========================

async def verify_api_token(request: Request) -> bool:
    """
    Проверка API токена для защиты API endpoints

    Токен передается в заголовке X-API-Token

    Args:
        request: FastAPI Request объект

    Returns:
        bool: True если токен валиден

    Raises:
        HTTPException: Если токен отсутствует или неверный
    """
    # Получаем токен из заголовка
    token = request.headers.get("X-API-Token")

    # Проверяем наличие токена
    if not token:
        logger.warning(f"API request without X-API-Token header from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Требуется аутентификация. Укажите X-API-Token заголовок."
        )

    # Получаем ожидаемый токен из переменных окружения
    expected_token = os.getenv("API_TOKEN")

    # Если API_TOKEN не задан в конфиге - разрешаем доступ (для обратной совместимости)
    # ⚠️  В production ВСЕГДА должен быть задан API_TOKEN!
    if not expected_token:
        logger.warning(
            "⚠️  SECURITY WARNING: API_TOKEN not set in environment! "
            "API endpoints are unprotected. Please set API_TOKEN in .env file."
        )
        return True

    # Защита от timing-атак: используем постоянное время сравнения
    if not hmac.compare_digest(token, expected_token):
        logger.warning(f"Invalid API token from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Неверный токен аутентификации"
        )

    logger.debug(f"API token validated for request from {request.client.host}")
    return True


async def verify_api_token_optional(request: Request) -> Optional[bool]:
    """
    Опциональная проверка API токена (для endpoints, которые могут работать без токена)

    Args:
        request: FastAPI Request объект

    Returns:
        Optional[bool]: True если токен валиден, None если токен не указан

    Raises:
        HTTPException: Если токен указан но неверный
    """
    token = request.headers.get("X-API-Token")

    # Если токен не указан - возвращаем None (аутентификация не выполнена)
    if not token:
        return None

    # Если токен указан - проверяем его
    expected_token = os.getenv("API_TOKEN")

    if not expected_token:
        logger.warning(
            "⚠️  SECURITY WARNING: API_TOKEN not set in environment!"
        )
        return True

    # Защита от timing-атак: используем постоянное время сравнения
    if not hmac.compare_digest(token, expected_token):
        logger.warning(f"Invalid API token from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Неверный токен аутентификации"
        )

    return True
