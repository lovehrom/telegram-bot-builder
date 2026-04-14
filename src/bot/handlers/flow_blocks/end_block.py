from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler


@register_handler
class EndBlockHandler(BlockHandler):
    """Обработчик конечного блока"""

    block_type = "end"

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Конечный блок - отправляет финальное сообщение"""
        config = block.config
        final_message = config.get('final_message', '✅ Вы завершили этот flow!')

        await message.answer(final_message)

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Конечный блок не требует обязательной конфигурации"""
        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """Конечный блок не имеет выходов"""
        return None
