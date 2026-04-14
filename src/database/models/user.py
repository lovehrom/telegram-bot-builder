from datetime import datetime, timezone
from sqlalchemy import Boolean, Integer, String, DateTime, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registration_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    flow_progress: Mapped[list["FlowProgress"]] = relationship(
        "FlowProgress",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Legacy field removed: current_lesson_number (migrated to FlowProgress)
    # Legacy relationship removed: progress (UserProgress) - migrated to flow_progress

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
