# Telegram Bot Builder

Конструктор Telegram-ботов с визуальным веб-интерфейсом drag-and-drop.

## Возможности

- **14 типов блоков:** текст, изображение, видео, меню, инлайн-клавиатура, квиз, оплата, задержка, условие, случайный выбор, действие и другие
- **Visual Flow Builder** — drag-and-drop редактор на React + Vite
- **Telegram Bot API** — интеграция через aiogram
- **Flow Executor** — выполнение созданных сценариев
- **Валидация сценариев** — проверка корректности flow перед выполнением
- **Статистика** — сбор и аналитика использования ботов
- **Admin Panel** — управление пользователями и биллингом
- **Dark/Light Theme** — переключение темы в интерфейсе

## Стек

**Backend:** Python 3.11+, aiogram 3.x, SQLAlchemy, SQLite, FastAPI

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Zustand, React Flow

## Установка

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run dev
```

## Запуск

```bash
python -m src.bot.main
```

## Архитектура

```
src/
├── admin/           # Admin panel (FastAPI)
│   ├── api/         # API endpoints
│   ├── auth/        # Authentication
│   ├── frontend/    # React frontend (Vite)
│   ├── services/    # Business logic (audit, validation, statistics)
│   ├── static/      # CSS assets
│   └── templates/   # HTML templates
├── bot/
│   ├── filters/     # Bot filters
│   ├── fsm/         # Finite state machine states
│   ├── handlers/    # Telegram handlers + flow block handlers (14 types)
│   ├── keyboards/   # Inline & Reply keyboards
│   ├── middlewares/  # Database middleware
│   └── services/    # Flow executor, quiz, user services
├── database/        # SQLAlchemy models & config
│   └── models/      # User, Flow, Block, Connection, Media, Payment
└── utils/           # Validators, constants, error handling
frontend/src/
├── components/      # React components (FlowEditor, MediaSelector, UI)
├── hooks/           # Custom hooks (auto-save, DnD, gestures)
├── services/        # API client, validation
├── types/           # TypeScript types
└── utils/           # Utilities
alembic/             # Database migrations
```

## Скриншоты

*Добавить скриншоты интерфейса*

## Лицензия

MIT
