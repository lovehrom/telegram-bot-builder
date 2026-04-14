from sqlalchemy import Boolean, String, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class PaymentSettings(Base):
    """Настройки платежной системы"""

    __tablename__ = "payment_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    # Токен платежного провайдера от BotFather
    payment_provider_token: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    # Тестовый режим
    is_test_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Название для инвойса
    payment_title: Mapped[str] = mapped_column(String(255), nullable=False, default="Доступ к курсу")
    # Описание
    payment_description: Mapped[str] = mapped_column(String(500), nullable=False, default="Полный доступ ко всем урокам")
    # Валюта (по умолчанию RUB для Telegram Payments)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    # Цена в минимальных единицах (копейки для RUB)
    price_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=9900)  # 99.00 руб по умолчанию

    __table_args__ = (
        CheckConstraint("id = 1", name="ck_payment_settings_singleton"),
    )
