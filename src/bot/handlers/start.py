from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from src.bot.services.user_service import get_or_create_user
from src.utils.constants import WELCOME_MESSAGE, CALLBACK_START_LEARNING
from sqlalchemy import select
from src.database.models import ConversationFlow


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, db_session):
    """Команда /start - приветствие + persistent keyboard, запуск активного flow"""
    user = await get_or_create_user(
    db_session,
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    # Показываем persistent keyboard
    from src.bot.keyboards.persistent import PersistentKeyboard
    keyboard = await PersistentKeyboard.get_main_keyboard(db_session, user.id)

    # Проверяем есть ли незавершённый flow у пользователя
    from src.database.models import UserFlowState
    active_state_result = await db_session.execute(
        select(UserFlowState).where(
            UserFlowState.user_id == user.id,
            UserFlowState.is_completed == False
        ).order_by(UserFlowState.started_at.desc())
    )
    active_state = active_state_result.scalar_one_or_none()

    if active_state:
        # Продолжаем активный flow
        from src.bot.services.flow_executor import FlowExecutor
        executor = FlowExecutor(db_session, message.bot)
        await executor.start_flow(user.id, active_state.flow_id, message)
        return

    # Проверяем есть ли глобальное меню
    global_menu_result = await db_session.execute(
        select(ConversationFlow)
        .where(ConversationFlow.is_global_menu == True)
        .limit(1)
    )
    global_menu = global_menu_result.scalar_one_or_none()

    if global_menu:
        # Запускаем глобальное меню
        from src.bot.services.flow_executor import FlowExecutor
        executor = FlowExecutor(db_session, message.bot)
        await executor.start_flow(user.id, global_menu.id, message)
        return

    # Если нет flow — отправляем приветствие с persistent keyboard
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=keyboard
    )


@router.callback_query(F.data == CALLBACK_START_LEARNING)
async def cb_start_learning(callback: CallbackQuery, db_session):
    """Начать обучение - запускает активный flow"""
    user = await get_or_create_user(db_session, callback.from_user.id)

    # Проверяем есть ли глобальное меню
    global_menu_result = await db_session.execute(
        select(ConversationFlow)
        .where(ConversationFlow.is_global_menu == True)
        .limit(1)
    )
    global_menu = global_menu_result.scalar_one_or_none()

    if global_menu:
        # Запускаем глобальное меню
        from src.bot.services.flow_executor import FlowExecutor
        executor = FlowExecutor(db_session, callback.bot)
        await executor.start_flow(user.id, global_menu.id, callback.message)
        await callback.answer()
        return

    # Если нет глобального меню, берём активный flow
    result = await db_session.execute(
        select(ConversationFlow)
        .where(ConversationFlow.is_active == True)
        .order_by(ConversationFlow.id)
        .limit(1)
    )
    flow = result.scalar_one_or_none()

    if flow:
        # Запускаем flow через executor
        from src.bot.services.flow_executor import FlowExecutor
        executor = FlowExecutor(db_session, callback.bot)
        await executor.start_flow(user.id, flow.id, callback.message)
    else:
        await callback.message.answer("Сценарии пока не добавлены.")

    await callback.answer()
