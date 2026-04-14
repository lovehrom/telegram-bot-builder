import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    """Конфигурация бота"""
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [
        int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()
    ]

    # Redis (FSM storage)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))



config = BotConfig()
