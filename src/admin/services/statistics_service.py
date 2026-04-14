from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from src.database.models import User, ConversationFlow, FlowProgress


class StatisticsService:
    """Service for gathering statistics using Flows system"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard_stats(self):
        """Получить статистику для дашборда на основе Flows"""
        # Метрики пользователей
        total_users = await self.session.scalar(select(func.count(User.id)))
        paid_users = await self.session.scalar(
            select(func.count(User.id)).where(User.is_paid == True)
        )
        new_users_week = await self.session.scalar(
            select(func.count(User.id)).where(
                User.registration_date >= datetime.utcnow() - timedelta(days=7)
            )
        )

        # Метрики flows
        total_flows = await self.session.scalar(select(func.count(ConversationFlow.id)))
        total_flows_active = await self.session.scalar(
            select(func.count(ConversationFlow.id)).where(ConversationFlow.is_active == True)
        )

        # Метрики прогресса по flows
        total_attempts = await self.session.scalar(select(func.count(FlowProgress.id)))
        passed_tests = await self.session.scalar(
            select(func.count(FlowProgress.id)).where(FlowProgress.passed == True)
        )

        # Средний балл
        avg_score_result = await self.session.execute(
            select(func.avg(
                case(
                    (FlowProgress.total_questions > 0,
                     FlowProgress.score),
                    else_=0
                )
            ))
        )
        avg_score = avg_score_result.scalar() or 0

        # Average progress per flow
        avg_attempts_per_flow = await self.session.execute(
            select(func.avg(FlowProgress.attempts))
        )
        avg_attempts = avg_attempts_per_flow.scalar() or 0

        return {
            "users": {
                "total": total_users,
                "paid": paid_users,
                "free": total_users - paid_users if total_users else 0,
                "new_this_week": new_users_week,
                "conversion_rate": round(paid_users / total_users * 100, 1) if total_users > 0 else 0
            },
            "flows": {
                "total": total_flows,
                "active": total_flows_active
            },
            "progress": {
                "total_attempts": total_attempts,
                "passed": passed_tests,
                "pass_rate": round(passed_tests / total_attempts * 100, 1) if total_attempts > 0 else 0,
                "avg_score": round(avg_score, 1),
                "avg_attempts_per_flow": round(avg_attempts, 1)
            }
        }

    async def get_funnel_stats(self):
        """Получает данные для воронки пользователей"""

        # Этап 1: Всего зарегистрировано
        total_users = await self.session.scalar(select(func.count(User.id)))

        # Этап 2: Начали обучение (продвинулись дальше start блока)
        started_learning = await self.session.scalar(
            select(func.count(User.id))
            .where(User.id.in_(
                select(FlowProgress.user_id)
                .where(FlowProgress.attempts > 0)
            ))
        )

        # Этап 3: Оплатили
        paid_users = await self.session.scalar(
            select(func.count(User.id)).where(User.is_paid == True)
        )

        # Этап 4: Прошли хотя бы 1 flow (passed=True)
        completed_flows = await self.session.scalar(
            select(func.count(func.distinct(FlowProgress.user_id)))
            .where(FlowProgress.passed == True)
        )

        # Этап 5: Завершили все активные flows
        total_flows = await self.session.scalar(select(func.count(ConversationFlow.id)))
        completed_all_flows = await self.session.scalar(
            select(func.count(User.id))
            .where(User.id.in_(
                select(FlowProgress.user_id)
                .where(FlowProgress.passed == True)
            ))
            .where(User.is_paid == True)
        )

        return {
            "funnel": {
                "registered": total_users,
                "started": started_learning,
                "paid": paid_users,
                "completed_flows": completed_flows,
                "completed_all": completed_all_flows
            },
            "conversion_rates": {
                "to_start": round(started_learning / total_users * 100, 1) if total_users > 0 else 0,
                "to_paid": round(paid_users / started_learning * 100, 1) if started_learning > 0 else 0,
                "to_flow": round(completed_flows / paid_users * 100, 1) if paid_users > 0 else 0,
                "to_completion": round(completed_all_flows / completed_flows * 100, 1) if completed_flows > 0 else 0
            }
        }

    async def get_activity_timeline(self, days: int = 7):
        """Получает активность по дням для графика"""
        # #16: Один запрос с GROUP BY вместо N+1
        start_date = datetime.utcnow() - timedelta(days=days - 1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)

        # Новый расчёт: учитываем все дни от start_date до сегодня
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        actual_start = datetime.utcnow() - timedelta(days=days - 1)
        actual_start = actual_start.replace(hour=0, minute=0, second=0, microsecond=0)
        actual_end = today

        # Запрос новых пользователей по дням
        new_users_result = await self.session.execute(
            select(
                func.date(User.registration_date).label('day'),
                func.count(User.id).label('count')
            )
            .where(User.registration_date >= actual_start)
            .where(User.registration_date <= actual_end + timedelta(days=1))
            .group_by(func.date(User.registration_date))
        )

        # Запрос активных пользователей по дням
        active_users_result = await self.session.execute(
            select(
                func.date(User.last_activity).label('day'),
                func.count(User.id).label('count')
            )
            .where(User.last_activity >= actual_start)
            .where(User.last_activity <= actual_end + timedelta(days=1))
            .group_by(func.date(User.last_activity))
        )

        new_users_map = {row.day: row.count for row in new_users_result}
        active_users_map = {row.day: row.count for row in active_users_result}

        # Заполняем все дни
        timeline = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - 1 - i)
            day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_key = day.date() if hasattr(day, 'date') else day
            # Пробуем получить по date объекту
            try:
                date_key = day.date()
            except AttributeError:
                date_key = day

            timeline.append({
                "date": date.strftime("%Y-%m-%d"),
                "new_users": new_users_map.get(date_key, 0) or 0,
                "active_users": active_users_map.get(date_key, 0) or 0
            })

        return timeline

    async def get_flow_completion_stats(self):
        """Статистика прохождения flows"""
        result = await self.session.execute(
            select(
                ConversationFlow.id,
                ConversationFlow.name,
                func.count(FlowProgress.id).label('attempts'),
                func.sum(case((FlowProgress.passed == True, 1), else_=0)).label('passes')
            )
            .join(FlowProgress, ConversationFlow.id == FlowProgress.flow_id)
            .group_by(ConversationFlow.id, ConversationFlow.name)
            .having(func.count(FlowProgress.id) > 0)
            .order_by(ConversationFlow.id)
        )

        flows_stats = []
        for row in result:
            attempts = row.attempts or 0
            passes = row.passes or 0
            flows_stats.append({
                "id": row.id,
                "name": row.name,
                "attempts": attempts,
                "passes": passes,
                "pass_rate": round(passes / attempts * 100, 1) if attempts > 0 else 0
            })

        return flows_stats

    async def get_top_completed_flows(self, limit: int = 10):
        """Получить топ flows по прохождению"""
        result = await self.session.execute(
            select(
                ConversationFlow.name,
                func.count(func.distinct(FlowProgress.user_id)).label('completed_count'),
                func.avg(FlowProgress.score).label('avg_score')
            )
            .outerjoin(FlowProgress, ConversationFlow.id == FlowProgress.flow_id)
            .group_by(ConversationFlow.name)
            .having(ConversationFlow.is_active == True)
            .order_by(func.count(func.distinct(FlowProgress.user_id)).desc())
            .limit(limit)
        )

        top_flows = []
        for row in result:
            top_flows.append({
                "name": row.name,
                "completed_count": row.completed_count,
                "avg_score": round(row.avg_score or 0, 1)
            })

        return top_flows

    async def get_user_progress_by_flow(self, user_id: int):
        """Прогресс конкретного пользователя по flow"""
        result = await self.session.execute(
            select(
                ConversationFlow.id,
                ConversationFlow.name,
                FlowProgress.attempts,
                FlowProgress.correct_answers,
                FlowProgress.total_questions,
                FlowProgress.passed,
                FlowProgress.score,
                FlowProgress.completed_at
            )
            .outerjoin(FlowProgress, ConversationFlow.id == FlowProgress.flow_id)
            .where(FlowProgress.user_id == user_id)
            .order_by(ConversationFlow.id)
        )

        progress_list = []
        for row in result:
            progress_list.append({
                "flow_id": row.id,
                "name": row.name,
                "attempts": row.attempts,
                "correct_answers": row.correct_answers,
                "total_questions": row.total_questions,
                "passed": row.passed,
                "score": row.score,
                "completed_at": row.completed_at
            })

        return progress_list
