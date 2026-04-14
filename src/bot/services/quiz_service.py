"""
Quiz service for Flow system
Updated to use FlowProgress instead of UserProgress
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from src.database.models import User, ConversationFlow, FlowProgress


async def create_flow_progress(
    session: AsyncSession,
    user: User,
    flow: ConversationFlow,
    correct_answers: int,
    total_questions: int
) -> FlowProgress:
    """Создать или обновить запись о прогрессе по flow"""
    passed = (correct_answers / total_questions) >= 0.8 if total_questions > 0 else False
    score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0

    # Проверяем есть ли уже запись
    existing = await get_user_progress_for_flow(session, user.id, flow.id)

    if existing:
        # Обновляем существующую
        existing.attempts += 1
        existing.correct_answers = correct_answers
        existing.total_questions = total_questions
        existing.passed = passed
        existing.score = score
        existing.completed_at = datetime.utcnow()
        existing.last_activity = datetime.utcnow()
        await session.commit()
        await session.refresh(existing)
        return existing

    # Создаём новую
    progress = FlowProgress(
        user_id=user.id,
        flow_id=flow.id,
        attempts=1,
        correct_answers=correct_answers,
        total_questions=total_questions,
        completed_at=datetime.utcnow(),
        passed=passed,
        score=score
    )
    session.add(progress)
    await session.commit()
    await session.refresh(progress)
    return progress


async def get_user_progress_for_flow(
    session: AsyncSession,
    user_id: int,
    flow_id: int
) -> FlowProgress | None:
    """Получить прогресс пользователя по flow"""
    result = await session.execute(
        select(FlowProgress)
        .where(FlowProgress.user_id == user_id, FlowProgress.flow_id == flow_id)
    )
    return result.scalar_one_or_none()


def calculate_score(correct: int, total: int) -> float:
    """Рассчитать процент правильных ответов"""
    if total == 0:
        return 0.0
    return (correct / total) * 100


def is_passed(correct: int, total: int, threshold: float = 0.8) -> bool:
    """Проверить пройден ли тест"""
    if total == 0:
        return False
    return (correct / total) >= threshold


async def update_progress_score(
    session: AsyncSession,
    user_id: int,
    flow_id: int,
    correct: int,
    total: int
) -> FlowProgress:
    """Обновить счёт после ответа на вопрос"""
    progress = await get_user_progress_for_flow(session, user_id, flow_id)

    if not progress:
        # Создаём через create_flow_progress
        from src.database.models import User, ConversationFlow
        user = await session.get(User, user_id)
        flow = await session.get(ConversationFlow, flow_id)
        return await create_flow_progress(session, user, flow, correct, total)

    # Обновляем счёт
    progress.correct_answers = correct
    progress.total_questions = total
    progress.score = int(calculate_score(correct, total))
    progress.passed = is_passed(correct, total)
    progress.last_activity = datetime.utcnow()

    if progress.passed and not progress.completed_at:
        progress.completed_at = datetime.utcnow()

    await session.commit()
    await session.refresh(progress)
    return progress
