import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.session import get_async_session
from src.database.models import User
from src.admin.auth.dependencies import verify_api_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/telegram/{telegram_id}")
async def get_user_by_telegram(
    telegram_id: int,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """
    Получить пользователя по Telegram ID (защищено API токеном)

    Используется ботом для проверки статуса пользователя и оплаты

    Headers:
        X-API-Token: Ваш API токен (настраивается в .env как API_TOKEN)
    """
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User not found: telegram_id={telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")

    logger.debug(f"Retrieved user data for telegram_id={telegram_id}")
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "full_name": user.full_name,
        "is_paid": user.is_paid,
        "is_admin": user.is_admin
    }


@router.post("/telegram/{telegram_id}/payment")
async def mark_user_paid(
    telegram_id: int,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """
    Отметить пользователя как оплатившего (защищено API токеном)

    Используется ботом или платежной системой после успешной оплаты

    Headers:
        X-API-Token: Ваш API токен (настраивается в .env как API_TOKEN)
    """
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Payment failed: user not found for telegram_id={telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")

    user.is_paid = True
    await session.commit()

    logger.info(f"User {telegram_id} marked as paid via API")
    return {
        "message": "Payment recorded successfully",
        "is_paid": True,
        "telegram_id": telegram_id
    }
