from datetime import datetime, timedelta, timezone
from sqlalchemy import Boolean, Integer, DateTime, ForeignKey, JSON, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class UserFlowState(Base):
    """Track execution state of a flow for a user"""

    __tablename__ = "user_flow_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    flow_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversation_flows.id', ondelete='CASCADE'), nullable=False)
    current_block_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('flow_blocks.id'), nullable=True)

    # Execution context (stores answers, temporary data, variables)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # State tracking
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
    flow: Mapped["ConversationFlow"] = relationship("ConversationFlow")
    current_block: Mapped["FlowBlock"] = relationship("FlowBlock")

    # Индекс для быстрого поиска активных/завершённых состояний пользователя (#10)
    __table_args__ = (
        UniqueConstraint('user_id', 'flow_id', name='uq_user_flow'),
        Index('ix_user_flow_state_user_completed', 'user_id', 'is_completed'),
        Index('ix_user_flow_state_flow_id', 'flow_id'),
    )

    @classmethod
    async def cleanup_stale_states(cls, session, user_id: int = None, hours: int = 1):
        """Очистка зависших состояний flow (не обновлялись более hours часов)"""
        from sqlalchemy import delete, func
        stmt = delete(cls).where(
            cls.last_activity < cutoff,
            cls.is_completed == False
        )
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    def __repr__(self) -> str:
        return f"<UserFlowState(id={self.id}, user_id={self.user_id}, flow_id={self.flow_id}, completed={self.is_completed})>"
