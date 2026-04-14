from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler
from src.utils.callback_security import sign_callback


@register_handler
class MenuBlockHandler(BlockHandler):
    """Menu block with custom buttons"""

    block_type = "menu"
    awaits_user_input = True

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Send menu with buttons to user"""
        config = block.config

        text = config.get('text', 'Choose an option:')
        buttons = config.get('buttons', [])

        if not buttons:
            # #24: Логирование пустых buttons
            logging.getLogger(__name__).warning(f"Menu block (id={block.id}) имеет пустой список buttons")
            await message.answer("⚠️ Menu has no buttons configured")
            return

        # Build keyboard
        keyboard = self._build_menu_keyboard(buttons, block.id, config.get('is_global', False))
        await message.answer(text, reply_markup=keyboard)

    def _build_menu_keyboard(self, buttons: list, block_id: int, is_global: bool = False) -> InlineKeyboardMarkup:
        """Build inline keyboard from config"""
        keyboard_buttons = []
        for btn in buttons:

            if is_global:
                # #5: Global menu — все callback_data подписаны через HMAC
                action = btn.get('action', 'launch_flow')
                target = btn.get('target', '')

                if action == 'launch_flow':
                    callback_data = sign_callback('global', 'launch', target)
                elif action == 'callback':
                    callback_data = sign_callback('global', 'cmd', target)
                else:
                    callback_data = sign_callback('flow', str(block_id), 'menu', btn.get('callback_data', 'action'))

                keyboard_buttons.append([
                    InlineKeyboardButton(text=btn.get('label', 'Button'), callback_data=callback_data)
                ])
            else:
                # Обычный menu block с HMAC подписью
                callback_data = sign_callback('flow', str(block_id), 'menu', btn.get('callback_data', 'action'))
                keyboard_buttons.append([
                    InlineKeyboardButton(text=btn.get('label', 'Button'), callback_data=callback_data)
                ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Validate menu block configuration"""
        if 'buttons' not in config:
            return False, "Menu block requires 'buttons' field"

        buttons = config['buttons']
        if not isinstance(buttons, list) or len(buttons) == 0:
            return False, "'buttons' must be a non-empty list"

        # Если is_global=True - проверить специальную структуру
        if config.get('is_global'):
            for i, btn in enumerate(buttons):
                if 'label' not in btn:
                    return False, f"Button {i} missing 'label'"
                if 'action' not in btn:
                    return False, f"Button {i} missing 'action'"
                if 'target' not in btn:
                    return False, f"Button {i} missing 'target'"

                action = btn['action']
                if action not in ['launch_flow', 'callback']:
                    return False, f"Button {i} has invalid action '{action}'. Must be 'launch_flow' or 'callback'"
        else:
            # Обычная валидация для старого формата
            for i, btn in enumerate(buttons):
                if 'label' not in btn:
                    return False, f"Button {i} missing 'label'"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response=None) -> str | None:
        """Return condition based on which button was pressed"""
        if user_response:
            # user_response format: "menu_{button_callback_data}"
            return f"menu_{user_response}"
        return None
