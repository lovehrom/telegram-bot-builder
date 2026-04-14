from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class FlowConnection(Base):
    """Connection between flow blocks with optional conditions"""

    __tablename__ = "flow_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flow_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversation_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    from_block_id: Mapped[int] = mapped_column(Integer, ForeignKey('flow_blocks.id', ondelete='CASCADE'), nullable=False, index=True)
    to_block_id: Mapped[int] = mapped_column(Integer, ForeignKey('flow_blocks.id', ondelete='CASCADE'), nullable=False)
    condition: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 'correct', 'wrong', 'button_1', 'paid', 'unpaid', etc.
    condition_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # Additional condition logic

    # Visual layout data for editor rendering
    connection_style: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # For editor rendering (color, style, etc.)

    # Common fields
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow(), onupdate=func.now(), nullable=False)

    # Relationships
    flow: Mapped["ConversationFlow"] = relationship("ConversationFlow")
    from_block: Mapped["FlowBlock"] = relationship(
        "FlowBlock",
        foreign_keys=[from_block_id],
        back_populates="outgoing_connections"
    )
    to_block: Mapped["FlowBlock"] = relationship(
        "FlowBlock",
        foreign_keys=[to_block_id],
        back_populates="incoming_connections"
    )

    __table_args__ = (
        # Уникальность: конкретная пара from→to с одним condition (включая None)
        UniqueConstraint('from_block_id', 'to_block_id', 'condition', name='uq_block_to_condition'),
    )

    def __repr__(self) -> str:
        return f"<FlowConnection(id={self.id}, from={self.from_block_id}, to={self.to_block_id}, condition='{self.condition}')>"
