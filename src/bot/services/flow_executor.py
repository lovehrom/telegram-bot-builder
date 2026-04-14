import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
import logging

# #9: Таймаут на выполнение одного блока
BLOCK_EXECUTION_TIMEOUT = 30  # секунд
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from src.database.models import (
    User,
    ConversationFlow,
    FlowBlock,
    FlowConnection,
    UserFlowState,
    FlowProgress
)
from src.bot.handlers.flow_blocks.base import get_handler

logger = logging.getLogger(__name__)

# Максимальная глубина итеративного выполнения блоков
MAX_FLOW_DEPTH = 1000


class FlowExecutor:
    """Движок для выполнения conversation flows"""

    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self._managed = False  # #25: Флаг контекстного менеджера

    # #25: Контекстный менеджер с автоматическим commit/rollback
    async def __aenter__(self):
        self._managed = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Ошибка в FlowExecutor: {exc_val}", exc_info=(exc_type, exc_val, exc_tb))
            await self.session.rollback()
        else:
            await self.session.commit()
        self._managed = False
        return True

    async def _safe_send(self, message: Message, text: str, **kwargs) -> bool:
        """Безопасная отправка сообщения с обработкой блокировки"""
        try:
            await message.answer(text, **kwargs)
            return True
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {message.from_user.id}: {e}")
            return False

    async def _update_user_activity(self, user_id: int) -> None:
        """#2: Обновить User.last_activity при каждом взаимодействии"""
        try:
            await self.session.execute(
                update(User).where(User.id == user_id).values(
                    last_activity=datetime.utcnow()
                )
            )
        except Exception as e:
            logger.error(f"Ошибка обновления активности пользователя {user_id}: {e}", exc_info=True)

    async def start_flow(
        self,
        user_id: int,
        flow_id: int,
        telegram_message: Message
    ) -> UserFlowState:
        """Запустить flow для пользователя"""
        # Удаляем завершённые записи
        await self.session.execute(
            delete(UserFlowState).where(
                UserFlowState.user_id == user_id,
                UserFlowState.flow_id == flow_id,
                UserFlowState.is_completed == True
            )
        )

        # Завершаем все другие активные states (только один flow одновременно)
        await self.session.execute(
            update(UserFlowState).where(
                UserFlowState.user_id == user_id,
                UserFlowState.flow_id != flow_id,
                UserFlowState.is_completed == False
            ).values(
                is_completed=True,
                completed_at=datetime.utcnow(),
                current_block_id=None
            )
        )

        # Очистка зависших состояний (не обновлялись более 1 часа)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        await self.session.execute(
            delete(UserFlowState).where(
                UserFlowState.user_id == user_id,
                UserFlowState.flow_id == flow_id,
                UserFlowState.is_completed == False,
                UserFlowState.last_activity < cutoff
            )
        )
        await self.session.flush()

        existing_state = await self.session.execute(
            select(UserFlowState).where(
                UserFlowState.user_id == user_id,
                UserFlowState.flow_id == flow_id,
                UserFlowState.is_completed == False
            )
        )
        state = existing_state.scalar_one_or_none()

        if state:
            await self.resume_flow(state, telegram_message)
        else:
            flow = await self.session.get(ConversationFlow, flow_id)
            if not flow:
                raise ValueError(f"Flow {flow_id} not found")
            if not flow.is_active:
                raise ValueError(f"Flow {flow_id} is not active")
            if not flow.start_block_id:
                raise ValueError(f"Flow {flow_id} has no start block")

            state = UserFlowState(
                user_id=user_id,
                flow_id=flow_id,
                current_block_id=flow.start_block_id,
                context={},
                is_completed=False
            )
            self.session.add(state)
            try:
                await self.session.flush()
            except Exception:
                # #6: Race condition — IntegrityError при UniqueConstraint
                await self.session.rollback()
                existing = await self.session.execute(
                    select(UserFlowState).where(
                        UserFlowState.user_id == user_id,
                        UserFlowState.flow_id == flow_id,
                        UserFlowState.is_completed == False
                    )
                )
                state = existing.scalar_one_or_none()
                if not state:
                    raise
                self.session.add(state)

            # #10: Создать запись FlowProgress при старте
            await self._create_flow_progress(user_id, flow_id)

            # #2: Обновить активность пользователя
            await self._update_user_activity(user_id)

            await self.execute_current_block(state, telegram_message)

        return state

    async def _create_flow_progress(self, user_id: int, flow_id: int) -> None:
        """#10: Создать запись FlowProgress при старте flow"""
        try:
            progress = FlowProgress(
                user_id=user_id,
                flow_id=flow_id,
                attempts=1,
                started_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            self.session.add(progress)
            await self.session.flush()
        except Exception as e:
            logger.error(f"Ошибка создания FlowProgress для user={user_id}, flow={flow_id}: {e}", exc_info=True)

    async def resume_flow(self, state: UserFlowState, telegram_message: Message) -> None:
        """Возобновить выполнение flow"""
        # #2: Обновить активность при возобновлении
        await self._update_user_activity(state.user_id)
        await self.execute_current_block(state, telegram_message)

    async def execute_current_block(self, state: UserFlowState, message: Message) -> None:
        """Выполнить текущий блок и последующие автоматические блоки (итеративный цикл)"""
        # #2: Обновить User.last_activity при каждом выполнении блока
        await self._update_user_activity(state.user_id)

        depth = 0
        while depth < MAX_FLOW_DEPTH:
            if not state.current_block_id:
                await self.complete_flow(state, message)
                return

            block = await self.session.get(FlowBlock, state.current_block_id)
            if not block:
                raise ValueError(f"Block {state.current_block_id} not found")

            handler = get_handler(block.block_type)
            if not handler:
                raise ValueError(f"No handler for block type: {block.block_type}")

            try:
                # #9: Таймаут на выполнение блока
                await asyncio.wait_for(
                    handler.execute(block, state, message, self.session, self),
                    timeout=BLOCK_EXECUTION_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error(f"Таймаут ({BLOCK_EXECUTION_TIMEOUT}с) при выполнении блока {block.id} (type: {block.block_type}) для пользователя {state.user_id}")
                sent = await self._safe_send(message, "⚠️ Превышено время выполнения блока. Попробуйте позже.")
                if not sent:
                    await self.complete_flow(state, None, send_completion_message=False)
                return
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logger.warning(f"Пользователь {state.user_id} заблокировал бота или ошибка API: {e}")
                await self.complete_flow(state, None, send_completion_message=False)
                return
            except Exception as e:
                logger.error(f"Error executing block {block.id} (type: {block.block_type}): {e}", exc_info=True)
                sent = await self._safe_send(message, "⚠️ Произошла ошибка при выполнении сценария. Попробуйте позже.")
                if not sent:
                    await self.complete_flow(state, None, send_completion_message=False)
                return

            if state.context.get('_awaits_branches'):
                logger.info(f"Block {block.id} awaits branches - flow paused for user {state.user_id}")
                return

            # Обновить активность в UserFlowState
            try:
                state.last_activity = datetime.utcnow()
                await self.session.flush()
            except Exception as e:
                logger.error(f"Error updating activity for user {state.user_id}: {e}", exc_info=True)

            if not handler.awaits_user_input:
                condition = await handler.get_next_condition(block, state=state)
                if condition is None and block.block_type == "end":
                    await self.complete_flow(state, message, send_completion_message=False)
                    return
                await self.transition_to_next(state, condition, message)
            else:
                logger.info(f"Block {block.id} awaits user input - flow paused for user {state.user_id}")
                return

            depth += 1

        logger.error(f"Превышена максимальная глубина flow ({MAX_FLOW_DEPTH}) для пользователя {state.user_id}")
        await self.complete_flow(state, message)

    async def transition_to_next(
        self, state: UserFlowState, condition: str | None = None, message: Message = None
    ) -> None:
        """Перейти к следующему блоку на основе условия"""
        if not state.current_block_id:
            await self.complete_flow(state, message)
            return

        connections_result = await self.session.execute(
            select(FlowConnection).where(
                FlowConnection.from_block_id == state.current_block_id,
                FlowConnection.flow_id == state.flow_id
            )
        )
        connections = connections_result.scalars().all()

        if not connections:
            await self.complete_flow(state, message)
            return

        next_connection = None
        for conn in connections:
            if condition is None and conn.condition is None:
                next_connection = conn
                break
            elif conn.condition == condition:
                next_connection = conn
                break

        if not next_connection:
            logger.warning(
                f"Нет подходящего соединения для условия '{condition}' из блока {state.current_block_id}. "
                f"Доступные: {[c.condition for c in connections]}"
            )
            return

        state.current_block_id = next_connection.to_block_id
        await self.session.flush()

    async def handle_callback(
        self, callback_data: str, state: UserFlowState, message: Message
    ) -> None:
        """Обработать callback от кнопки и перейти к следующему блоку"""
        # #2: Обновить активность при callback
        await self._update_user_activity(state.user_id)

        parts = callback_data.split(":", 3)
        if len(parts) < 3:
            raise ValueError(f"Invalid callback data format: {callback_data}")

        if parts[0] == "fc":
            try:
                block_id = int(parts[1])
                flow_id = int(parts[2])
                block = await self.session.get(FlowBlock, block_id)
                if not block:
                    raise ValueError(f"Block {block_id} not found")
                handler = get_handler(block.block_type)
                if not handler:
                    raise ValueError(f"No handler for block type: {block.block_type}")
                condition = f"course_{flow_id}"
                state.context.pop('_awaits_branches', None)
                await self.session.flush()
                await self.transition_to_next(state, condition, message)
                await self.execute_current_block(state, message)
                return
            except ValueError:
                logger.error(f"Некорректный fc callback: {callback_data}")
                return

        try:
            block_id = int(parts[1])
        except ValueError:
            logger.error(f"Некорректный block_id в callback: {callback_data}")
            return

        action = parts[2] if len(parts) > 2 else None
        data = parts[3] if len(parts) > 3 else None

        block = await self.session.get(FlowBlock, block_id)
        if not block:
            raise ValueError(f"Block {block_id} not found")

        handler = get_handler(block.block_type)
        if not handler:
            raise ValueError(f"No handler for block type: {block.block_type}")

        if action == "answer":
            state.context['last_answer'] = data
            correct_index = block.config.get('correct_index')
            if correct_index is not None:
                try:
                    is_correct = (int(data) == correct_index)
                except ValueError:
                    is_correct = False
                state.context['quiz_correct'] = is_correct
                condition = 'correct' if is_correct else 'wrong'
            else:
                condition = None
        elif action == "branch":
            condition = data
        else:
            condition = await handler.get_next_condition(block, data, state)

        state.context.pop('_awaits_branches', None)
        await self.session.flush()
        await self.transition_to_next(state, condition, message)
        await self.execute_current_block(state, message)

    async def complete_flow(
        self, state: UserFlowState, message: Message = None, send_completion_message: bool = True
    ) -> None:
        """Завершить выполнение flow"""
        state.is_completed = True
        state.completed_at = datetime.utcnow()
        state.current_block_id = None
        await self.session.flush()

        # #10: Обновить FlowProgress при завершении
        await self._update_flow_progress_on_complete(state)

        if send_completion_message and message:
            sent = await self._safe_send(message, "✅ Flow завершён!")
            if not sent:
                logger.warning(f"Не удалось отправить сообщение о завершении flow пользователю {state.user_id}")

    async def _update_flow_progress_on_complete(self, state: UserFlowState) -> None:
        """#10: Обновить FlowProgress при завершении flow"""
        try:
            result = await self.session.execute(
                select(FlowProgress).where(
                    FlowProgress.user_id == state.user_id,
                    FlowProgress.flow_id == state.flow_id,
                    FlowProgress.completed_at.is_(None)
                ).order_by(FlowProgress.started_at.desc())
            )
            progress = result.scalar_one_or_none()
            if progress:
                progress.completed_at = datetime.utcnow()
                progress.last_activity = datetime.utcnow()
                # Обновляем счётчик из контекста
                ctx = state.context or {}
                progress.correct_answers = ctx.get('correct_answers', progress.correct_answers)
                progress.total_questions = ctx.get('total_questions', progress.total_questions)
                total = progress.total_questions
                if total > 0:
                    progress.score = (progress.correct_answers / total) * 100
                progress.passed = progress.score >= 70  # порог прохождения 70%
                await self.session.flush()
        except Exception as e:
            logger.error(f"Ошибка обновления FlowProgress: {e}", exc_info=True)

    async def get_flow_for_user(self, user_id: int) -> ConversationFlow | None:
        """
        #3: Получить активный flow с фильтрацией по user_id
        Проверяет, есть ли у пользователя активный UserFlowState, и возвращает
        соответствующий ConversationFlow. Если нет активного state — возвращает
        глобальный активный flow.
        """
        # Сначала проверяем есть ли активный state у пользователя
        state_result = await self.session.execute(
            select(UserFlowState).where(
                UserFlowState.user_id == user_id,
                UserFlowState.is_completed == False
            ).order_by(UserFlowState.started_at.desc())
        )
        active_state = state_result.scalar_one_or_none()

        if active_state:
            # Возвращаем flow из активного state
            flow = await self.session.get(ConversationFlow, active_state.flow_id)
            if flow and flow.is_active:
                return flow

        # Иначе возвращаем глобальный активный flow
        result = await self.session.execute(
            select(ConversationFlow)
            .where(ConversationFlow.is_active == True)
            .order_by(ConversationFlow.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
