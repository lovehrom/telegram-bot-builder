from abc import ABC, abstractmethod
from typing import Any, Coroutine
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState


class BlockHandler(ABC):
    """Базовый класс для всех обработчиков блоков"""

    block_type: str = None

    @property
    def awaits_user_input(self) -> bool:
        """
        Должен ли этот блок ждать ввода пользователя перед переходом к следующему

        Returns:
            True - блок должен паузить flow и ждать callback/ответ
            False - блок автоматически переходит к следующему
        """
        return False

    @abstractmethod
    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor: Any = None
    ) -> None:
        """
        Выполнить логику блока

        Args:
            block: Блок flow для выполнения
            state: Текущее состояние выполнения flow пользователя
            message: Сообщение от пользователя (для ответа)
            session: Сессия базы данных
            executor: Опционально - экземпляр FlowExecutor для дополнительных операций
        """
        pass

    async def get_next_condition(
        self,
        block: FlowBlock,
        user_response: Any = None,
        state: UserFlowState = None
    ) -> str | None:
        """
        Определить условие для перехода к следующему блоку

        Args:
            block: Текущий блок
            user_response: Ответ пользователя (если применимо)
            state: Текущее состояние flow пользователя (для блокам которым нужен контекст)

        Returns:
            Условие для выбора следующего блока (например, 'correct', 'wrong', 'paid', etc.)
            или None для перехода по единственному соединению
        """
        return None

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """
        Валидировать конфигурацию блока

        Args:
            config: Словарь с конфигурацией блока

        Returns:
            (is_valid, error_message) - кортеж с флагом валидности и сообщением об ошибке
        """
        return True, ""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(type='{self.block_type}')>"


# Реестр обработчиков блоков
BLOCK_HANDLERS: dict[str, type[BlockHandler]] = {}


def register_handler(handler_class: type[BlockHandler]) -> type[BlockHandler]:
    """
    Декоратор для регистрации обработчика блока

    Usage:
        @register_handler
        class TextBlockHandler(BlockHandler):
            block_type = 'text'
            ...
    """
    if not handler_class.block_type:
        raise ValueError(f"Handler {handler_class.__name__} must define block_type")

    BLOCK_HANDLERS[handler_class.block_type] = handler_class
    return handler_class


def get_handler(block_type: str) -> BlockHandler | None:
    """
    Получить экземпляр обработчика для типа блока

    Args:
        block_type: Тип блока

    Returns:
        Экземпляр обработчика или None, если тип не найден
    """
    handler_class = BLOCK_HANDLERS.get(block_type)
    if handler_class:
        return handler_class()
    return None
