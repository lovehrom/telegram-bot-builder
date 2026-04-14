"""
FlowProgress model - прогресс пользователя по flow
Заменяет UserProgress для новой системы на базе Flows
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Integer, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class FlowProgress(Base):
    """Прогресс пользователя по конкретному flow"""

    __tablename__ = "flow_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    flow_id: Mapped[int] = mapped_column(Integer, ForeignKey('conversation_flows.id', ondelete='CASCADE'), nullable=False, index=True)

    # Прогресс
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Время
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Результат
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # percentage

    # Дополнительные данные (JSON для гибкости)
    flow_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Номер попытки прохождения (для поддержки нескольких прохождений)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="flow_progress")
    flow: Mapped["ConversationFlow"] = relationship("ConversationFlow")

    # UniqueConstraint убран: пользователь может проходить flow несколько раз
    # Для различения прохождений используется поле attempt + started_at

    def __repr__(self) -> str:
        return f"<FlowProgress(id={self.id}, user_id={self.user_id}, flow_id={self.flow_id}, passed={self.passed}, score={self.score})>"

    @property
    def pass_rate(self) -> float:
        """Процент правильных ответов"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100
