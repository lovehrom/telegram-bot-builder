from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler
from src.utils.callback_security import sign_callback


@register_handler
class ConfirmationBlockHandler(BlockHandler):
    """Обработчик блока подтверждения (Да/Нет)"""

    block_type = "confirmation"
    awaits_user_input = True

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Отправить сообщение с кнопками подтверждения"""
        config = block.config

        text = config.get('text', 'Подтвердите действие:')
        confirm_label = config.get('confirm_label', '✅ Да')
        cancel_label = config.get('cancel_label', '❌ Нет')

        # Построить клавиатуру
        keyboard = self._build_confirmation_keyboard(block.id, confirm_label, cancel_label)
        await message.answer(text, reply_markup=keyboard)

    def _build_confirmation_keyboard(
        self,
        block_id: int,
        confirm_label: str,
        cancel_label: str
    ) -> InlineKeyboardMarkup:
        """Построить inline клавиатуру с кнопками Да/Нет"""
        keyboard_buttons = [
            [
                InlineKeyboardButton(
                    text=confirm_label,
                    callback_data=sign_callback("flow", str(block_id), "conf", "confirmed")
                )
            ],
            [
                InlineKeyboardButton(
                    text=cancel_label,
                    callback_data=sign_callback("flow", str(block_id), "conf", "cancelled")
                )
            ]
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию блока подтверждения"""
        # #15: text обязателен
        if 'text' not in config:
            return False, "'text' is required for confirmation block"

        if 'text' in config and not isinstance(config['text'], str):
            return False, "'text' must be a string"

        # #15: Предупреждение если confirm_label/cancel_label отсутствуют
        if 'confirm_label' not in config:
            import logging as _logging
            _logging.getLogger(__name__).warning("confirm_label отсутствует в конфигурации confirmation блока, будет использовано значение по умолчанию")
        elif config['confirm_label'] and not isinstance(config['confirm_label'], str):
            return False, "'confirm_label' must be a string"

        if 'cancel_label' not in config:
            import logging as _logging
            _logging.getLogger(__name__).warning("cancel_label отсутствует в конфигурации confirmation блока, будет использовано значение по умолчанию")
        elif config['cancel_label'] and not isinstance(config['cancel_label'], str):
            return False, "'cancel_label' must be a string"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """Вернуть условие на основе того, какая кнопка была нажата"""
        if user_response:
            # user_response format: "conf_confirmed" или "conf_cancelled"
            return f"conf_{user_response}"
        return None
