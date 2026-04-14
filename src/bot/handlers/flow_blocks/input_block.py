"""
Input Block Handler - получение ввода от пользователя
"""
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler
class InputBlockHandler(BlockHandler):
    """Обработчик input блока - получение ввода от пользователя"""

    block_type = "input"

    @property
    def awaits_user_input(self) -> bool:
        """Input блок ждёт ответа пользователя"""
        return True

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor=None
    ) -> None:
        """
        Запросить ввод от пользователя

        Config:
        - prompt: текст запроса
        - variable_name: имя переменной для сохранения
        - input_type: тип ввода (text, number, email, phone)
        - validation_message: сообщение при невалидном вводе
        """
        config = block.config

        prompt = config.get('prompt', 'Введите значение:')
        parse_mode = config.get('parse_mode', 'HTML')

        await message.answer(prompt, parse_mode=parse_mode)

        # Сохраняем информацию о текущем input блоке в context
        context = state.context or {}
        context['_awaiting_input'] = {
            'block_id': block.id,
            'variable_name': config.get('variable_name', 'user_input'),
            'input_type': config.get('input_type', 'text'),
            'validation_message': config.get('validation_message', 'Неверный формат ввода')
        }
        state.context = context

    async def process_user_input(
        self,
        user_message: str,
        state: UserFlowState,
        session: AsyncSession
    ) -> tuple[bool, str]:
        """
        Обработать ввод пользователя

        Returns:
            (is_valid, error_message)
        """
        context = state.context or {}
        awaiting_input = context.get('_awaiting_input', {})

        if not awaiting_input:
            return True, user_message  # Не в режиме ввода

        input_type = awaiting_input.get('input_type', 'text')
        variable_name = awaiting_input.get('variable_name', 'user_input')
        validation_message = awaiting_input.get('validation_message', 'Неверный формат ввода')

        # Валидация по типу
        is_valid = True
        processed_value = user_message

        if input_type == 'number':
            try:
                processed_value = float(user_message)
                # Если целое число, сохраняем как int
                if '.' not in user_message:
                    processed_value = int(processed_value)
            except ValueError:
                is_valid = False

        elif input_type == 'email':
            if '@' not in user_message or '.' not in user_message.split('@')[-1]:
                is_valid = False

        elif input_type == 'phone':
            # Простая проверка - только цифры и + в начале
            clean_phone = user_message.replace('+', '').replace(' ', '').replace('-', '')
            if not clean_phone.isdigit() or len(clean_phone) < 10:
                is_valid = False
            processed_value = user_message  # Сохраняем как есть с форматированием

        if is_valid:
            # Сохраняем значение в context
            context[variable_name] = processed_value
            # Убираем флаг ожидания ввода
            del context['_awaiting_input']
            state.context = context
            logger.debug(f"Input saved: {variable_name} = {processed_value}")
            return True, ""
        else:
            logger.debug(f"Input validation failed: {user_message} for type {input_type}")
            return False, validation_message

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию input блока"""
        if 'prompt' not in config:
            return False, "Input block requires 'prompt' field"

        if not isinstance(config['prompt'], str):
            return False, "'prompt' must be a string"

        if 'variable_name' not in config:
            return False, "Input block requires 'variable_name' field"

        valid_input_types = ['text', 'number', 'email', 'phone']
        input_type = config.get('input_type', 'text')
        if input_type not in valid_input_types:
            return False, f"Invalid input_type. Must be one of: {valid_input_types}"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response=None) -> str | None:
        """Input блоки имеют единственный выход (после успешного ввода)"""
        return None
