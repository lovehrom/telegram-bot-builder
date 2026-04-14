from sqladmin import ModelView

from src.database.models import User


class AdminUserView(ModelView, model=User):
    """Админ-вью для управления пользователями"""
    
    # Русские названия
    name = "Пользователь"
    name_plural = "Пользователи (Users)"
    icon = "fa-users"
    
    column_list = [
        User.id,
        User.telegram_id,
        User.username,
        User.full_name,
        User.is_admin,
        User.is_paid,
        User.registration_date,
        User.last_activity
    ]

    column_labels = {
        "id": "ID",
        "telegram_id": "📱 Telegram ID (числовой ID из Telegram)",
        "username": "👤 Юзернейм",
        "full_name": "📝 Полное имя",
        "is_admin": "👤 Администратор",
        "is_paid": "💳 Оплатил",
        "registration_date": "📅 Регистрация",
        "last_activity": "🕐 Последняя активность"
    }

    form_columns = [
        User.telegram_id,
        User.username,
        User.full_name,
        User.is_admin,
        User.is_paid
    ]

    column_sortable_list = [
        User.id,
        User.registration_date,
        User.last_activity
    ]

    column_default_sort = (User.registration_date, True)  # desc

    column_formatters = {
        "is_admin": lambda m, a: "👤 Да" if m.is_admin else "👤 Нет",
        "is_paid": lambda m, a: "💳 Оплачено" if m.is_paid else "🆓 Бесплатно"
    }

    form_extra_js = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Подсказка для Telegram ID
            const telegramIdContainer = document.querySelector('[name="telegram_id"]')?.closest('.form-group');
            if (telegramIdContainer) {
                const help = document.createElement('div');
                help.className = 'text-xs text-gray-500 mt-2';
                help.innerHTML = '💡 <strong>Как найти Telegram ID:</strong><br>1. Напишите боту @userinfobot<br>2. Или используйте <code>get_chat</code> в Bot API';
                telegramIdContainer.appendChild(help);
            }

            // Подсказка для is_admin
            const isAdminContainer = document.querySelector('[name="is_admin"]')?.closest('.form-group');
            if (isAdminContainer) {
                const help = document.createElement('div');
                help.className = 'text-xs text-gray-500 mt-2';
                help.textContent = '⚠️ Администратор имеет доступ к админ-панели и управлению всеми настройками';
                isAdminContainer.appendChild(help);
            }
        });
        </script>
    """
