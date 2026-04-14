from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.database.session import get_async_session
from src.admin.services.statistics_service import StatisticsService
from src.database.models import ConversationFlow
from src.admin.auth.dependencies import verify_api_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats/dashboard")
async def get_dashboard_stats(session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """
    Получить статистику дашборда

    Возвращает метрики:
    - Пользователи: всего, платных, новых за неделю, конверсия
    - Flows: всего, активных
    - Прогресс: попыток, сдано, pass rate, средний балл
    """
    try:
        service = StatisticsService(session)
        return await service.get_dashboard_stats()
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка получения статистики дашборда. Попробуйте позже.")


@router.get("/stats/full")
async def get_full_dashboard_stats(session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """
    Получить полную статистику для визуального дашборда

    Возвращает:
    - Базовую статистику
    - Воронку пользователей с конверсией
    - Таймлайн активности
    - Статистику по flows
    """
    try:
        service = StatisticsService(session)

        basic_stats = await service.get_dashboard_stats()
        funnel = await service.get_funnel_stats()
        timeline = await service.get_activity_timeline(days=7)
        flow_stats = await service.get_flow_completion_stats()

        return {
            "users": basic_stats["users"],
            "flows": basic_stats["flows"],
            "progress": basic_stats["progress"],
            "funnel": funnel["funnel"],
            "conversion_rates": funnel["conversion_rates"],
            "timeline": timeline,
            "flow_stats": flow_stats
        }
    except Exception as e:
        logger.error(f"Error getting full dashboard stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка получения полной статистики. Попробуйте позже.")


@router.get("/quick-stats")
async def get_quick_stats(session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Быстрая статистика для главной страницы админки"""
    try:
        service = StatisticsService(session)

        # Используем существующий метод get_dashboard_stats
        basic_stats = await service.get_dashboard_stats()

        # Получаем количество сценариев (flows)
        total_flows_result = await session.execute(
            select(func.count()).select_from(ConversationFlow)
        )
        total_flows = total_flows_result.scalar() or 0

        return {
            "total_users": basic_stats["users"]["total"],
            "active_today": basic_stats["users"].get("active_week", 0),
            "paid_users": basic_stats["users"]["paid"],
            "total_flows": total_flows,
        }
    except Exception as e:
        logger.error(f"Error getting quick stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка получения быстрой статистики. Попробуйте позже.")
