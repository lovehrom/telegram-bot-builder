from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models import ConversationFlow, FlowBlock


class PersistentKeyboard:
    """Генератор постоянного меню бота"""

    @staticmethod
    async def get_main_keyboard(session: AsyncSession, user_id: int = None) -> ReplyKeyboardMarkup:
        """
        Создать клавиатуру с кнопками

        Приоритеты:
        1. Загрузить из Global Menu Flow (если есть)
        2. Fallback на все активные flows

        Args:
            session: Сессия БД
            user_id: ID пользователя (опционально, для будущих персонализаций)

        Returns:
            ReplyKeyboardMarkup с кнопками
        """
        # 1. Попробовать найти Global Menu Flow
        global_flow_result = await session.execute(
            select(ConversationFlow).where(
                ConversationFlow.is_global_menu == True
            ).limit(1)
        )
        global_flow = global_flow_result.scalar_one_or_none()

        keyboard = []

        if global_flow:
            # 2. Загрузить menu blocks из global flow
            menu_blocks_result = await session.execute(
                select(FlowBlock).where(
                    FlowBlock.flow_id == global_flow.id,
                    FlowBlock.block_type == "menu"
                ).order_by(FlowBlock.position)
            )
            menu_blocks = menu_blocks_result.scalars().all()

            # 3. Парсить каждый menu block и добавить кнопки
            for block in menu_blocks:
                buttons = block.config.get('buttons', [])
                is_global = block.config.get('is_global', False)

                for btn in buttons:
                    if is_global:
                        # Global menu кнопки
                        keyboard.append([KeyboardButton(text=btn.get('label', 'Button'))])

            # 4. Если нет кнопок - fallback
            if not keyboard:
                return await PersistentKeyboard._get_fallback_keyboard(session)

        else:
            # 5. Fallback - показать все активные flows (старое поведение)
            return await PersistentKeyboard._get_fallback_keyboard(session)

        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            is_persistent=True,
            one_time_keyboard=False
        )

    @staticmethod
    async def _get_fallback_keyboard(session: AsyncSession) -> ReplyKeyboardMarkup:
        """Fallback клавиатура - показывает все активные flows"""
        # Получить все активные flows
        result = await session.execute(
            select(ConversationFlow)
            .where(ConversationFlow.is_active == True)
            .where(ConversationFlow.is_global_menu == False)  # Исключить global menu
            .order_by(ConversationFlow.name)
        )
        flows = result.scalars().all()

        keyboard = []

        # Добавить кнопки flows
        for flow in flows:
            button = KeyboardButton(text=flow.name)
            keyboard.append([button])

        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            is_persistent=True,
            one_time_keyboard=False
        )
