import logging
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler
class DecisionBlockHandler(BlockHandler):
    """
    Decision block for branching based on conditions

    Поддерживает условия:
    - equals, not_equals: равенство/неравенство
    - greater, less: больше/меньше (для чисел)
    - greater_equal, less_equal: больше или равно/меньше или равно
    - contains, not_contains: содержит/не содержит (для строк)

    Переменные:
    - context.{key}: значение из контекста пользователя
    - quiz_passed: пройден ли квиз (boolean)
    - user.is_paid: оплатил ли пользователь (boolean)
    - lesson_score: результат квиза (число)
    """

    block_type = "decision"

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """
        Выполнить decision блок: оценить условие и перейти к соответствующему блоку

        Использует условия 'true' или 'false' для маршрутизации:
        - 'true': условие выполнено
        - 'false': условие не выполнено
        """
        config = block.config

        variable = config.get('variable')  # e.g., 'quiz_passed', 'user.is_paid', 'context.my_var'
        operator = config.get('operator')  # e.g., 'equals', 'not_equals', 'greater', 'less'
        value = config.get('value')

        # Логируем для отладки
        logger.debug(
            f"Decision block: variable={variable}, operator={operator}, value={value}"
        )

        # Get value from context
        actual_value = self._get_variable_value(variable, state, config)

        # Evaluate condition
        result = self._evaluate_condition(actual_value, operator, value)

        logger.debug(
            f"Decision result: actual_value={actual_value}, result={result}"
        )

        # Записываем результат в контекст — transition_to_next вызовет execute_current_block
        state.context['_decision_result'] = 'true' if result else 'false'

    def _get_variable_value(self, variable: str, state: UserFlowState, config: dict):
        """
        Получить значение переменной из контекста или других источников

        Supported variables:
        - context.{key}: get from state.context
        - quiz_passed: get quiz_passed flag from context
        - user.is_paid: get is_paid flag from context
        - lesson_score: get quiz score from context
        """
        if not variable:
            logger.warning("Decision block: variable is empty")
            return None

        # Context variables
        if variable.startswith('context.'):
            # Get from context
            key = variable.replace('context.', '')
            value = state.context.get(key) if state.context else None
            logger.debug(f"Retrieved context.{key} = {value}")
            return value

        # Built-in variables
        if variable == 'quiz_passed':
            # Check if quiz was passed
            value = state.context.get('quiz_passed', False) if state.context else False
            logger.debug(f"Retrieved quiz_passed = {value}")
            return value

        elif variable == 'user.is_paid':
            # Check if user is paid
            value = state.context.get('is_paid', False) if state.context else False
            logger.debug(f"Retrieved user.is_paid = {value}")
            return value

        elif variable == 'lesson_score':
            # Get quiz score
            value = state.context.get('quiz_score', 0) if state.context else 0
            logger.debug(f"Retrieved lesson_score = {value}")
            return value

        elif variable == 'quiz_correct':
            # Number of correct answers
            value = state.context.get('quiz_correct', 0) if state.context else 0
            logger.debug(f"Retrieved quiz_correct = {value}")
            return value

        else:
            # Try to get from context directly
            value = state.context.get(variable) if state.context else None
            logger.debug(f"Retrieved {variable} = {value} (fallback to context)")
            return value

    def _evaluate_condition(self, actual_value, operator: str, expected_value):
        """
        Оценить условие

        Args:
            actual_value: Фактическое значение
            operator: Оператор сравнения
            expected_value: Ожидаемое значение

        Returns:
            bool: Результат сравнения
        """
        if actual_value is None:
            logger.debug("Condition evaluation failed: actual_value is None")
            return False

        try:
            if operator == 'equals':
                result = actual_value == expected_value
            elif operator == 'not_equals':
                result = actual_value != expected_value
            elif operator == 'greater':
                result = actual_value > expected_value
            elif operator == 'less':
                result = actual_value < expected_value
            elif operator == 'greater_equal':
                result = actual_value >= expected_value
            elif operator == 'less_equal':
                result = actual_value <= expected_value
            elif operator == 'contains':
                result = expected_value in actual_value if isinstance(actual_value, str) else False
            elif operator == 'not_contains':
                result = expected_value not in actual_value if isinstance(actual_value, str) else True
            else:
                logger.warning(f"Unknown operator: {operator}")
                result = False

            logger.debug(
                f"Condition evaluated: {actual_value} {operator} {expected_value} = {result}"
            )
            return result

        except (TypeError, AttributeError) as e:
            logger.error(f"Error evaluating condition: {e}, actual_value={actual_value}, operator={operator}, expected_value={expected_value}")
            return False

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """
        Валидировать конфигурацию decision блока

        Required fields:
        - variable: имя переменной для проверки
        - operator: оператор сравнения
        - value: ожидаемое значение
        """
        required_fields = ['variable', 'operator', 'value']

        for field in required_fields:
            if field not in config:
                return False, f"Decision block requires '{field}' field"

        valid_operators = [
            'equals', 'not_equals',
            'greater', 'less',
            'greater_equal', 'less_equal',
            'contains', 'not_contains'
        ]

        if config['operator'] not in valid_operators:
            return False, f"Invalid operator '{config['operator']}'. Must be one of: {valid_operators}"

        # Validate variable name
        variable = config['variable']
        if not variable or not isinstance(variable, str):
            return False, "Variable must be a non-empty string"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response=None, state: UserFlowState = None) -> str:
        """
        Вернуть условие для маршрутизации на основе результата decision

        Decision блоки выполняются автоматически, результат хранится в контексте
        """
        if state and isinstance(state, UserFlowState):
            return state.context.get('_decision_result')
        return None
