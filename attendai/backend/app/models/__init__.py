"""SQLAlchemy модели базы данных."""
import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float,
    ForeignKey, Integer, LargeBinary, String, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STAFF = "staff"
    VIEWER = "viewer"


class PersonType(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    STAFF = "staff"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"         # Присутствует
    ABSENT = "absent"           # Отсутствует
    LATE = "late"               # Опоздал
    EXCUSED = "excused"         # Уважительная причина
    UNKNOWN = "unknown"         # Неопознанный вход


class CameraStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


# ─── User (Система / Администраторы) ──────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    notifications = relationship("Notification", back_populates="user")


# ─── Person (Студент / Преподаватель / Сотрудник) ─────────────────────────────

class Person(Base):
    __tablename__ = "persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(PersonType), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)

    # Биометрия — вектор лица (512-мерный float32)
    face_embedding = Column(LargeBinary, nullable=True)
    face_embedding_updated = Column(DateTime(timezone=True), nullable=True)

    # Студенческие данные
    student_id = Column(String(50), nullable=True, unique=True)  # Номер студ. билета
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True)
    admission_year = Column(Integer, nullable=True)

    # Данные преподавателя
    department = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    group = relationship("Group", back_populates="students")
    attendance_records = relationship("AttendanceRecord", back_populates="person")


# ─── Group (Учебная группа) ───────────────────────────────────────────────────

class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # ИС-21, КТ-22
    specialty = Column(String(255), nullable=True)
    course = Column(Integer, nullable=True)  # Курс (1-5)
    academic_year = Column(String(20), nullable=True)  # 2024-2025
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    students = relationship("Person", back_populates="group")
    schedules = relationship("Schedule", back_populates="group")


# ─── Subject (Предмет) ────────────────────────────────────────────────────────

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=True)
    hours_per_semester = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("Person", foreign_keys=[teacher_id])
    schedules = relationship("Schedule", back_populates="subject")


# ─── Schedule (Расписание) ────────────────────────────────────────────────────

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    room = Column(String(50), nullable=True)

    # День недели (1-7) и номер пары (1-8)
    day_of_week = Column(Integer, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    start_time = Column(String(5), nullable=False)  # "08:00"
    end_time = Column(String(5), nullable=False)    # "09:30"

    # Тип занятия
    lesson_type = Column(String(50), default="lecture")  # lecture, practice, lab
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="schedules")
    subject = relationship("Subject", back_populates="schedules")
    teacher = relationship("Person", foreign_keys=[teacher_id])
    attendance_sessions = relationship("AttendanceSession", back_populates="schedule")


# ─── AttendanceSession (Сессия занятия) ───────────────────────────────────────

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    total_students = Column(Integer, default=0)
    present_count = Column(Integer, default=0)
    attendance_rate = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    schedule = relationship("Schedule", back_populates="attendance_sessions")
    records = relationship("AttendanceRecord", back_populates="session")


# ─── AttendanceRecord (Запись посещаемости) ───────────────────────────────────

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("attendance_sessions.id"), nullable=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True)

    status = Column(Enum(AttendanceStatus), nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    confidence = Column(Float, nullable=True)    # Уверенность распознавания (0-1)
    snapshot_url = Column(String(500), nullable=True)  # Скриншот кадра
    is_manual = Column(Boolean, default=False)  # Ручная отметка

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("AttendanceSession", back_populates="records")
    person = relationship("Person", back_populates="attendance_records")
    camera = relationship("Camera", back_populates="records")


# ─── Camera ───────────────────────────────────────────────────────────────────

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    rtsp_url = Column(String(500), nullable=True)  # Зашифровано в prod
    ip_address = Column(String(50), nullable=True)
    status = Column(Enum(CameraStatus), default=CameraStatus.OFFLINE)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    resolution = Column(String(20), default="1920x1080")
    fps = Column(Integer, default=25)
    extra_config = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    records = relationship("AttendanceRecord", back_populates="camera")


# ─── Notification ─────────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    type = Column(String(50), nullable=False)  # alert, report, system
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
