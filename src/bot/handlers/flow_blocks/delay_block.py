import asyncio
import logging
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler
class DelayBlockHandler(BlockHandler):
    """
    Обработчик блока задержки

    Создает паузу в выполнении flow на указанное количество секунд.
    """

    block_type = "delay"

    @property
    def awaits_user_input(self) -> bool:
        """Delay block не ждёт ввода — автоматический переход после задержки"""
        return False

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """
        Задержка перед переходом к следующему блоку

        Args:
            block: Блок задержки
            state: Состояние flow пользователя
            message: Сообщение от пользователя
            session: Сессия базы данных
            executor: Flow executor (не используется)
        """
        config = block.config

        duration = config.get('duration', 5)  # секунды

        logger.info(
            f"Delay block: pausing for {duration}s for user {state.user_id}, "
            f"flow {state.flow_id}"
        )

        # Синхронная задержка - блокирует выполнение flow на указанное время
        await asyncio.sleep(duration)

        logger.info(
            f"Delay block: {duration}s delay completed for user {state.user_id}"
        )

        # После задержки executor автоматически перейдет к следующему блоку

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """
        Валидировать конфигурацию блока задержки

        Args:
            config: Конфигурация блока

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if 'duration' in config:
            if not isinstance(config['duration'], (int, float)):
                return False, "'duration' must be a number"
            if config['duration'] < 0:
                return False, "'duration' cannot be negative"
            if config['duration'] > 300:  # 5 минут максимум
                return False, "'duration' cannot exceed 300 seconds (5 minutes)"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """Блок задержки автоматически переходит дальше без условия"""
        return None
