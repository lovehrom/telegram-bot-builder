from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler


@register_handler
class VideoBlockHandler(BlockHandler):
    """Обработчик видео блока"""

    block_type = "video"

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Отправить видео пользователю"""
        config = block.config

        video_file_id = config.get('video_file_id')
        caption = config.get('caption', '')
        parse_mode = config.get('parse_mode', 'HTML')
        protect_content = config.get('protect_content', True)

        if not video_file_id:
            await message.answer("⚠️ Видео не найдено")
            return

        await message.answer_video(
            video_file_id,
            caption=caption if caption else None,
            parse_mode=parse_mode if caption else None,
            protect_content=protect_content
        )

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию видео блока"""
        if 'video_file_id' not in config:
            return False, "Video block requires 'video_file_id' field"

        if not isinstance(config['video_file_id'], str):
            return False, "'video_file_id' must be a string"

        if len(config['video_file_id']) == 0:
            return False, "'video_file_id' cannot be empty"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """Видео блоки имеют единственный выход"""
        return None
