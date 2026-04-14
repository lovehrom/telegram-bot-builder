import os
from dotenv import load_dotenv

load_dotenv()


def get_database_url() -> str:
    """
    Формирует URL для подключения к PostgreSQL

    Поддерживает два формата:
    1. DATABASE_URL - единая строка подключения (Railway, Heroku, и т.д.)
    2. Отдельные переменные POSTGRES_USER, POSTGRES_PASSWORD, DB_HOST, DB_PORT, POSTGRES_DB
    """
    # Приоритет: DATABASE_URL (для Railway, Heroku, и других PaaS)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Если URL начинается с postgresql://, заменить на postgresql+asyncpg://
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
        return database_url

    # Fallback: собрать URL из отдельных переменных (для локальной разработки)
    return (
        f"postgresql+asyncpg://"
        f"{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DB', 'vine_bot')}"
    )
