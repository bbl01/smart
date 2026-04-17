"""
Сервис обработки видеопотоков с IP-камер.
Читает RTSP-поток, извлекает кадры и отправляет на распознавание.
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID

import cv2
import numpy as np
from loguru import logger

from app.core.config import settings


class CameraStreamProcessor:
    """
    Обрабатывает RTSP-видеопотоки с IP-камер.

    Каждая камера работает в отдельной asyncio-задаче.
    Кадры обрабатываются с заданным интервалом.
    """

    def __init__(self, face_service, redis_client, db_session):
        self.face_service = face_service
        self.redis = redis_client
        self.db = db_session
        self._streams: Dict[str, asyncio.Task] = {}
        self._caps: Dict[str, cv2.VideoCapture] = {}

    async def start_camera(self, camera_id: str, rtsp_url: str):
        """Запуск обработки потока с камеры."""
        if camera_id in self._streams:
            logger.warning(f"Камера {camera_id} уже обрабатывается")
            return

        logger.info(f"Запуск потока камеры {camera_id}: {rtsp_url[:30]}...")
        task = asyncio.create_task(
            self._process_stream(camera_id, rtsp_url),
            name=f"camera_{camera_id}",
        )
        self._streams[camera_id] = task

    async def stop_camera(self, camera_id: str):
        """Остановка обработки потока."""
        if camera_id in self._streams:
            self._streams[camera_id].cancel()
            del self._streams[camera_id]

        if camera_id in self._caps:
            self._caps[camera_id].release()
            del self._caps[camera_id]

        logger.info(f"Камера {camera_id} остановлена")

    async def _process_stream(self, camera_id: str, rtsp_url: str):
        """
        Основной цикл обработки потока.
        Читает кадры, обнаруживает лица, обновляет статус камеры.
        """
        consecutive_errors = 0
        max_errors = 10

        while True:
            try:
                cap = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG),
                )

                if not cap.isOpened():
                    logger.error(f"Не удалось открыть поток камеры {camera_id}")
                    await self._update_camera_status(camera_id, "error")
                    await asyncio.sleep(30)
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        break
                    continue

                await self._update_camera_status(camera_id, "online")
                self._caps[camera_id] = cap
                consecutive_errors = 0

                logger.info(f"✅ Камера {camera_id} подключена")

                while True:
                    ret, frame = await asyncio.get_event_loop().run_in_executor(
                        None, cap.read
                    )

                    if not ret:
                        logger.warning(f"Потеря кадра с камеры {camera_id}")
                        break

                    # Конвертируем кадр в bytes для ML-сервиса
                    frame_bytes = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda f: cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes(),
                        frame,
                    )

                    # Обработка кадра (распознавание лиц)
                    detections = await self.face_service.process_camera_frame(
                        frame_bytes, camera_id
                    )

                    if detections:
                        await self._handle_detections(detections, camera_id, frame_bytes)

                    # Обновляем last_seen в Redis
                    await self.redis.setex(
                        f"camera:last_seen:{camera_id}",
                        60,
                        str(time.time()),
                    )

                    await asyncio.sleep(settings.CAMERA_PROCESS_INTERVAL)

                cap.release()
                await self._update_camera_status(camera_id, "error")
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                logger.info(f"Поток камеры {camera_id} отменён")
                if camera_id in self._caps:
                    self._caps[camera_id].release()
                return
            except Exception as e:
                logger.exception(f"Ошибка обработки камеры {camera_id}: {e}")
                await asyncio.sleep(10)

    async def _handle_detections(
        self,
        detections: list[dict],
        camera_id: str,
        frame_bytes: bytes,
    ):
        """
        Обработка результатов распознавания.
        Создаёт записи о посещаемости и публикует события в Redis.
        """
        now = datetime.now(timezone.utc)

        for detection in detections:
            person_id = detection.get("person_id")
            confidence = detection.get("confidence", 0.0)
            is_known = detection.get("is_known", False)

            # Дедупликация: не записываем одно лицо чаще, чем раз в 5 минут
            dedup_key = f"attendance:dedup:{camera_id}:{person_id or 'unknown'}"
            if await self.redis.exists(dedup_key):
                continue

            await self.redis.setex(dedup_key, 300, "1")

            # Публикуем событие в WebSocket канал
            event = {
                "type": "face_detected",
                "camera_id": camera_id,
                "person_id": person_id,
                "confidence": round(confidence, 4),
                "is_known": is_known,
                "timestamp": now.isoformat(),
            }

            import json
            await self.redis.publish("attendance:events", json.dumps(event))

            logger.info(
                f"Камера {camera_id}: {'ID:' + str(person_id)[:8] if person_id else 'НЕИЗВЕСТНЫЙ'} "
                f"(уверенность: {confidence:.1%})"
            )

    async def _update_camera_status(self, camera_id: str, status: str):
        """Обновление статуса камеры в Redis (читается дашбордом)."""
        await self.redis.hset(
            f"camera:status:{camera_id}",
            mapping={
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def get_active_streams(self) -> list[str]:
        """Список активных потоков."""
        return [
            cam_id
            for cam_id, task in self._streams.items()
            if not task.done()
        ]
