"""MinIO / S3 storage service."""
import uuid
from app.core.config import settings
from loguru import logger

class StorageService:
    async def upload_photo(self, data: bytes, person_id: str, content_type: str = "image/jpeg") -> str:
        """Upload photo and return public URL."""
        try:
            from minio import Minio
            client = Minio(settings.MINIO_ENDPOINT,
                           access_key=settings.MINIO_ACCESS_KEY,
                           secret_key=settings.MINIO_SECRET_KEY,
                           secure=settings.MINIO_SECURE)
            bucket = settings.MINIO_BUCKET_PHOTOS
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
            key = f"persons/{person_id}/{uuid.uuid4()}.jpg"
            import io
            client.put_object(bucket, key, io.BytesIO(data), len(data), content_type=content_type)
            return f"http://{settings.MINIO_ENDPOINT}/{bucket}/{key}"
        except Exception as e:
            logger.error(f"Storage upload error: {e}")
            return ""
