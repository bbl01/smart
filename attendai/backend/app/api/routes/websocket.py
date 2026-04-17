"""
WebSocket маршруты для передачи событий в реальном времени.
Клиенты подписываются и получают события распознавания, статусы камер и уведомления.
"""
import asyncio
import json
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


class ConnectionManager:
    """Менеджер WebSocket подключений."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WS подключение: {websocket.client}. Всего: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WS отключение. Всего: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Отправка сообщения всем подключённым клиентам."""
        if not self.active_connections:
            return

        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)

        for conn in dead_connections:
            self.active_connections.discard(conn)

    async def send_personal(self, message: dict, websocket: WebSocket):
        """Отправка сообщения конкретному клиенту."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Ошибка отправки WS сообщения: {e}")
            self.disconnect(websocket)


manager = ConnectionManager()


@router.websocket("/live")
async def websocket_live(websocket: WebSocket):
    """
    WebSocket эндпоинт для событий посещаемости в реальном времени.

    Типы событий (server → client):
    - face_detected: распознано лицо
    - camera_status: изменение статуса камеры
    - attendance_update: обновление счётчиков
    - alert: системное уведомление

    Типы сообщений (client → server):
    - ping: проверка соединения
    - subscribe: подписка на конкретные камеры
    """
    await manager.connect(websocket)

    # Отправляем приветственное сообщение
    await websocket.send_json({
        "type": "connected",
        "message": "AttendAI Live Feed подключён",
    })

    # Подключаемся к Redis Pub/Sub для получения событий
    from app.core.dependencies import get_redis
    redis = None

    try:
        # Получаем Redis клиент из app state
        redis = websocket.app.state.redis if hasattr(websocket.app.state, "redis") else None

        if redis:
            pubsub = redis.pubsub()
            await pubsub.subscribe("attendance:events", "camera:events", "system:alerts")

            async def listen_redis():
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            await manager.broadcast(data)
                        except json.JSONDecodeError:
                            pass

            redis_task = asyncio.create_task(listen_redis())

        # Основной цикл — обрабатываем сообщения от клиента
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif message.get("type") == "subscribe":
                    # Клиент хочет получать события только с определённых камер
                    cameras = message.get("cameras", [])
                    await websocket.send_json({
                        "type": "subscribed",
                        "cameras": cameras,
                    })

            except asyncio.TimeoutError:
                # Heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except Exception:
                    break
            except json.JSONDecodeError:
                continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket ошибка: {e}")
    finally:
        manager.disconnect(websocket)
        if redis:
            try:
                await pubsub.unsubscribe()
                redis_task.cancel()
            except Exception:
                pass


async def broadcast_face_detection(event: dict):
    """Утилита для рассылки события распознавания лица из других сервисов."""
    await manager.broadcast({
        "type": "face_detected",
        **event,
    })


async def broadcast_camera_status(camera_id: str, status: str):
    """Рассылка изменения статуса камеры."""
    await manager.broadcast({
        "type": "camera_status",
        "camera_id": camera_id,
        "status": status,
    })


async def broadcast_alert(title: str, message: str, level: str = "info"):
    """Рассылка системного уведомления."""
    await manager.broadcast({
        "type": "alert",
        "title": title,
        "message": message,
        "level": level,
    })
