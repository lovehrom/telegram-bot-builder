"""
Action Block Handler - выполнение действий (установка переменных, API запросы)
"""
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler
class ActionBlockHandler(BlockHandler):
    """Обработчик action блока - выполнение действий"""

    block_type = "action"

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor=None
    ) -> None:
        """
        Выполнить действие

        Actions:
        - set_variable: установить переменную в context
        - api_request: выполнить HTTP запрос (будущий функционал)
        - add_tag: добавить тег пользователю (будущий функционал)
        """
        config = block.config
        action_type = config.get('action_type', 'set_variable')

        if action_type == 'set_variable':
            await self._execute_set_variable(config, state, session)
        elif action_type == 'increment':
            await self._execute_increment(config, state, session)
        elif action_type == 'decrement':
            await self._execute_decrement(config, state, session)
        else:
            logger.warning(f"Unknown action type: {action_type}")

    async def _execute_set_variable(
        self,
        config: dict,
        state: UserFlowState,
        session: AsyncSession
    ) -> None:
        """Установить переменную в context"""
        variable_name = config.get('variable_name')
        variable_value = config.get('variable_value')

        if not variable_name:
            logger.warning("set_variable action missing variable_name")
            return

        # Обновляем context
        context = state.context or {}
        context[variable_name] = variable_value
        state.context = context

        logger.debug(f"Set variable: {variable_name} = {variable_value}")

    async def _execute_increment(
        self,
        config: dict,
        state: UserFlowState,
        session: AsyncSession
    ) -> None:
        """Увеличить числовую переменную"""
        variable_name = config.get('variable_name')
        increment_by = config.get('increment_by', 1)

        if not variable_name:
            return

        context = state.context or {}
        current_value = context.get(variable_name, 0)

        try:
            new_value = float(current_value) + float(increment_by)
            # Если оба целые, сохраняем как int
            if isinstance(current_value, int) and isinstance(increment_by, int):
                new_value = int(new_value)
            context[variable_name] = new_value
            state.context = context
            logger.debug(f"Incremented {variable_name}: {current_value} -> {new_value}")
        except (ValueError, TypeError):
            logger.warning(f"Cannot increment non-numeric value: {variable_name}")

    async def _execute_decrement(
        self,
        config: dict,
        state: UserFlowState,
        session: AsyncSession
    ) -> None:
        """Уменьшить числовую переменную"""
        variable_name = config.get('variable_name')
        decrement_by = config.get('decrement_by', 1)

        if not variable_name:
            return

        context = state.context or {}
        current_value = context.get(variable_name, 0)

        try:
            new_value = float(current_value) - float(decrement_by)
            if isinstance(current_value, int) and isinstance(decrement_by, int):
                new_value = int(new_value)
            context[variable_name] = new_value
            state.context = context
            logger.debug(f"Decremented {variable_name}: {current_value} -> {new_value}")
        except (ValueError, TypeError):
            logger.warning(f"Cannot decrement non-numeric value: {variable_name}")

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию action блока"""
        action_type = config.get('action_type')

        if not action_type:
            return False, "Action block requires 'action_type' field"

        valid_actions = ['set_variable', 'increment', 'decrement']
        if action_type not in valid_actions:
            return False, f"Invalid action_type. Must be one of: {valid_actions}"

        if action_type in ['set_variable', 'increment', 'decrement']:
            if 'variable_name' not in config:
                return False, f"{action_type} action requires 'variable_name' field"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response=None) -> str | None:
        """Action блоки имеют единственный выход"""
        return None
