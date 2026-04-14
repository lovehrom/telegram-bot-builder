"""
Random Block Handler - случайное ветвление
"""
import random
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler
class RandomBlockHandler(BlockHandler):
    """Обработчик random блока - случайный выбор следующего пути"""

    block_type = "random"

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor=None
    ) -> None:
        """
        Выбрать случайный путь

        Config:
        - mode: 'equal' (равные шансы) или 'weighted' (взвешенные)
        - weights: веса для каждого пути (только для mode='weighted')
          пример: {"path_a": 70, "path_b": 30}
        - branches: список веток для режима equal
          пример: ["branch_a", "branch_b", "branch_c"]

        Результат сохраняется в context['_random_result']
        """
        config = block.config
        mode = config.get('mode', 'equal')

        if mode == 'equal':
            result = await self._select_equal(config, state)
        elif mode == 'weighted':
            result = await self._select_weighted(config, state)
        else:
            logger.warning(f"Unknown random mode: {mode}")
            result = None

        if result:
            # Сохраняем результат в context
            context = state.context or {}
            context['_random_result'] = result
            state.context = context
            logger.debug(f"Random selection: {result}")

    async def _select_equal(self, config: dict, state: UserFlowState) -> str | None:
        """Равновероятный выбор из списка веток"""
        branches = config.get('branches', [])

        if not branches:
            logger.warning("Random block has no branches defined")
            return None

        # Выбираем случайную ветку
        selected = random.choice(branches)
        return selected

    async def _select_weighted(self, config: dict, state: UserFlowState) -> str | None:
        """Взвешенный выбор на основе весов"""
        weights = config.get('weights', {})

        if not weights:
            logger.warning("Random block has no weights defined")
            return None

        # Получаем список веток и их весов
        branches = list(weights.keys())
        weight_values = list(weights.values())

        if not branches:
            return None

        # Нормализуем веса (на случай если сумма != 100)
        total_weight = sum(weight_values)
        if total_weight == 0:
            # Если все веса 0, используем равные шансы
            return random.choice(branches)

        # Взвешенный случайный выбор
        selected = random.choices(branches, weights=weight_values, k=1)[0]
        return selected

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию random блока"""
        mode = config.get('mode', 'equal')

        valid_modes = ['equal', 'weighted']
        if mode not in valid_modes:
            return False, f"Invalid mode. Must be one of: {valid_modes}"

        if mode == 'equal':
            branches = config.get('branches', [])
            if not branches:
                return False, "Random block with mode='equal' requires 'branches' list"
            if not isinstance(branches, list):
                return False, "'branches' must be a list"
            if len(branches) < 2:
                return False, "'branches' must have at least 2 options"

        elif mode == 'weighted':
            weights = config.get('weights', {})
            if not weights:
                return False, "Random block with mode='weighted' requires 'weights' dict"
            if not isinstance(weights, dict):
                return False, "'weights' must be a dictionary"
            if len(weights) < 2:
                return False, "'weights' must have at least 2 options"

            # Проверяем что все веса числовые
            for key, value in weights.items():
                if not isinstance(value, (int, float)):
                    return False, f"Weight for '{key}' must be a number"

        return True, ""

    async def get_next_condition(
        self,
        block: FlowBlock,
        user_response=None,
        state: UserFlowState = None
    ) -> str | None:
        """
        Вернуть выбранный случайный путь

        Результат берётся из context['_random_result']
        """
        if state and state.context:
            return state.context.get('_random_result')
        return None
