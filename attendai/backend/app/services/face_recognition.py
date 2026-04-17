"""
Сервис распознавания лиц.
Использует InsightFace для извлечения эмбеддингов и FAISS для поиска.
"""
import asyncio
import io
import struct
import time
from pathlib import Path
from typing import Optional
from uuid import UUID

import faiss
import numpy as np
from loguru import logger
from PIL import Image

from app.core.config import settings


class FaceRecognitionService:
    """
    Сервис биометрического распознавания лиц.

    Архитектура:
    1. InsightFace (ArcFace) — извлечение 512-мерного вектора из фото лица
    2. FAISS IndexFlatIP — векторный индекс для быстрого cosine-поиска
    3. Redis — кэш последних результатов и идентификаторов

    Точность:
    - LFW benchmark: >99.4% (buffalo_l модель)
    - Порог по умолчанию: 0.6 cosine similarity
    """

    def __init__(self):
        self.app = None          # InsightFace FaceAnalysis
        self.index = None        # FAISS индекс
        self.id_map: dict[int, str] = {}   # faiss_idx -> person_id
        self.embedding_dim = 512
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Загрузка модели и построение FAISS индекса из БД."""
        async with self._lock:
            if self._initialized:
                return

            logger.info("Загрузка InsightFace модели...")
            await asyncio.get_event_loop().run_in_executor(
                None, self._load_model
            )

            # Инициализация пустого индекса
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            logger.info(f"FAISS индекс инициализирован (dim={self.embedding_dim})")

            self._initialized = True
            logger.info("✅ FaceRecognitionService готов")

    def _load_model(self):
        """Загрузка InsightFace (выполняется в thread executor)."""
        try:
            import insightface
            from insightface.app import FaceAnalysis

            model_dir = Path(settings.ML_MODELS_DIR)
            model_dir.mkdir(parents=True, exist_ok=True)

            self.app = FaceAnalysis(
                name=settings.INSIGHTFACE_MODEL,
                root=str(model_dir),
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
                if settings.FACE_GPU_ID >= 0
                else ["CPUExecutionProvider"],
            )
            self.app.prepare(ctx_id=settings.FACE_GPU_ID, det_size=(640, 640))
            logger.info(f"InsightFace модель '{settings.INSIGHTFACE_MODEL}' загружена")
        except ImportError:
            logger.warning(
                "InsightFace не установлен. Используется заглушка для разработки."
            )
            self.app = None

    async def extract_embedding(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Извлечение биометрического вектора из изображения.

        Args:
            image_bytes: байты изображения (JPEG/PNG)

        Returns:
            numpy array shape (512,) или None если лицо не найдено
        """
        if self.app is None:
            # Заглушка для разработки без GPU
            return np.random.randn(self.embedding_dim).astype(np.float32)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_sync, image_bytes)

    def _extract_sync(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Синхронное извлечение эмбеддинга."""
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_np = np.array(img)

            faces = self.app.get(img_np)
            if not faces:
                return None

            # Берём лицо с наибольшей площадью bbox
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            embedding = face.embedding

            # L2 нормализация для cosine similarity через IP
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Ошибка извлечения эмбеддинга: {e}")
            return None

    async def add_person(self, person_id: str, embedding: np.ndarray):
        """Добавление/обновление персоны в FAISS индексе."""
        async with self._lock:
            # Если персона уже есть, удаляем
            for idx, pid in list(self.id_map.items()):
                if pid == person_id:
                    del self.id_map[idx]
                    # Примечание: FAISS IndexFlatIP не поддерживает удаление.
                    # В prod используйте IndexIDMap с remove_ids()
                    break

            faiss_idx = self.index.ntotal
            self.index.add(embedding.reshape(1, -1))
            self.id_map[faiss_idx] = person_id
            logger.debug(f"Персона {person_id} добавлена в FAISS (idx={faiss_idx})")

    async def identify_face(
        self,
        embedding: np.ndarray,
        threshold: Optional[float] = None,
    ) -> tuple[Optional[str], float]:
        """
        Поиск персоны по биометрическому вектору.

        Returns:
            (person_id, confidence) или (None, score) если не найдено
        """
        if self.index.ntotal == 0:
            return None, 0.0

        threshold = threshold or settings.FACE_RECOGNITION_THRESHOLD

        query = embedding.reshape(1, -1).astype(np.float32)
        distances, indices = self.index.search(query, k=1)

        score = float(distances[0][0])
        idx = int(indices[0][0])

        if score >= threshold and idx in self.id_map:
            return self.id_map[idx], score

        return None, score

    async def process_camera_frame(
        self,
        frame_bytes: bytes,
        camera_id: str,
    ) -> list[dict]:
        """
        Обработка кадра с камеры: детекция + идентификация всех лиц.

        Returns:
            Список обнаруженных лиц:
            [{person_id, confidence, bbox, is_known}, ...]
        """
        if self.app is None:
            return []

        loop = asyncio.get_event_loop()
        faces_raw = await loop.run_in_executor(None, self._detect_faces, frame_bytes)

        results = []
        for face_data in faces_raw:
            embedding = face_data["embedding"]
            person_id, confidence = await self.identify_face(embedding)

            results.append({
                "person_id": person_id,
                "confidence": confidence,
                "bbox": face_data["bbox"],
                "is_known": person_id is not None,
                "camera_id": camera_id,
                "timestamp": time.time(),
            })

        return results

    def _detect_faces(self, frame_bytes: bytes) -> list[dict]:
        """Синхронная детекция лиц в кадре."""
        try:
            img = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
            img_np = np.array(img)
            faces = self.app.get(img_np)

            result = []
            for face in faces:
                emb = face.embedding
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                result.append({
                    "embedding": emb.astype(np.float32),
                    "bbox": face.bbox.tolist(),
                    "det_score": float(face.det_score),
                })
            return result
        except Exception as e:
            logger.error(f"Ошибка детекции лиц: {e}")
            return []

    @staticmethod
    def embedding_to_bytes(embedding: np.ndarray) -> bytes:
        """Сериализация вектора для хранения в PostgreSQL."""
        return struct.pack(f"{len(embedding)}f", *embedding.tolist())

    @staticmethod
    def bytes_to_embedding(data: bytes) -> np.ndarray:
        """Десериализация вектора из PostgreSQL."""
        n = len(data) // 4
        values = struct.unpack(f"{n}f", data)
        return np.array(values, dtype=np.float32)

    async def rebuild_index_from_db(self, db_session):
        """
        Перестройка FAISS индекса из базы данных.
        Вызывается при старте приложения.
        """
        from sqlalchemy import select
        from app.models import Person

        async with self._lock:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.id_map = {}

            result = await db_session.execute(
                select(Person).where(
                    Person.face_embedding.isnot(None),
                    Person.is_active == True,
                )
            )
            persons = result.scalars().all()

            embeddings = []
            for i, person in enumerate(persons):
                emb = self.bytes_to_embedding(person.face_embedding)
                embeddings.append(emb)
                self.id_map[i] = str(person.id)

            if embeddings:
                emb_matrix = np.vstack(embeddings).astype(np.float32)
                self.index.add(emb_matrix)

            logger.info(
                f"FAISS индекс пересобран: {len(persons)} персон загружено"
            )

    async def cleanup(self):
        """Освобождение ресурсов."""
        self.app = None
        self.index = None
        self.id_map = {}
        self._initialized = False
        logger.info("FaceRecognitionService остановлен")
