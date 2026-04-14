from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from src.bot.config import config
from src.bot.middlewares import DatabaseMiddleware


# Создаем Redis storage
redis = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB
)

storage = RedisStorage(redis=redis)

# Создаем диспетчер
dp = Dispatcher(storage=storage)

# DatabaseMiddleware — инжектит db_session в data для всех handler'ов
dp.update.middleware(DatabaseMiddleware())
