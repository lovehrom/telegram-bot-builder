"""
Create Payment Block Handler - создание платёжного инвойса
ЗАГЛУШКА: не интегрирован с реальной платёжной системой
"""
import logging
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import FlowBlock, UserFlowState
from .base import BlockHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler
class CreatePaymentBlockHandler(BlockHandler):
    """Обработчик create_payment блока - создание платёжного инвойса"""

    block_type = "create_payment"

    @property
    def awaits_user_input(self) -> bool:
        """Payment блок не ждёт ввода пользователя"""
        return False

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor=None
    ) -> None:
        """
        Создать платёжный инвойс

        ЗАГЛУШКА: Логирует попытку оплаты и переходит к следующему блоку

        Config:
        - amount: сумма платежа
        - currency: валюта (RUB, USD, EUR)
        - description: описание платежа
        - provider_token: токен платёжного провайдера (будущее)
        """
        config = block.config

        amount = config.get('amount', 0)
        currency = config.get('currency', 'RUB')
        description = config.get('description', 'Оплата доступа')

        # Логируем попытку создания платежа
        logger.info(
            f"[CREATE_PAYMENT] User {state.user_id}, Flow {state.flow_id}, "
            f"Block {block.id}: Creating invoice for {amount} {currency} - {description}"
        )

        # Сохраняем информацию о платеже в context
        state.context['payment'] = {
            'amount': amount,
            'currency': currency,
            'description': description,
            'status': 'created',
            'created_at': str(message.date) if message.date else None
        }

        # ЗАГЛУШКА: В реальной реализации здесь был бы код для:
        # 1. Интеграции с платёжной системой (ЮKassa, Stripe, CryptoBot)
        # 2. Генерации платёжной ссылки
        # 3. Отправки инвойса через Telegram Payments API
        # 4. Ожидания подтверждения оплаты через webhook

        # Отправляем уведомление пользователю
        await message.answer(
            f"💳 <b>Создание платежа</b>\n\n"
            f"Сумма: {amount} {currency}\n"
            f"Описание: {description}\n\n"
            f"<i>⚠️ Платёжная система в режиме тестирования.\n"
            f"Для реальной оплаты обратитесь к администратору.</i>",
            parse_mode='HTML'
        )

        logger.info(
            f"[CREATE_PAYMENT] Invoice created (stub mode) for user {state.user_id}"
        )

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Валидировать конфигурацию create_payment блока"""
        amount = config.get('amount')

        if amount is None:
            return False, "Create payment block requires 'amount' field"

        if not isinstance(amount, (int, float)):
            return False, "'amount' must be a number"

        if amount <= 0:
            return False, "'amount' must be greater than 0"

        currency = config.get('currency', 'RUB')
        valid_currencies = ['RUB', 'USD', 'EUR', 'KZT', 'BYN']
        if currency not in valid_currencies:
            return False, f"Invalid currency. Must be one of: {valid_currencies}"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response=None) -> str | None:
        """
        Create payment блок имеет единственный выход

        В реальной реализации мог бы возвращать:
        - 'success' — платёж создан успешно
        - 'failed' — ошибка создания платежа
        """
        return None  # Единственный выход, автоматически переходит к следующему блоку
