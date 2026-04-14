from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler
from src.utils.callback_security import sign_callback


@register_handler
class QuizBlockHandler(BlockHandler):
    """Обработчик викторины"""

    block_type = "quiz"

    @property
    def awaits_user_input(self) -> bool:
        """#23: Property для согласованности с InputBlock"""
        return True

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Отправить вопрос с вариантами ответов"""
        config = block.config

        question = config.get('question', '')
        options = config.get('options', [])
        explanation = config.get('explanation', '')

        if not question or not options:
            await message.answer("⚠️ Ошибка в конфигурации викторины")
            return

        # Сохранить данные викторины в контексте
        state.context[f'quiz_{block.id}_question'] = question
        state.context[f'quiz_{block.id}_options'] = options
        state.context[f'quiz_{block.id}_explanation'] = explanation

        # Построить клавиатуру с вариантами ответов
        keyboard = self._build_quiz_keyboard(options, block.id)

        await message.answer(
            f"❓ {question}",
            reply_markup=keyboard
        )

    def _build_quiz_keyboard(self, options: list, block_id: int) -> InlineKeyboardMarkup:
        """Построить inline клавиатуру для викторины"""
        buttons = []
        for i, option in enumerate(options):
            callback_data = sign_callback("flow", str(block_id), "answer", str(i))
            buttons.append([InlineKeyboardButton(text=f"{i + 1}. {option}", callback_data=callback_data)])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию викторины"""
        if 'question' not in config:
            return False, "Quiz block requires 'question' field"

        if 'options' not in config:
            return False, "Quiz block requires 'options' field"

        if 'correct_index' not in config:
            return False, "Quiz block requires 'correct_index' field"

        options = config['options']
        if not isinstance(options, list) or len(options) < 2:
            return False, "'options' must be a list with at least 2 items"

        correct_index = config['correct_index']
        if not isinstance(correct_index, int) or correct_index < 0 or correct_index >= len(options):
            return False, f"'correct_index' must be between 0 and {len(options) - 1}"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response = None) -> str | None:
        """Определить условие на основе ответа"""
        if user_response is not None:
            correct_index = block.config.get('correct_index')
            if correct_index is not None and int(user_response) == correct_index:
                return 'correct'
            else:
                return 'wrong'
        return None
