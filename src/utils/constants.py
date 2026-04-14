# ===========================
# Сообщения бота
# ===========================

WELCOME_MESSAGE = """
🤖 Добро пожаловать в Bot Constructor!

Создавайте Telegram ботов без кода
через визуальный конструктор сценариев.

Нажмите "Начать" для запуска!
"""

START_LEARNING_BUTTON = "Начать 🚀"

# Сообщения доступа
PAID_CONTENT_MESSAGE = """
💳 Этот контент доступен после оплаты.

Используйте /pay_test для симуляции оплаты.
"""

LOCKED_LESSON_MESSAGE = """
🔒 Пройдите предыдущий шаг, чтобы разблокировать этот.
"""

# Сообщения тестирования
QUIZ_SUCCESS_MESSAGE = """
✅ Поздравляем! Тест пройден!

Результат: {correct}/{total} ({percentage}%)

Следующий шаг теперь разблокирован.
"""

QUIZ_FAILURE_MESSAGE = """
❌ Тест не пройден. Результат: {correct}/{total} ({percentage}%)

Пожалуйста, попробуйте снова.

Для прохода нужно 80% правильных ответов.
"""

PAYMENT_SUCCESS_MESSAGE = """
💳 Оплата прошла успешно!

Теперь у вас есть доступ ко всему контенту.

Используйте /start для продолжения.
"""

# Настройки тестов
PASS_THRESHOLD = 0.8  # 80%
PASS_PERCENTAGE = 80

# Клавиатуры
CALLBACK_START_LEARNING = "start_learning"
CALLBACK_MENU = "menu"
CALLBACK_QUIZ_PREFIX = "quiz_"
CALLBACK_LESSON_PREFIX = "lesson_"
CALLBACK_ANSWER_PREFIX = "answer_"
CALLBACK_NEXT_LESSON = "next_lesson"
