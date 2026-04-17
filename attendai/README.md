# 🎓 AttendAI — Умная система учёта посещаемости

<div align="center">

![AttendAI Banner](docs/assets/banner.png)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Автоматизированная биометрическая система учёта посещаемости для образовательных учреждений**

[Демо](#-демо) · [Установка](#-быстрый-старт) · [Документация](#-документация) · [API](#-api-документация) · [Вклад в проект](#-contributing)

</div>

---

## 📋 О проекте

**AttendAI** — комплексная платформа для автоматического учёта посещаемости с применением технологий распознавания лиц, компьютерного зрения и аналитики данных. Система полностью заменяет ручной журнал посещаемости, обеспечивая точный учёт в режиме реального времени.

### Ключевые возможности

| Функция | Описание |
|---------|----------|
| 🎥 **Видеораспознавание** | Идентификация лиц с точностью >99% через IP-камеры |
| 📊 **Аналитика в реальном времени** | Дашборд с метриками, трендами и тепловыми картами |
| 🔔 **Умные уведомления** | Алерты преподавателям, родителям и администрации |
| 📱 **Мобильное приложение** | PWA для доступа с любого устройства |
| 📄 **Автоотчёты** | Генерация PDF/Excel отчётов по расписанию |
| 🔒 **Безопасность** | JWT-аутентификация, RBAC, шифрование биометрии |
| 🌐 **REST API** | Полный API для интеграции с LMS и ЭИОС |
| 🤖 **ML-пайплайн** | Дообучение модели на новых сотрудниках/студентах |

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         КЛИЕНТСКИЙ СЛОЙ                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  React SPA   │  │   PWA Mobile │  │  Admin Dashboard     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼──────────────┘
          │                 │                      │ HTTPS / WSS
┌─────────▼─────────────────▼──────────────────────▼─────────────┐
│                        API GATEWAY (Nginx)                       │
│              Rate Limiting · SSL Termination · Load Balance      │
└─────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      BACKEND (FastAPI)                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │  Auth API  │  │Attendance  │  │Analytics   │  │WebSocket │  │
│  │  (JWT)     │  │  API       │  │  API       │  │ Server   │  │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               ML Service (Face Recognition)               │   │
│  │   InsightFace/FaceNet · FAISS Index · Redis Cache        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                 │                      │
┌─────────▼────┐  ┌─────────▼────┐  ┌────────────▼──────────────┐
│  PostgreSQL   │  │    Redis     │  │      MinIO (S3)            │
│  (основные   │  │  (кэш +      │  │  (видео, фото, отчёты)    │
│   данные)    │  │  очереди)    │  │                            │
└──────────────┘  └──────────────┘  └───────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                    КАМЕРЫ (RTSP-потоки)                          │
│           IP-камеры · Веб-камеры · NVR-системы                  │
└────────────────────────────────────────────────────────────────┘
```

### Технологический стек

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com) — высокопроизводительный асинхронный API
- [SQLAlchemy 2.0](https://sqlalchemy.org) + [Alembic](https://alembic.sqlalchemy.org) — ORM и миграции
- [Celery](https://celeryq.dev) + [Redis](https://redis.io) — фоновые задачи и очереди
- [InsightFace](https://github.com/deepinsight/insightface) — SOTA модель распознавания лиц
- [FAISS](https://github.com/facebookresearch/faiss) — быстрый векторный поиск по биометрии
- [OpenCV](https://opencv.org) — обработка видеопотоков

**Frontend:**
- [React 18](https://react.dev) + [TypeScript](https://typescriptlang.org)
- [Zustand](https://zustand-demo.pmnd.rs) — управление состоянием
- [TanStack Query](https://tanstack.com/query) — кэширование данных
- [Recharts](https://recharts.org) — графики и визуализация
- [Tailwind CSS](https://tailwindcss.com) — стилизация

**Infrastructure:**
- [Docker Compose](https://docs.docker.com/compose) — локальная разработка
- [Nginx](https://nginx.org) — reverse proxy
- [MinIO](https://min.io) — S3-совместимое хранилище
- [Prometheus](https://prometheus.io) + [Grafana](https://grafana.com) — мониторинг

---

## 🚀 Быстрый старт

### Требования

- **Docker** 24.0+ и **Docker Compose** 2.20+
- **Git**
- Минимум 8 ГБ RAM (для ML-моделей)
- GPU опционально (значительно ускоряет распознавание)

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-org/attendai.git
cd attendai
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактируйте .env — укажите секреты и параметры
nano .env
```

Минимально необходимые переменные в `.env`:
```env
SECRET_KEY=your-super-secret-key-min-32-chars
POSTGRES_PASSWORD=your-db-password
FIRST_ADMIN_EMAIL=admin@yourschool.edu
FIRST_ADMIN_PASSWORD=Admin123!
```

### 3. Запуск системы

```bash
# Запуск всех сервисов
docker compose up -d

# Просмотр логов
docker compose logs -f backend

# Проверка статуса
docker compose ps
```

### 4. Первоначальная настройка

```bash
# Инициализация базы данных и создание admin-пользователя
docker compose exec backend python -m app.cli init-db
docker compose exec backend python -m app.cli create-admin

# Загрузка демо-данных (опционально)
docker compose exec backend python -m app.cli seed-demo
```

### 5. Доступ к сервисам

| Сервис | URL | Описание |
|--------|-----|----------|
| 🌐 Web App | http://localhost:3000 | Основной интерфейс |
| 📖 API Docs | http://localhost:8000/docs | Swagger UI |
| 📊 Grafana | http://localhost:3001 | Мониторинг |
| 🗄️ MinIO | http://localhost:9001 | Хранилище файлов |
| 🔴 Redis UI | http://localhost:8081 | Redis Commander |

---

## 📁 Структура проекта

```
attendai/
├── backend/                    # FastAPI приложение
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── auth.py         # Аутентификация
│   │   │       ├── attendance.py   # Посещаемость
│   │   │       ├── cameras.py      # Управление камерами
│   │   │       ├── persons.py      # База студентов/сотрудников
│   │   │       ├── analytics.py    # Аналитика и отчёты
│   │   │       └── websocket.py    # WebSocket события
│   │   ├── core/
│   │   │   ├── config.py           # Конфигурация (Pydantic Settings)
│   │   │   ├── security.py         # JWT, хэширование
│   │   │   └── dependencies.py     # Dependency injection
│   │   ├── db/
│   │   │   ├── base.py             # SQLAlchemy base
│   │   │   └── session.py          # Сессии БД
│   │   ├── models/                 # SQLAlchemy модели
│   │   │   ├── user.py
│   │   │   ├── person.py
│   │   │   ├── attendance.py
│   │   │   ├── camera.py
│   │   │   └── schedule.py
│   │   ├── schemas/                # Pydantic схемы
│   │   ├── services/               # Бизнес-логика
│   │   │   ├── face_recognition.py # ML-сервис
│   │   │   ├── attendance.py
│   │   │   ├── camera_stream.py
│   │   │   ├── notification.py
│   │   │   └── report.py
│   │   └── utils/
│   ├── migrations/                 # Alembic миграции
│   ├── tests/                      # Pytest тесты
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React приложение
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/          # Компоненты дашборда
│   │   │   ├── cameras/            # Видеопотоки
│   │   │   ├── analytics/          # Графики и таблицы
│   │   │   └── shared/             # UI-библиотека
│   │   ├── pages/                  # Страницы
│   │   ├── hooks/                  # Кастомные хуки
│   │   ├── store/                  # Zustand store
│   │   └── utils/
│   ├── Dockerfile
│   └── package.json
│
├── ml/                         # ML-пайплайн
│   ├── models/                     # Веса моделей
│   ├── training/                   # Скрипты обучения
│   └── utils/                      # Утилиты
│
├── docker/                     # Docker конфигурации
│   ├── nginx/
│   └── postgres/
│
├── docs/                       # Документация
│   ├── api/
│   ├── deployment/
│   └── user-guide/
│
├── .github/
│   └── workflows/              # CI/CD пайплайны
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── README.md
```

---

## 📖 Документация

- [📦 Установка и развёртывание](docs/deployment/README.md)
- [🔌 API Reference](docs/api/README.md)
- [🤖 ML-пайплайн: обучение и настройка](docs/ml/README.md)
- [📹 Подключение камер](docs/cameras/README.md)
- [👥 Руководство администратора](docs/user-guide/admin.md)
- [🔒 Безопасность и GDPR](docs/security/README.md)

---

## 🔌 API Документация

После запуска системы API документация доступна по адресам:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Примеры запросов

```bash
# Получение токена
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@school.edu", "password": "Admin123!"}'

# Получение статистики посещаемости
curl -X GET http://localhost:8000/api/v1/analytics/summary \
  -H "Authorization: Bearer {token}"

# Регистрация нового студента с фото
curl -X POST http://localhost:8000/api/v1/persons \
  -H "Authorization: Bearer {token}" \
  -F "data={\"name\": \"Иван Иванов\", \"type\": \"student\", \"group\": \"ИС-21\"}" \
  -F "photo=@photo.jpg"
```

---

## 🧪 Тестирование

```bash
# Запуск всех тестов
docker compose exec backend pytest

# С покрытием кода
docker compose exec backend pytest --cov=app --cov-report=html

# Только unit-тесты (быстро)
docker compose exec backend pytest tests/unit -v

# Только integration-тесты
docker compose exec backend pytest tests/integration -v
```

---

## 🚢 Production-развёртывание

```bash
# Production запуск
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Масштабирование воркеров
docker compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

Подробнее: [docs/deployment/production.md](docs/deployment/production.md)

---

## 🤝 Contributing

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/amazing-feature`
3. Закоммитьте: `git commit -m 'feat: add amazing feature'`
4. Запуште: `git push origin feature/amazing-feature`
5. Откройте Pull Request

Читайте [CONTRIBUTING.md](CONTRIBUTING.md) для деталей.

---

## 📄 Лицензия

Распространяется под лицензией MIT. См. [LICENSE](LICENSE) для деталей.

---

## 📞 Контакты

- 📧 Email: support@attendai.edu
- 💬 Telegram: [@attendai_support](https://t.me/attendai_support)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/attendai/issues)

---

<div align="center">
Сделано с ❤️ для образования
</div>
