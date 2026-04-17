"""
AttendAI — главный модуль FastAPI приложения
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import auth, attendance, cameras, persons, analytics, websocket
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.db.base import Base
from app.services.face_recognition import FaceRecognitionService


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение работы приложения."""
    # Startup
    from loguru import logger

    logger.info("🚀 Запуск AttendAI...")

    # Создание таблиц (в prod используйте Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ База данных подключена")

    # Инициализация ML-модели
    face_service = FaceRecognitionService()
    await face_service.initialize()
    app.state.face_service = face_service
    logger.info("✅ Модель распознавания лиц загружена")

    logger.info(f"✅ Сервер запущен: http://0.0.0.0:{settings.BACKEND_PORT}")
    yield

    # Shutdown
    logger.info("🛑 Остановка AttendAI...")
    await face_service.cleanup()


app = FastAPI(
    title="AttendAI API",
    description="""
## 🎓 AttendAI — API умной системы учёта посещаемости

### Возможности:
- **Биометрическое распознавание** лиц через IP-камеры
- **Учёт посещаемости** студентов и сотрудников в реальном времени
- **Аналитика и отчёты** по группам, предметам, преподавателям
- **WebSocket** для живых обновлений дашборда
- **Уведомления** по email и Telegram

### Аутентификация:
Используйте `/api/v1/auth/login` для получения JWT токена.
Передавайте токен в заголовке: `Authorization: Bearer <token>`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── Prometheus Metrics ───────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# ─── Routers ─────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router,       prefix=f"{API_PREFIX}/auth",       tags=["🔐 Auth"])
app.include_router(persons.router,    prefix=f"{API_PREFIX}/persons",    tags=["👥 Persons"])
app.include_router(attendance.router, prefix=f"{API_PREFIX}/attendance", tags=["📋 Attendance"])
app.include_router(cameras.router,    prefix=f"{API_PREFIX}/cameras",    tags=["📹 Cameras"])
app.include_router(analytics.router,  prefix=f"{API_PREFIX}/analytics",  tags=["📊 Analytics"])
app.include_router(websocket.router,  prefix=f"{API_PREFIX}/ws",         tags=["🔌 WebSocket"])


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка состояния системы."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "AttendAI API",
    }
