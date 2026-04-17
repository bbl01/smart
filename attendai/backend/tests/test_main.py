"""
Тесты для AttendAI Backend
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.main import app
from app.core.config import settings


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """HTTP клиент для тестов с мокнутыми зависимостями."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def mock_face_service():
    """Мок FaceRecognitionService."""
    service = MagicMock()
    service.extract_embedding = AsyncMock(return_value=None)
    service.identify_face = AsyncMock(return_value=(None, 0.0))
    service.process_camera_frame = AsyncMock(return_value=[])
    return service


@pytest.fixture
def admin_token():
    """JWT токен администратора для тестов."""
    from app.api.routes.auth import create_access_token
    return create_access_token({"sub": "00000000-0000-0000-0000-000000000001", "role": "admin"})


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ─── Health Check ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    """Проверка доступности сервера."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AttendAI API"


# ─── Auth Tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Неверные учётные данные должны возвращать 401."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@email.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    """Без токена /me должен возвращать 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_access_token():
    """Проверка создания JWT токена."""
    from app.api.routes.auth import create_access_token
    from jose import jwt

    token = create_access_token({"sub": "test-user-id", "role": "admin"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == "test-user-id"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_hash_password():
    """Проверка хэширования и верификации пароля."""
    from app.api.routes.auth import hash_password, verify_password

    password = "SecurePassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


# ─── Analytics Tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analytics_summary_unauthorized(client):
    """Аналитика недоступна без авторизации."""
    response = await client.get("/api/v1/analytics/summary")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analytics_weekly_params(client, auth_headers):
    """Параметр weeks должен быть в диапазоне 1-12."""
    with patch("app.api.routes.analytics.get_db"):
        # weeks=0 должен вернуть ошибку валидации
        response = await client.get(
            "/api/v1/analytics/weekly?weeks=0",
            headers=auth_headers,
        )
        assert response.status_code == 422


# ─── Face Recognition Service Tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_face_service_embedding_to_bytes():
    """Проверка сериализации/десериализации эмбеддинга."""
    import numpy as np
    from app.services.face_recognition import FaceRecognitionService

    service = FaceRecognitionService()
    original = np.random.randn(512).astype(np.float32)

    # Сериализуем и десериализуем
    serialized = service.embedding_to_bytes(original)
    restored = service.bytes_to_embedding(serialized)

    assert restored.shape == (512,)
    np.testing.assert_array_almost_equal(original, restored, decimal=5)


@pytest.mark.asyncio
async def test_face_service_empty_index():
    """Поиск в пустом индексе должен возвращать (None, 0.0)."""
    import faiss
    from app.services.face_recognition import FaceRecognitionService

    service = FaceRecognitionService()
    service.index = faiss.IndexFlatIP(512)
    service.id_map = {}

    import numpy as np
    query = np.random.randn(512).astype(np.float32)
    person_id, confidence = await service.identify_face(query)

    assert person_id is None
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_face_service_add_and_identify():
    """Добавление персоны и её последующее нахождение."""
    import faiss
    import numpy as np
    from app.services.face_recognition import FaceRecognitionService

    service = FaceRecognitionService()
    service.index = faiss.IndexFlatIP(512)
    service.id_map = {}

    # Добавляем персону
    person_id = "test-person-123"
    embedding = np.random.randn(512).astype(np.float32)
    embedding /= np.linalg.norm(embedding)  # Нормализуем

    await service.add_person(person_id, embedding)

    # Ищем с тем же вектором (score = 1.0)
    found_id, confidence = await service.identify_face(embedding, threshold=0.5)

    assert found_id == person_id
    assert confidence >= 0.99  # Должен быть очень высокий score


# ─── Cameras Tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cameras_list_unauthorized(client):
    """Список камер недоступен без авторизации."""
    response = await client.get("/api/v1/cameras")
    assert response.status_code == 401


# ─── WebSocket Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_websocket_connection():
    """WebSocket должен принимать подключение и отвечать на ping."""
    from httpx_ws import aconnect_ws

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        try:
            async with aconnect_ws("/api/v1/ws/live", client) as ws:
                # Ожидаем приветственное сообщение
                msg = await ws.receive_json()
                assert msg["type"] == "connected"
        except ImportError:
            pytest.skip("httpx-ws не установлен")
