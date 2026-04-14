from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Text, DateTime, Boolean

from src.database.base import Base


class MediaLibrary(Base):
    """Модель для хранения загруженных медиа файлов"""
    __tablename__ = "media_library"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'photo', 'video', 'document'
    file_name: Mapped[str | None] = mapped_column(String(255))
    uploaded_by: Mapped[int] = mapped_column(BigInteger, nullable=False)  # telegram_id админа
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
