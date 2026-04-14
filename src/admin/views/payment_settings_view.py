from sqladmin import ModelView
from src.database.models import PaymentSettings


class PaymentSettingsAdmin(ModelView, model=PaymentSettings):
    """Admin view for PaymentSettings"""
    
    # Русские названия
    name = "Настройка оплаты"
    name_plural = "Настройки оплаты (Payment Settings)"
    icon = "fa-credit-card"

    column_list = [
        PaymentSettings.id,
        PaymentSettings.payment_provider_token,
        PaymentSettings.is_test_mode,
        PaymentSettings.currency,
        PaymentSettings.price_amount
    ]

    column_labels = {
        "id": "ID",
        "payment_provider_token": "Токен провайдера",
        "is_test_mode": "Тестовый режим",
        "payment_title": "Название",
        "payment_description": "Описание",
        "currency": "Валюта",
        "price_amount": "Цена (в копейках)"
    }

    form_columns = [
        PaymentSettings.payment_provider_token,
        PaymentSettings.is_test_mode,
        PaymentSettings.payment_title,
        PaymentSettings.payment_description,
        PaymentSettings.currency,
        PaymentSettings.price_amount
    ]

    # Детальный просмотр
    column_detail_list = [
        PaymentSettings.id,
        PaymentSettings.payment_provider_token,
        PaymentSettings.is_test_mode,
        PaymentSettings.payment_title,
        PaymentSettings.payment_description,
        PaymentSettings.currency,
        PaymentSettings.price_amount
    ]

    # Только одна запись
    def get_list(self, *args, **kwargs):
        # Всегда возвращаем только первую запись
        kwargs.pop('page', None)
        return super().get_list(*args, page=1, **kwargs)
