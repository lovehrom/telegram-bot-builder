import logging
from aiogram import Router, F
from aiogram.types import Message
from src.bot.filters.admin_filter import IsAdmin
from src.bot.config import config

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.video, IsAdmin(config.ADMIN_IDS))
async def admin_receive_video(message: Message, db_session):
    """
    Админ получает file_id загруженного видео

    Требуется двойная проверка:
    1. Проверка ADMIN_IDS из конфига
    2. Проверка is_admin в базе данных
    """
    from src.bot.services.user_service import get_user_by_telegram_id

    user = await get_user_by_telegram_id(db_session, message.from_user.id)

    if not user:
        await message.answer(
            "⛔ Пользователь не найден в базе данных.\n"
            "Нажмите /start для регистрации."
        )
        logger.warning(
            f"Unauthorized admin attempt: user {message.from_user.id} not in database"
        )
        return

    if not user.is_admin:
        await message.answer(
            "⛔ У вас нет прав администратора.\n"
            "Обратитесь к владельцу бота."
        )
        logger.warning(
            f"Unauthorized admin attempt: user {message.from_user.id} "
            f"(username: {user.username}) is not marked as admin in database"
        )
        return

    # Пользователь имеет права администратора
    file_id = message.video.file_id

    text = (
        f"📹 <b>File ID видео:</b>\n\n"
        f"<code>{file_id}</code>\n\n"
        f"Скопируйте этот ID и вставьте в админ-панель."
    )

    await message.answer(text)
    logger.info(
        f"Admin {message.from_user.id} retrieved video file_id: {file_id}"
    )
