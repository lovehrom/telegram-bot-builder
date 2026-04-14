from datetime import datetime, timezone
from sqlalchemy import Boolean, String, Text, Integer, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from ..base import Base


class FlowTemplate(Base):
    """Flow templates for reusing block configurations"""

    __tablename__ = "flow_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocks_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Stores block configurations
    connections_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Stores block connections
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # System or user template
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Telegram ID of creator

    def __repr__(self) -> str:
        return f"<FlowTemplate(id={self.id}, name='{self.name}', is_system={self.is_system})>"
