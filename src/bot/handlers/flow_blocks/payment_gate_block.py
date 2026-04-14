from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import FlowBlock, UserFlowState, User
from .base import BlockHandler, register_handler


@register_handler
class PaymentGateBlockHandler(BlockHandler):
    """Payment gate block - checks if user has paid"""

    block_type = "payment_gate"
    awaits_user_input = False  # Automatically checks payment status, doesn't wait for user input

    async def execute(
        self,
        block: FlowBlock,
        state: UserFlowState,
        message: Message,
        session: AsyncSession,
        executor = None
    ) -> None:
        """Check payment status and route accordingly"""
        config = block.config

        required = config.get('required', True)
        unpaid_message = config.get('unpaid_message',
            "This content requires payment. Use /pay to purchase access.")

        # Получить пользователя из БД (state.user_id — FK на User.id)
        result = await session.execute(
            select(User).where(User.id == state.user_id)
        )
        user = result.scalar_one_or_none()

        # Fallback: если не найден по внутреннему ID, пробуем по telegram_id
        if not user and state.context and 'telegram_id' in state.context:
            result = await session.execute(
                select(User).where(User.telegram_id == state.context['telegram_id'])
            )
            user = result.scalar_one_or_none()

        if not user:
            is_paid = False
        else:
            is_paid = user.is_paid

        # Store in context for other blocks to use
        state.context['is_paid'] = is_paid

        if required and not is_paid:
            await message.answer(f"💳 {unpaid_message}")
        else:
            # User has paid or payment not required - just continue
            pass

    async def validate_config(self, config: dict) -> tuple[bool, str]:
        """Validate payment gate configuration"""
        required_fields = ['unpaid_message']

        for field in required_fields:
            if field not in config:
                return False, f"Payment gate requires '{field}' field"

        return True, ""

    async def get_next_condition(self, block: FlowBlock, user_response=None, state=None) -> str:
        """Return payment status for routing"""
        if state and 'is_paid' in state.context:
            return 'paid' if state.context['is_paid'] else 'unpaid'
        # Default to unpaid if we can't determine status
        return 'unpaid'
