from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура (если нужна)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мои уроки 📚")],
            [KeyboardButton(text="Прогресс 📊")],
            [KeyboardButton(text="Помощь ❓")]
        ],
        resize_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Удалить клавиатуру"""
    return ReplyKeyboardRemove()
