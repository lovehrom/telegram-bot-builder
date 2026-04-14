from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler
from src.utils.callback_security import sign_callback


@register_handler
class StartBlockHandler(BlockHandler):
    """Обработчик стартового блока с поддержкой кнопок"""

    block_type = "start"

    @property
    def awaits_user_input(self) -> bool:
        """
        Start block не знает о branches до execute(), поэтому всегда False.
        Вместо этого в execute() устанавливается флаг в state.context['_awaits_branches'],
        который проверяется в flow_executor после execute().
        """
        return False  # Проверка branches через флаг в execute()

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """
        Стартовый блок - может показать меню с кнопками для ветвления

        Config format:
        {
            "message": "Добро пожаловать! Выберите путь:",
            "branches": [
                {"label": "Путь A", "condition": "path_a"},
                {"label": "Путь B", "condition": "path_b"}
            ]
        }
        """
        config = block.config

        # Если есть branches - показать кнопки для ветвления
        branches = config.get('branches', [])

        if branches:
            # Создать inline клавиатуру для ветвления
            keyboard = self._build_branch_keyboard(branches, block.id)
            text = config.get('message', 'Выберите путь:')
            await message.answer(text, reply_markup=keyboard)
            # #2: Устанавливаем флаг — flow_executor не должен переходить к следующему блоку
            state.context['_awaits_branches'] = True
        # Если нет branches - просто продолжаем (ничего не делаем)

    def _build_branch_keyboard(self, branches: list, block_id: int) -> InlineKeyboardMarkup:
        """Построить inline клавиатуру для ветвления"""
        buttons = []
        for branch in branches:
            callback_data = sign_callback('flow', str(block_id), 'branch', branch['condition'])
            buttons.append([
                InlineKeyboardButton(text=branch['label'], callback_data=callback_data)
            ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию start блока"""
        # Если есть branches - валидировать их
        if 'branches' in config:
            branches = config['branches']
            if not isinstance(branches, list):
                return False, "'branches' must be a list"

            for i, branch in enumerate(branches):
                if 'label' not in branch:
                    return False, f"Branch {i} missing 'label'"
                if 'condition' not in branch:
                    return False, f"Branch {i} missing 'condition'"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """
        Определить условие на основе выбора ветки

        user_response format: "path_a", "path_b", etc.
        """
        if user_response:
            return user_response
        return None
