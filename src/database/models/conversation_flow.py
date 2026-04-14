from datetime import datetime, timezone
from sqlalchemy import Boolean, String, Text, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class ConversationFlow(Base):
    """Conversation flow for bot interactions"""

    __tablename__ = "conversation_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_global_menu: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Циклический FK: ConversationFlow.start_block_id → FlowBlock.id, FlowBlock.flow_id → ConversationFlow.id
    # post_update=True в relationship ниже решает проблему: INSERT откладывает FK-проверку до второго запроса.
    # Это корректное архитектурное решение — flow должен знать свой стартовый блок, а блок — свой flow.
    start_block_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('flow_blocks.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    blocks: Mapped[list["FlowBlock"]] = relationship(
        "FlowBlock",
        back_populates="flow",
        foreign_keys="FlowBlock.flow_id",
        cascade="all, delete-orphan",
        order_by="FlowBlock.position"
    )
    # post_update=True — SQLAlchemy сначала INSERT без FK, затем UPDATE с FK (обходит циклическую зависимость)
    start_block: Mapped["FlowBlock"] = relationship(
        "FlowBlock",
        foreign_keys=[start_block_id],
        post_update=True
    )

    def __repr__(self) -> str:
        return f"<ConversationFlow(id={self.id}, name='{self.name}', is_active={self.is_active}, is_global_menu={self.is_global_menu})>"
