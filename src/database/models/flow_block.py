from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class FlowBlock(Base):
    """Individual block within a conversation flow"""

    __tablename__ = "flow_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Циклический FK: см. документацию в ConversationFlow.start_block_id (post_update=True решает)
    flow_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversation_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    block_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'text', 'video', 'quiz', 'decision', 'menu', 'payment_gate', etc.
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Visual position in editor
    label: Mapped[str] = mapped_column(String(255), nullable=False)  # Admin-friendly name

    # Block configuration (JSON based on block_type)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Position data for visual editor (x, y coordinates)
    position_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position_y: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Common fields
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow(), onupdate=func.now(), nullable=False)

    # Relationships
    flow: Mapped["ConversationFlow"] = relationship(
        "ConversationFlow",
        back_populates="blocks",
        foreign_keys=[flow_id]
    )
    outgoing_connections: Mapped[list["FlowConnection"]] = relationship(
        "FlowConnection",
        foreign_keys="FlowConnection.from_block_id",
        back_populates="from_block",
        cascade="all, delete-orphan"
    )
    incoming_connections: Mapped[list["FlowConnection"]] = relationship(
        "FlowConnection",
        foreign_keys="FlowConnection.to_block_id",
        back_populates="to_block",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FlowBlock(id={self.id}, type='{self.block_type}', label='{self.label}')>"
