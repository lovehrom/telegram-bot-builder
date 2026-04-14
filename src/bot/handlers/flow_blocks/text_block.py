from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler


@register_handler
class TextBlockHandler(BlockHandler):
    """Обработчик текстового блока"""

    block_type = "text"

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Отправить текстовое сообщение пользователю"""
        config = block.config

        text = config.get('text', '')
        parse_mode = config.get('parse_mode', 'HTML')
        disable_web_page_preview = config.get('disable_web_page_preview', False)

        await message.answer(
            text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview
        )

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию текстового блока"""
        if 'text' not in config:
            return False, "Text block requires 'text' field"

        if not isinstance(config['text'], str):
            return False, "'text' must be a string"

        if len(config['text']) == 0:
            return False, "'text' cannot be empty"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """Текстовые блоки имеют единственный выход"""
        return None
