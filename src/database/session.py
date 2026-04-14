from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from .config import get_database_url
from .base import Base


# Создание движка
engine = create_async_engine(
    get_database_url(),
    echo=False,  # True для отладки SQL запросов
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection для получения сессии"""
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Создание таблиц (для разработки)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
