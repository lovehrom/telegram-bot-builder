from aiogram.fsm.state import State, StatesGroup


class QuizState(StatesGroup):
    """Состояния для прохождения теста"""
    taking_quiz = State()
