from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
import logging

from src.database.models import ConversationFlow, User, FlowBlock, UserFlowState
from src.bot.services.user_service import get_or_create_user

router = Router()
logger = logging.getLogger(__name__)


@router.message()
async def handle_global_menu_button(message: Message, db_session):
    """Обработать нажатие на кнопку из persistent keyboard"""
    # Пропускаем команды
    if message.text.startswith("/"):
        return

    session = db_session
    # #7: Guard — если у пользователя есть активный flow, передаём обработку flow.py
    active_state_result = await session.execute(
        select(UserFlowState).where(
            UserFlowState.user_id == message.from_user.id,
            UserFlowState.is_completed == False
        ).order_by(UserFlowState.started_at.desc())
    )
    active_state = active_state_result.scalar_one_or_none()

    if active_state:
        # Пользователь в процессе flow — не перехватываем сообщение
        return

        # Получить пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = await get_or_create_user(
                session,
                message.from_user.id,
                message.from_user.username,
                message.from_user.full_name
            )

        # Проверить служебные кнопки (для обратной совместимости)
        if message.text == "📊 Прогресс":
            await handle_progress(message)
            return
        elif message.text == "❓ Помощь":
            await handle_help(message)
            return

        # Попробовать найти Global Menu Flow и кнопку в нем
        global_flow_result = await session.execute(
            select(ConversationFlow).where(
                ConversationFlow.is_global_menu == True
            ).limit(1)
        )
        global_flow = global_flow_result.scalar_one_or_none()

        if global_flow:
            # Ищем menu block с этой кнопкой
            menu_blocks_result = await session.execute(
                select(FlowBlock).where(
                    FlowBlock.flow_id == global_flow.id,
                    FlowBlock.block_type == "menu"
                ).order_by(FlowBlock.position)
            )
            menu_blocks = menu_blocks_result.scalars().all()

            # Ищем кнопку с нужным label
            for block in menu_blocks:
                buttons = block.config.get('buttons', [])
                is_global = block.config.get('is_global', False)

                if is_global:
                    for btn in buttons:
                        if btn.get('label') == message.text:
                            # Нашли кнопку - выполняем действие
                            action = btn.get('action', 'launch_flow')
                            target = btn.get('target', '')

                            if action == 'launch_flow':
                                # Запустить flow по названию
                                flow_result = await session.execute(
                                    select(ConversationFlow).where(
                                        ConversationFlow.name == target,
                                        ConversationFlow.is_active == True
                                    )
                                )
                                flow = flow_result.scalar_one_or_none()

                                if flow:
                                    logger.info(f"Launching flow '{flow.name}' (id={flow.id}) for user {user.id}")
                                    from src.bot.services.flow_executor import FlowExecutor
                                    executor = FlowExecutor(session, message.bot)
                                    await executor.start_flow(user.id, flow.id, message)
                                else:
                                    await message.answer(f"❌ Flow '{target}' не найден")
                                return

                            elif action == 'callback':
                                # Вызвать callback функцию
                                await handle_callback(target, message)
                                return

        # Если global menu нет или кнопка не найдена - пытаемся найти flow по названию (fallback)
        flow_result = await session.execute(
            select(ConversationFlow).where(
                ConversationFlow.name == message.text,
                ConversationFlow.is_active == True
            )
        )
        flow = flow_result.scalar_one_or_none()

        if flow:
            # Запустить flow
            logger.info(f"Starting flow '{flow.name}' (id={flow.id}) for user {user.id}")
            from src.bot.services.flow_executor import FlowExecutor
            executor = FlowExecutor(session, message.bot)
            await executor.start_flow(user.id, flow.id, message)
        else:
            # Если flow не найден, просто логируем
            logger.debug(f"No flow found for text: {message.text}")


async def handle_progress(message: Message):
    """Показать прогресс пользователя"""
    # TODO: Implement progress display based on UserProgress model
    await message.answer("📊 Ваш прогресс: Функция в разработке")


async def handle_help(message: Message):
    """Показать справку"""
    await message.answer(
        "❓ <b>Справка</b>\n\n"
        "Выберите кнопку из меню для начала.\n\n"
        "Доступные функции:\n"
        "• Выберите flow для прохождения\n"
        "• Прогресс - статистика обучения\n"
        "• Помощь - эта справка",
        parse_mode="HTML"
    )


async def handle_callback(command: str, message: Message):
    """Настраиваемые callback функции"""
    logger.info(f"Executing callback command: {command}")

    if command == "show_progress":
        await handle_progress(message)
    elif command == "show_help":
        await handle_help(message)
    else:
        await message.answer(f"⚠️ Команда '{command}' не найдена")
