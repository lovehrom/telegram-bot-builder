"""
Утилиты для валидации входных данных от пользователей.

Безопасность: все данные от пользователей должны быть валидированы
перед использованием для предотвращения инъекций и ошибок.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CallbackValidationError(Exception):
    """Исключение при ошибке валидации callback данных"""
    pass


def parse_callback_data(
    callback_data: str,
    expected_prefix: str,
    min_parts: int = 2,
    max_parts: Optional[int] = None
) -> list[str]:
    """
    Безопасный парсинг callback данных от Telegram кнопок

    Args:
        callback_data: Строка callback_data из Telegram
        expected_prefix: Ожидаемый префикс (например, "lesson_")
        min_parts: Минимальное количество частей после split
        max_parts: Максимальное количество частей (опционально)

    Returns:
        list[str]: Список частей callback_data

    Raises:
        CallbackValidationError: Если формат неверный
    """
    if not callback_data:
        logger.warning("Empty callback_data received")
        raise CallbackValidationError("Пустые данные callback")

    if not isinstance(callback_data, str):
        logger.warning(f"Invalid callback_data type: {type(callback_data)}")
        raise CallbackValidationError("Неверный тип данных callback")

    # Проверяем префикс
    if not callback_data.startswith(expected_prefix):
        logger.warning(
            f"Invalid callback prefix: expected '{expected_prefix}', "
            f"got '{callback_data[:len(expected_prefix)]}'"
        )
        raise CallbackValidationError(
            f"Неверный формат данных. Ожидается префикс: {expected_prefix}"
        )

    # Разбиваем на части
    parts = callback_data.split("_")

    if len(parts) < min_parts:
        logger.warning(
            f"Invalid callback format: expected at least {min_parts} parts, "
            f"got {len(parts)}"
        )
        raise CallbackValidationError(
            f"Неверный формат данных: ожидалось минимум {min_parts} частей, "
            f"получено {len(parts)}"
        )

    if max_parts and len(parts) > max_parts:
        logger.warning(
            f"Invalid callback format: expected at most {max_parts} parts, "
            f"got {len(parts)}"
        )
        raise CallbackValidationError(
            f"Неверный формат данных: ожидалось максимум {max_parts} частей, "
            f"получено {len(parts)}"
        )

    return parts


def safe_parse_int(
    value: str,
    field_name: str = "value",
    min_value: Optional[int] = None,
    max_value: Optional[int] = None
) -> int:
    """
    Безопасное преобразование строки в целое число с валидацией

    Args:
        value: Строка для преобразования
        field_name: Имя поля (для логов)
        min_value: Минимальное допустимое значение (опционально)
        max_value: Максимальное допустимое значение (опционально)

    Returns:
        int: Преобразованное число

    Raises:
        CallbackValidationError: Если преобразование не удалось или
                                 значение вне диапазона
    """
    try:
        result = int(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse {field_name} '{value}' as int: {e}")
        raise CallbackValidationError(
            f"Неверное значение {field_name}: '{value}'. "
            f"Ожидается целое число."
        )

    # Проверяем диапазон
    if min_value is not None and result < min_value:
        logger.warning(
            f"{field_name} {result} is less than minimum {min_value}"
        )
        raise CallbackValidationError(
            f"Значение {field_name} ({result}) меньше минимума ({min_value})"
        )

    if max_value is not None and result > max_value:
        logger.warning(
            f"{field_name} {result} is greater than maximum {max_value}"
        )
        raise CallbackValidationError(
            f"Значение {field_name} ({result}) больше максимума ({max_value})"
        )

    return result


def parse_lesson_callback(callback_data: str) -> int:
    """
    Парсит callback для урока: "lesson_{lesson_id}"

    Args:
        callback_data: Callback данные из Telegram

    Returns:
        int: ID урока

    Raises:
        CallbackValidationError: Если формат неверный
    """
    parts = parse_callback_data(callback_data, "lesson_", min_parts=2, max_parts=2)
    lesson_id = safe_parse_int(parts[1], "lesson_id", min_value=1)

    logger.debug(f"Parsed lesson callback: lesson_id={lesson_id}")
    return lesson_id


def parse_quiz_callback(callback_data: str) -> tuple[int, int]:
    """
    Парсит callback для викторины: "quiz_{lesson_id}_{answer_index}"

    Args:
        callback_data: Callback данные из Telegram

    Returns:
        tuple[int, int]: (lesson_id, answer_index)

    Raises:
        CallbackValidationError: Если формат неверный
    """
    parts = parse_callback_data(callback_data, "quiz_", min_parts=3, max_parts=3)
    lesson_id = safe_parse_int(parts[1], "lesson_id", min_value=1)
    answer_index = safe_parse_int(parts[2], "answer_index", min_value=0)

    logger.debug(f"Parsed quiz callback: lesson_id={lesson_id}, answer={answer_index}")
    return lesson_id, answer_index


def parse_flow_callback(callback_data: str) -> int:
    """
    Парсит callback для flow: "flow_{flow_id}"

    Args:
        callback_data: Callback данные из Telegram

    Returns:
        int: ID flow

    Raises:
        CallbackValidationError: Если формат неверный
    """
    parts = parse_callback_data(callback_data, "flow_", min_parts=2, max_parts=2)
    flow_id = safe_parse_int(parts[1], "flow_id", min_value=1)

    logger.debug(f"Parsed flow callback: flow_id={flow_id}")
    return flow_id
