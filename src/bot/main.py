import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src.bot.config import config
from src.bot.dp import dp
# DatabaseMiddleware подключён через dp.update.middleware в dp.py
from src.bot.handlers import start, payment, admin, flow, main_menu


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def periodic_cleanup():
    """Периодическая очистка зависших состояний flow (#8)"""
    from src.database.session import async_session_maker
    from src.database.models import UserFlowState
    while True:
        try:
            await asyncio.sleep(6 * 3600)  # Каждые 6 часов
            async with async_session_maker() as session:
                cleaned = await UserFlowState.cleanup_stale_states(session)
                logger.info(f"Периодическая очистка: удалено {cleaned} зависших states")
        except Exception as e:
            logger.error(f"Ошибка периодической очистки: {e}")


async def main():
    """Главная функция запуска бота"""
    # Создаем бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # DatabaseMiddleware уже подключён через dp.update.middleware

    # Регистрируем роутеры: flow router ПЕРЕД main_menu (#6)
    # Чтобы flow мог перехватить текстовые сообщения от пользователя
    dp.include_router(start.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    dp.include_router(flow.router)
    dp.include_router(main_menu.router)  # Главное меню — fallback, последний

    # Запускаем фоновую очистку (#8)
    asyncio.create_task(periodic_cleanup())

    # Запускаем поллинг
    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Бот остановлен")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
