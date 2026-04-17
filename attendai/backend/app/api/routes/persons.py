"""API маршруты управления персонами и биометрической регистрацией."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_face_service
from app.api.routes.auth import get_current_user, require_role
from app.models import Person, PersonType, UserRole
from app.services.face_recognition import FaceRecognitionService

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────────────────

class PersonResponse(BaseModel):
    id: str
    type: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    photo_url: Optional[str]
    student_id: Optional[str]
    group_id: Optional[str]
    department: Optional[str]
    is_active: bool
    has_biometrics: bool

    class Config:
        from_attributes = True


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("", summary="Список персон")
async def list_persons(
    type: Optional[PersonType] = Query(default=None),
    group_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    has_biometrics: Optional[bool] = Query(default=None),
    is_active: Optional[bool] = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Список всех персон с фильтрацией и поиском."""
    query = select(Person)

    if type:
        query = query.where(Person.type == type)
    if group_id:
        query = query.where(Person.group_id == group_id)
    if is_active is not None:
        query = query.where(Person.is_active == is_active)
    if has_biometrics is not None:
        if has_biometrics:
            query = query.where(Person.face_embedding.isnot(None))
        else:
            query = query.where(Person.face_embedding.is_(None))
    if search:
        query = query.where(
            or_(
                Person.full_name.ilike(f"%{search}%"),
                Person.email.ilike(f"%{search}%"),
                Person.student_id.ilike(f"%{search}%"),
            )
        )

    # Счётчик
    count_result = await db.execute(query.with_only_columns(
        Person.id
    ).limit(None).offset(None))
    total = len(count_result.all())

    # Пагинация
    result = await db.execute(
        query.order_by(Person.full_name).limit(limit).offset(offset)
    )
    persons = result.scalars().all()

    return {
        "items": [
            {
                "id": str(p.id),
                "type": p.type.value,
                "full_name": p.full_name,
                "email": p.email,
                "photo_url": p.photo_url,
                "student_id": p.student_id,
                "group_id": str(p.group_id) if p.group_id else None,
                "is_active": p.is_active,
                "has_biometrics": p.face_embedding is not None,
            }
            for p in persons
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать персону с фото",
)
async def create_person(
    # Form fields для multipart/form-data
    full_name: str = Form(...),
    type: PersonType = Form(...),
    email: Optional[str] = Form(default=None),
    phone: Optional[str] = Form(default=None),
    student_id: Optional[str] = Form(default=None),
    group_id: Optional[str] = Form(default=None),
    department: Optional[str] = Form(default=None),
    position: Optional[str] = Form(default=None),
    photo: Optional[UploadFile] = File(default=None),
    db: AsyncSession = Depends(get_db),
    face_service: FaceRecognitionService = Depends(get_face_service),
    _=Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
):
    """
    Регистрация новой персоны в системе.
    Если прикреплено фото — автоматически извлекается биометрический вектор.
    """
    person = Person(
        id=uuid.uuid4(),
        full_name=full_name,
        type=type,
        email=email,
        phone=phone,
        student_id=student_id,
        group_id=uuid.UUID(group_id) if group_id else None,
        department=department,
        position=position,
    )

    # Обработка фото и биометрии
    if photo:
        image_bytes = await photo.read()

        # Сохраняем фото в MinIO
        from app.services.storage import StorageService
        storage = StorageService()
        photo_url = await storage.upload_photo(
            image_bytes, str(person.id), photo.content_type or "image/jpeg"
        )
        person.photo_url = photo_url

        # Извлекаем биометрический вектор
        embedding = await face_service.extract_embedding(image_bytes)
        if embedding is not None:
            person.face_embedding = face_service.embedding_to_bytes(embedding)
            from datetime import datetime, timezone
            person.face_embedding_updated = datetime.now(timezone.utc)

            # Добавляем в FAISS индекс
            await face_service.add_person(str(person.id), embedding)
        else:
            # Фото загружено, но лицо не обнаружено
            raise HTTPException(
                status_code=422,
                detail="Лицо не обнаружено на фотографии. "
                       "Убедитесь, что лицо чётко видно и хорошо освещено.",
            )

    db.add(person)
    await db.commit()
    await db.refresh(person)

    return {
        "id": str(person.id),
        "full_name": person.full_name,
        "type": person.type.value,
        "photo_url": person.photo_url,
        "has_biometrics": person.face_embedding is not None,
        "message": "Персона успешно зарегистрирована",
    }


@router.get("/{person_id}", summary="Данные персоны")
async def get_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Полные данные по персоне."""
    result = await db.execute(
        select(Person).where(Person.id == person_id)
    )
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Персона не найдена")

    return {
        "id": str(person.id),
        "type": person.type.value,
        "full_name": person.full_name,
        "email": person.email,
        "phone": person.phone,
        "photo_url": person.photo_url,
        "student_id": person.student_id,
        "group_id": str(person.group_id) if person.group_id else None,
        "department": person.department,
        "position": person.position,
        "is_active": person.is_active,
        "has_biometrics": person.face_embedding is not None,
        "face_embedding_updated": (
            person.face_embedding_updated.isoformat()
            if person.face_embedding_updated else None
        ),
    }


@router.post("/{person_id}/enroll-face", summary="Обновить биометрию")
async def enroll_face(
    person_id: str,
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    face_service: FaceRecognitionService = Depends(get_face_service),
    _=Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
):
    """
    Обновление биометрического профиля персоны.
    Загружает новое фото и пересчитывает вектор лица.
    """
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Персона не найдена")

    image_bytes = await photo.read()
    embedding = await face_service.extract_embedding(image_bytes)

    if embedding is None:
        raise HTTPException(
            status_code=422,
            detail="Лицо не обнаружено на фотографии",
        )

    person.face_embedding = face_service.embedding_to_bytes(embedding)
    from datetime import datetime, timezone
    person.face_embedding_updated = datetime.now(timezone.utc)

    # Обновляем фото
    from app.services.storage import StorageService
    storage = StorageService()
    photo_url = await storage.upload_photo(
        image_bytes, person_id, photo.content_type or "image/jpeg"
    )
    person.photo_url = photo_url

    await db.commit()

    # Обновляем FAISS индекс
    await face_service.add_person(person_id, embedding)

    return {"message": "Биометрия успешно обновлена", "person_id": person_id}


@router.delete("/{person_id}", summary="Удалить персону")
async def delete_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(UserRole.ADMIN)),
):
    """Деактивация персоны (мягкое удаление)."""
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Персона не найдена")

    person.is_active = False
    await db.commit()
    return {"message": f"Персона {person.full_name} деактивирована"}
