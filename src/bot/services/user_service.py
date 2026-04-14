import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.database.models import User

logger = logging.getLogger(__name__)


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str = None,
    full_name: str = None
) -> User:
    """Получить или создать пользователя"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name
        )
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            # Race condition: другой процесс уже создал пользователя
            await session.rollback()
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one()
        await session.refresh(user)
        logger.info(f"Created new user: telegram_id={telegram_id}, username={username}")

    return user


async def get_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int
) -> User | None:
    """Получить пользователя по telegram_id"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


# Функция update_lesson_progress() удалена:
# поле current_lesson_number удалено из модели User.
# Используйте FlowProgress для отслеживания прогресса.


async def set_paid_status(
    session: AsyncSession,
    user: User,
    is_paid: bool
) -> User:
    """Установить статус оплаты с защитой от race conditions"""
    try:
        result = await session.execute(
            select(User)
            .where(User.id == user.id)
            .with_for_update()
        )
        locked_user = result.scalar_one()

        locked_user.is_paid = is_paid
        await session.commit()
        await session.refresh(locked_user)
        logger.info(
            f"Updated paid status for user {user.telegram_id}: is_paid={is_paid}"
        )
        return locked_user

    except Exception as e:
        logger.error(
            f"Error setting paid status for user {user.telegram_id}: {e}",
            exc_info=True
        )
        await session.rollback()
        raise