from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import FlowBlock, UserFlowState, User, ConversationFlow
from .base import BlockHandler, register_handler
from src.utils.callback_security import sign_callback


@register_handler
class CourseMenuBlockHandler(BlockHandler):
    """Обработчик блока меню курсов"""

    block_type = "course_menu"

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Показать меню с доступными курсами"""
        config = block.config

        text = config.get('text', '📚 Выберите курс:')
        show_locked = config.get('show_locked', False)

        # Получить пользователя
        result = await session.execute(select(User).where(User.id == state.user_id))
        user = result.scalar_one_or_none()

        # Получить все активные flows
        flows_result = await session.execute(
            select(ConversationFlow).where(ConversationFlow.is_active == True)
        )
        flows = flows_result.scalars().all()

        if not flows:
            await message.answer("⚠️ Нет доступных курсов")
            return

        # Построить меню курсов
        buttons = []
        for flow in flows:
            # Проверить доступ (по оплате)
            is_accessible = await self._check_flow_access(flow, user, session, config)

            if is_accessible or show_locked:
                icon = '🔓' if is_accessible else '🔒'
                label = f"{icon} {flow.name}"
                # Сохраняем flow_id в callback_data
                callback_data = f"start_flow_{flow.id}"
                buttons.append({
                    'label': label,
                    'callback_data': callback_data,
                    'disabled': not is_accessible
                })

        if not buttons:
            await message.answer("⚠️ Нет доступных курсов")
            return

        # Построить клавиатуру
        keyboard = self._build_course_keyboard(buttons, block.id, flow.id)
        await message.answer(text, reply_markup=keyboard)

    async def _check_flow_access(
        self,
        flow: ConversationFlow,
        user: User | None,
        session: AsyncSession,
        config: dict
    ) -> bool:
        """Проверить имеет ли пользователь доступ к flow"""
        # Если пользователь не найден - нет доступа
        if not user:
            return False

        # Базовая проверка - если пользователь оплатил, есть доступ ко всем курсам
        if user.is_paid:
            return True

        # Проверка специфичных требований для flow
        flow_access_config = config.get('flow_access', {})

        # Если flow указан в списке бесплатных - дать доступ
        free_flows = flow_access_config.get('free_flows', [])
        if flow.name in free_flows or flow.id in free_flows:
            return True

        # Проверка по тегам (если flow имеет теги в metadata)
        flow_metadata = flow_access_config.get('metadata', {})
        if isinstance(flow_metadata, dict):
            # Если flow помечен как бесплатный
            if flow_metadata.get('is_free', False):
                return True

            # Проверка по requeriment_level
            required_level = flow_metadata.get('required_level', 0)
            user_level = getattr(user, 'level', 0)
            if user_level >= required_level:
                return True

        # По умолчанию - нет доступа для неоплативших пользователей
        return False

    def _build_course_keyboard(self, buttons: list, block_id: int, flow_id: int) -> InlineKeyboardMarkup:
        """Построить inline клавиатуру с кнопками курсов"""
        keyboard_buttons = []

        for btn in buttons:
            # Если курс заблокирован, добавляем префикс к callback_data
            # чтобы обработчик мог игнорировать нажатия
            if btn.get('disabled', False):
                # Обрезаем callback_data до 64 байт (лимит Telegram)
                raw_callback = f"flow_{block_id}_course_locked_{btn['callback_data']}"
                callback_data = sign_callback("flow", str(block_id), "course_locked", btn["callback_data"][:40])
            else:
                # Обрезаем callback_data до 64 байт (лимит Telegram)
                callback_data = sign_callback("fc", str(block_id), str(flow_id))

            keyboard_buttons.append([
                InlineKeyboardButton(text=btn['label'], callback_data=callback_data)
            ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию меню курсов"""
        if 'text' in config and not isinstance(config['text'], str):
            return False, "'text' must be a string"

        if 'show_locked' in config and not isinstance(config['show_locked'], bool):
            return False, "'show_locked' must be a boolean"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """
        Вернуть условие на основе выбранного курса
        user_response format: "start_flow_{flow_id}"
        """
        if user_response and user_response.startswith("start_flow_"):
            # Извлечь flow_id из callback_data
            flow_id = user_response.replace("start_flow_", "")
            return f"course_{flow_id}"
        return None
