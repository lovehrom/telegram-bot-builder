from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.utils.constants import (
    CALLBACK_START_LEARNING,
    CALLBACK_MENU,
    CALLBACK_QUIZ_PREFIX,
    CALLBACK_LESSON_PREFIX,
)


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура старта"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать обучение 🍷", callback_data=CALLBACK_START_LEARNING)]
        ]
    )


def get_lesson_keyboard(lesson_id: int, has_questions: bool = True, has_next: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура урока"""
    buttons = []

    if has_questions:
        buttons.append([InlineKeyboardButton(text="Пройти тест 📝", callback_data=f"{CALLBACK_QUIZ_PREFIX}{lesson_id}")])

    if has_next:
        buttons.append([InlineKeyboardButton(text="Следующий урок ➡️", callback_data=f"{CALLBACK_LESSON_PREFIX}{lesson_id + 1}")])

    buttons.append([InlineKeyboardButton(text="В меню 🏠", callback_data=CALLBACK_MENU)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quiz_keyboard(options: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура для ответов на вопрос"""
    buttons = []
    for i, option in enumerate(options):
        buttons.append([
            InlineKeyboardButton(text=option, callback_data=f"answer_{i}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_results_keyboard(passed: bool, lesson_id: int) -> InlineKeyboardMarkup:
    """Клавиатура результатов теста"""
    if passed:
        buttons = [
            [InlineKeyboardButton(text="Следующий урок ➡️", callback_data=f"{CALLBACK_LESSON_PREFIX}{lesson_id + 1}")],
            [InlineKeyboardButton(text="В меню 🏠", callback_data=CALLBACK_MENU)]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="Пересдать 🔄", callback_data=f"{CALLBACK_QUIZ_PREFIX}{lesson_id}")],
            [InlineKeyboardButton(text="В меню 🏠", callback_data=CALLBACK_MENU)]
        ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
