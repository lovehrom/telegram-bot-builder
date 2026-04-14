"""
Модуль для обработки ошибок с классификацией и структурированным логированием.

Предоставляет специальные исключения для различных типов ошибок
и функции для их обработки.
"""

import logging
from typing import Optional
from aiogram.types import Message

logger = logging.getLogger(__name__)


# ===========================
# Custom Exceptions
# ===========================

class FlowExecutionError(Exception):
    """Базовое исключение для ошибок выполнения flow"""
    def __init__(self, message: str, flow_id: Optional[int] = None, block_id: Optional[int] = None):
        self.message = message
        self.flow_id = flow_id
        self.block_id = block_id
        super().__init__(self.message)

    def __str__(self):
        details = []
        if self.flow_id:
            details.append(f"flow_id={self.flow_id}")
        if self.block_id:
            details.append(f"block_id={self.block_id}")
        details_str = ", ".join(details) if details else "no details"
        return f"[{details_str}] {self.message}"


class BlockExecutionError(FlowExecutionError):
    """Ошибка при выполнении конкретного блока"""
    pass


class DatabaseError(FlowExecutionError):
    """Ошибка при работе с базой данных"""
    pass


class ValidationError(FlowExecutionError):
    """Ошибка валидации данных"""
    pass


class UserError(FlowExecutionError):
    """Ошибка связанная с пользователем (не найден, нет прав и т.д.)"""
    pass


class ConfigurationError(FlowExecutionError):
    """Ошибка конфигурации flow или блока"""
    pass


# ===========================
# Error Handlers
# ===========================

async def handle_flow_execution_error(
    error: Exception,
    message: Message,
    flow_id: Optional[int] = None,
    block_id: Optional[int] = None,
    user_facing_message: Optional[str] = None
) -> None:
    """
    Обработать ошибку выполнения flow с логированием и ответом пользователю

    Args:
        error: Исключение
        message: Aiogram Message объект для ответа
        flow_id: ID flow (для логирования)
        block_id: ID блока (для логирования)
        user_facing_message: Кастомное сообщение для пользователя
    """
    # Классифицируем ошибку
    if isinstance(error, FlowExecutionError):
        # Наши кастомные ошибки
        error_type = type(error).__name__
        logger.error(
            f"Flow execution error: {error_type}: {error}",
            extra={
                "flow_id": getattr(error, 'flow_id', flow_id),
                "block_id": getattr(error, 'block_id', block_id),
                "error_type": error_type
            },
            exc_info=True
        )

        # Сообщение пользователю
        if user_facing_message:
            await message.answer(user_facing_message)
        else:
            await message.answer("⚠️ Произошла ошибка при выполнении сценария")

    elif isinstance(error, (ValueError, KeyError, AttributeError, TypeError)):
        # Ошибки данных/типов
        logger.error(
            f"Data error in flow: {type(error).__name__}: {error}",
            extra={"flow_id": flow_id, "block_id": block_id},
            exc_info=True
        )
        await message.answer("⚠️ Неверный формат данных в сценарии")

    elif isinstance(error, PermissionError):
        # Ошибки прав доступа
        logger.warning(
            f"Permission error: {error}",
            extra={"flow_id": flow_id, "block_id": block_id}
        )
        await message.answer("⛔ У вас нет прав для этого действия")

    else:
        # Неожиданная ошибка
        logger.critical(
            f"Unexpected error in flow execution: {type(error).__name__}: {error}",
            extra={"flow_id": flow_id, "block_id": block_id},
            exc_info=True
        )
        await message.answer("❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")


async def handle_database_error(
    error: Exception,
    operation: str,
    context: Optional[dict] = None
) -> None:
    """
    Обработать ошибку базы данных

    Args:
        error: Исключение
        operation: Описание операции (например, "update user progress")
        context: Дополнительный контекст (для логирования)
    """
    logger.error(
        f"Database error during '{operation}': {type(error).__name__}: {error}",
        extra=context or {},
        exc_info=True
    )


async def handle_validation_error(
    error: Exception,
    field_name: str,
    message: Message
) -> None:
    """
    Обработать ошибку валидации

    Args:
        error: Исключение
        field_name: Имя поля которое не прошло валидацию
        message: Aiogram Message объект для ответа
    """
    logger.warning(
        f"Validation error for field '{field_name}': {error}",
        exc_info=False
    )
    await message.answer(f"⚠️ Неверное значение поля: {field_name}")


def safe_execute(
    operation: str,
    error_message: str = "Operation failed",
    raise_on_error: bool = False
):
    """
    Декоратор для безопасного выполнения функций с обработкой ошибок

    Args:
        operation: Название операции (для логирования)
        error_message: Сообщение об ошибке
        raise_on_error: Пересылать ли исключение после логирования

    Usage:
        @safe_execute("update user progress")
        async def my_function():
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"{operation} failed: {type(e).__name__}: {e}",
                    exc_info=True
                )
                if raise_on_error:
                    raise
                return None
        return wrapper
    return decorator


# ===========================
# Error Context Managers
# ===========================

class ErrorContext:
    """Контекст менеджер для отслеживания ошибок с контекстом"""

    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.context["operation"] = operation

    async def __aenter__(self):
        logger.debug(f"Starting: {self.operation}", extra=self.context)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            logger.debug(f"Completed: {self.operation}", extra=self.context)
            return False

        # Произошла ошибка
        logger.error(
            f"Error in {self.operation}: {exc_type.__name__}: {exc_val}",
            extra=self.context,
            exc_info=(exc_type, exc_val, exc_tb)
        )

        # Не подавляем исключение
        return False


# ===========================
# User-Facing Error Messages
# ===========================

USER_ERRORS = {
    "flow_not_found": "Сценарий не найден. Пожалуйста, обратитесь к администратору.",
    "block_not_found": "Ошибка в сценарии: блок не найден.",
    "invalid_configuration": "Ошибка конфигурации сценария.",
    "database_error": "Ошибка базы данных. Пожалуйста, попробуйте позже.",
    "user_not_found": "Пользователь не найден. Нажмите /start для регистрации.",
    "access_denied": "У вас нет прав для этого действия.",
    "invalid_input": "Неверный формат данных. Пожалуйста, попробуйте снова.",
    "timeout": "Время ожидания истекло. Пожалуйста, попробуйте снова.",
}


def get_user_error(error_key: str, default: str = "Произошла ошибка") -> str:
    """
    Получить пользовательское сообщение об ошибке

    Args:
        error_key: Ключ ошибки из USER_ERRORS
        default: Сообщение по умолчанию

    Returns:
        str: Сообщение об ошибке для пользователя
    """
    return USER_ERRORS.get(error_key, default)
