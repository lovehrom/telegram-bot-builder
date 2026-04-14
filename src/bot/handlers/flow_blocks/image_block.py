from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler


@register_handler
class ImageBlockHandler(BlockHandler):
    """Обработчик блока изображений"""

    block_type = "image"

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Отправить изображение пользователю"""
        config = block.config

        photo_file_id = config.get('photo_file_id')
        caption = config.get('caption', '')
        parse_mode = config.get('parse_mode', 'HTML')
        protect_content = config.get('protect_content', True)

        if not photo_file_id:
            await message.answer("⚠️ Изображение не найдено")
            return

        await message.answer_photo(
            photo_file_id,
            caption=caption if caption else None,
            parse_mode=parse_mode if caption else None,
            protect_content=protect_content
        )

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию блока изображения"""
        if 'photo_file_id' not in config:
            return False, "Image block requires 'photo_file_id' field"

        if not isinstance(config['photo_file_id'], str):
            return False, "'photo_file_id' must be a string"

        if len(config['photo_file_id']) == 0:
            return False, "'photo_file_id' cannot be empty"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """Блок изображений имеет единственный выход"""
        return None
