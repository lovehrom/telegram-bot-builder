from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
import logging

from src.database.models import User, UserFlowState
from src.bot.services.flow_executor import FlowExecutor
from src.utils.callback_security import verify_callback
from src.bot.handlers.flow_blocks.input_block import InputBlockHandler

router = Router()
logger = logging.getLogger(__name__)


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """Получить пользователя по Telegram ID"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


@router.message(F.text.startswith("/test_flow"))
async def cmd_test_flow(message: Message, db_session):
    """Тестовая команда для запуска flow"""

    user = await get_user_by_telegram_id(db_session, message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, пройдите регистрацию по команде /start")
        return

    # Получить активный flow
    executor = FlowExecutor(db_session, message.bot)
    flow = await executor.get_flow_for_user(user.id)

    if not flow:
        await message.answer("Нет активного flow")
        return

    # Запустить flow
    try:
        await executor.start_flow(user.id, flow.id, message)
    except Exception as e:
        await message.answer("Произошла ошибка при запуске сценария. Попробуйте позже.")
        raise


@router.message(F.text, ~F.text.startswith("/"))
async def handle_user_input_for_flow(message: Message, db_session):
    """Обрабатывать пользовательский ввод для input block в flow"""
    session = db_session
    user = await get_user_by_telegram_id(db_session, message.from_user.id)
    if not user:
        return

    # Проверить есть ли активный flow с ожиданием ввода
    result = await session.execute(
        select(UserFlowState).where(
            UserFlowState.user_id == user.id,
            UserFlowState.is_completed == False
        ).order_by(UserFlowState.started_at.desc())
    )
    state = result.scalar_one_or_none()

    if not state:
        return

    # Проверить флаг ожидания ввода
    context = state.context or {}
    awaiting_input = context.get('_awaiting_input')

    if not awaiting_input:
        return

    # Валидировать ввод через InputBlockHandler
    handler = InputBlockHandler()
    is_valid, error_msg = await handler.process_user_input(
        message.text, state, session
    )

    if not is_valid:
        await message.answer(error_msg)
        return

    # #1: Обрабатываем в единой транзакции с rollback при ошибке
    try:
        executor = FlowExecutor(session, message.bot)
        condition = None  # Input block всегда передаёт None для продолжения
        state.context.pop('_awaits_branches', None)
        await executor.transition_to_next(state, condition, message)

        # Выполняем следующий блок после перехода
        await executor.execute_current_block(state, message)

        # Один commit в конце всей цепочки обработки
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка обработки input в flow: {e}", exc_info=True)
        raise


@router.callback_query(F.data.startswith(("fc:", "flow:")))
async def handle_flow_callback(callback: CallbackQuery, db_session):
    """Обработать callback от flow кнопок (fc_ и flow_ префиксы)"""

    session = db_session
    # Получить пользователя
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("? Пользователь не найден")
        return

    # Получить активное состояние пользователя
    result = await session.execute(
        select(UserFlowState).where(
            UserFlowState.user_id == user.id,
            UserFlowState.is_completed == False
        ).order_by(UserFlowState.started_at.desc())
    )
    state = result.scalar_one_or_none()

    if not state:
        await callback.answer("? Нет активного flow")
        return
    # #7: Защита от двойного нажатия — callback устарел если block_id не совпадает
    callback_parts = callback.data.split(':', 3)
    if len(callback_parts) >= 2:
        try:
            callback_block_id = int(callback_parts[1])
            if state.current_block_id != callback_block_id:
                await callback.answer('⚠️ Устаревшая кнопка')
                return
        except ValueError:
            pass

    # Verify HMAC signature
    is_valid, verified_data = verify_callback(callback.data)
    if not is_valid:
        await callback.answer("Invalid callback")
        return
    # Use verified data instead of raw callback.data
    callback_data = verified_data

    # Обработать callback в контексте активного flow
    executor = FlowExecutor(session, callback.bot)
    try:
        await executor.handle_callback(
            callback_data,
            state,
            callback.message
        )
        await callback.answer()
    except Exception as e:
        await callback.answer("Произошла ошибка. Попробуйте позже.")
        raise
