# Telegram Bot Builder

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## Overview

Telegram Bot Builder is a visual drag-and-drop editor for creating Telegram bots without writing code. Design conversation flows on a canvas, connect blocks into pipelines, and deploy them instantly — all from a modern web interface.

## What I Built

### Visual Flow Editor

A React-based canvas editor powered by React Flow that lets you build bot conversations by placing and connecting blocks. Features include:

- **Auto-save** — changes are persisted to the server automatically
- **Keyboard shortcuts** — copy, paste, delete, undo/redo
- **Touch gestures** — full mobile support with pinch-to-zoom and drag
- **localStorage backup** — offline recovery if the server is unreachable
- **Undo/Redo** — full history stack for safe editing

### 14 Block Types

| Block | Description |
|-------|-------------|
| **Start** | Entry point of the flow |
| **End** | Terminal block that ends the conversation |
| **Text** | Sends a plain text message |
| **Image** | Sends a photo with optional caption |
| **Video** | Sends a video with optional caption |
| **Menu** | Displays a reply keyboard with buttons |
| **Inline Keyboard** | Sends buttons attached to a message |
| **Quiz** | Multiple-choice question with scoring |
| **Payment** | Processes Telegram payments |
| **Delay** | Pauses execution for a specified duration |
| **Condition** | Branches the flow based on user input or variable |
| **Random Choice** | Picks a random path from connected branches |
| **Action** | Executes a custom action (API call, variable set, etc.) |
| **Confirmation** | Asks the user to confirm or cancel |
| **Decision** | Multi-way branch based on evaluated conditions |

### Flow Executor

A Python runtime engine that executes published flows at scale:

- Fetches the flow definition from the database
- Resolves the starting block and traverses connections
- Handles parallel branches, delays, and conditional logic
- Persists user state between messages

### Flow Validation

Before a flow can be published, the validator checks:

- No orphaned blocks (every block must be reachable from Start)
- No infinite loops without exit conditions
- Required fields are filled on every block
- Connection types match (e.g., only valid transitions between block types)

### Admin Panel

A FastAPI + Jinja2 web dashboard for managing the platform:

- **User management** — view, edit, and suspend accounts
- **Subscription plans** — configure pricing tiers and quotas
- **Analytics** — per-flow message counts, active users, error rates
- **Authentication** — JWT-secured login with role-based access

## Key Technical Decisions

### Dual Architecture

The project splits cleanly into two independent applications:

- **Python backend** — handles Telegram communication (aiogram 3.x), flow execution, database operations, and the admin panel (FastAPI)
- **React frontend** — serves the visual editor as a single-page application (Vite + TypeScript)

This separation allows the frontend to be deployed as static files while the backend runs as a standalone service.

### Database Schema

SQLAlchemy ORM with Alembic migrations manages **11 tables**: `User`, `Flow`, `Block`, `Connection`, `Media`, `Payment`, `Subscription`, `Plan`, `AnalyticsEvent`, `AdminSession`, `Variable`.

### Custom Finite State Machine

Instead of relying on aiogram's built-in FSM (tied to handler decorators), a custom FSM implementation manages bot state:

- State is stored in the database, not memory — survives restarts
- Supports multiple concurrent users per flow
- Clean separation between state persistence and execution logic

### Block-Based Architecture

Every block type is implemented as a self-contained module with two required methods:

- `validate()` — checks that the block's configuration is correct
- `execute()` — runs the block's logic against the current context

This makes adding new block types straightforward: implement the interface and register it.

### Admin Authentication

The admin panel uses JWT tokens issued by FastAPI. Sessions are stored in the database with expiration and refresh logic. Role-based access control distinguishes between super-admins and operators.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.11 |
| Telegram Framework | aiogram 3.x |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Admin API | FastAPI |
| UI Framework | React 18 |
| Language | TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| State Management | Zustand |
| Flow Canvas | React Flow |
| Containerization | Docker |

## Architecture

```
telegram-bot-builder/
├── bot/                    # Telegram bot application
│   ├── main.py             # aiogram entry point
│   ├── executor/           # Flow execution engine
│   │   ├── runner.py       # Main flow runner
│   │   ├── fsm.py          # Custom FSM implementation
│   │   └── context.py      # Execution context
│   ├── blocks/             # Block implementations
│   │   ├── base.py         # Base block class (validate/execute)
│   │   ├── text.py
│   │   ├── image.py
│   │   ├── video.py
│   │   ├── menu.py
│   │   ├── inline_keyboard.py
│   │   ├── quiz.py
│   │   ├── payment.py
│   │   ├── delay.py
│   │   ├── condition.py
│   │   ├── random_choice.py
│   │   ├── action.py
│   │   ├── start.py
│   │   ├── end.py
│   │   ├── confirmation.py
│   │   └── decision.py
│   └── middleware/         # aiogram middlewares
├── admin/                  # Admin panel (FastAPI)
│   ├── main.py             # FastAPI entry point
│   ├── routes/             # API routes
│   ├── templates/          # Jinja2 templates
│   ├── auth.py             # JWT authentication
│   └── dependencies.py     # Dependency injection
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── flow.py
│   ├── block.py
│   ├── connection.py
│   ├── media.py
│   ├── payment.py
│   ├── subscription.py
│   ├── plan.py
│   ├── analytics.py
│   ├── admin_session.py
│   └── variable.py
├── migrations/             # Alembic migrations
├── frontend/               # React editor
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── blocks/         # Block editor components
│   │   ├── store/          # Zustand stores
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Validation, serialization
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/lovehrom/telegram-bot-builder.git
cd telegram-bot-builder
cp .env.example .env          # Configure BOT_TOKEN and database URL
docker-compose up -d
```

The frontend will be available at `http://localhost:3000` and the admin panel at `http://localhost:8000`.

### Manual Setup

**Backend:**

```bash
cd bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python main.py
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Admin Panel:**

```bash
cd admin
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## License

This project is licensed under the [MIT License](LICENSE).
