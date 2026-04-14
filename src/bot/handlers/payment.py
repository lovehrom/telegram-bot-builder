from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, PreCheckoutQuery, SuccessfulPayment
from aiogram.types import LabeledPrice
import logging

from src.bot.services.user_service import get_user_by_telegram_id, set_paid_status
from src.utils.constants import PAYMENT_SUCCESS_MESSAGE


logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("pay_test"))
async def cmd_pay_test(message: Message, db_session):
    """Тестовая команда оплаты"""
    user = await get_user_by_telegram_id(db_session, message.from_user.id)

    if user:
        await set_paid_status(db_session, user, True)
        await message.answer(PAYMENT_SUCCESS_MESSAGE)
    else:
        await message.answer("Сначала используйте /start")


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_q: PreCheckoutQuery):
    """Обработка pre-checkout query с валидацией суммы"""
    try:
        payload = pre_checkout_q.invoice_payload
        # payload format: payment_gate_{block_id}
        if not payload or not payload.startswith("payment_gate_"):
            logger.warning(f"Invalid payment payload: {payload}")
            await pre_checkout_q.answer(ok=False, error_message="Invalid payment payload")
            return

        block_id = int(payload.split("_")[-1])

        async with async_session_maker() as session:
            from src.database.models import FlowBlock
            block = await session.get(FlowBlock, block_id)

            if not block:
                logger.warning(f"Payment block {block_id} not found")
                await pre_checkout_q.answer(ok=False, error_message="Payment block not found")
                return

            # Compare amount from invoice with configured price
            config = block.config or {}
            expected_amount = config.get("price", 0)
            # Telegram sends amount in smallest currency units (cents/kopecks)
            expected_amount_kopecks = int(expected_amount * 100)

            if expected_amount_kopecks > 0 and pre_checkout_q.total_amount != expected_amount_kopecks:
                logger.warning(
                    f"Payment amount mismatch: expected {expected_amount_kopecks}, "
                    f"got {pre_checkout_q.total_amount}"
                )
                await pre_checkout_q.answer(
                    ok=False,
                    error_message=f"Price mismatch. Expected: {expected_amount} RUB"
                )
                return

        await pre_checkout_q.answer(ok=True)
    except Exception as e:
        logger.error(f"Pre-checkout validation error: {e}", exc_info=True)
        await pre_checkout_q.answer(ok=False, error_message="Payment validation failed")


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, successful_payment: SuccessfulPayment, db_session):
    """Обработка успешной оплаты"""
    user = await get_user_by_telegram_id(db_session, message.from_user.id)

    if user:
        # Устанавливаем флаг оплаты
        await set_paid_status(db_session, user, True)

        # Логируем транзакцию
        logger.info(
            f"Payment successful: user_id={user.id}, "
            f"amount={successful_payment.total_amount // 100} {successful_payment.currency}, "
            f"payload={successful_payment.invoice_payload}"
        )

        await message.answer(
            f"✅ Оплата прошла успешно!\n"
            f"Сумма: {successful_payment.total_amount // 100} {successful_payment.currency}\n\n"
            f"{PAYMENT_SUCCESS_MESSAGE}"
        )
    else:
        await message.answer("Ошибка: пользователь не найден")


async def create_payment_invoice(
    bot: Bot,
    user_id: int,
    title: str,
    description: str,
    payload: str,
    price: int,
    provider_token: str,
    currency: str = "RUB"
) -> None:
    """Создать и отправить инвойс пользователю"""
    prices = [LabeledPrice(label=title, amount=price)]

    await bot.send_invoice(
        chat_id=user_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices,
        start_parameter="start_payment",
        need_name=True,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
    )
