"""API маршруты аналитики и отчётов."""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.api.routes.auth import get_current_user
from app.models import (
    AttendanceRecord, AttendanceSession, Person,
    PersonType, AttendanceStatus, Group
)

router = APIRouter()


@router.get("/summary", summary="Общая статистика")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Сводная статистика для главного дашборда:
    - Количество присутствующих сейчас
    - Посещаемость за сегодня
    - Распределение по типам участников
    """
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

    # Присутствующие сегодня (уникальные персоны)
    present_query = await db.execute(
        select(func.count(func.distinct(AttendanceRecord.person_id)))
        .where(
            AttendanceRecord.detected_at.between(today_start, today_end),
            AttendanceRecord.status == AttendanceStatus.PRESENT,
        )
    )
    present_count = present_query.scalar() or 0

    # Всего зарегистрированных активных персон
    total_query = await db.execute(
        select(func.count(Person.id)).where(Person.is_active == True)
    )
    total_persons = total_query.scalar() or 1

    # Разбивка по типам
    type_query = await db.execute(
        select(Person.type, func.count(Person.id))
        .where(Person.is_active == True)
        .group_by(Person.type)
    )
    by_type = {row[0].value: row[1] for row in type_query.fetchall()}

    # Нарушения сегодня (неизвестные лица)
    alerts_query = await db.execute(
        select(func.count(AttendanceRecord.id))
        .where(
            AttendanceRecord.detected_at.between(today_start, today_end),
            AttendanceRecord.status == AttendanceStatus.UNKNOWN,
        )
    )
    alerts_count = alerts_query.scalar() or 0

    attendance_rate = round((present_count / total_persons) * 100, 1) if total_persons else 0

    return {
        "present_now": present_count,
        "total_registered": total_persons,
        "attendance_rate": attendance_rate,
        "alerts_today": alerts_count,
        "by_type": by_type,
        "date": today.isoformat(),
    }


@router.get("/weekly", summary="Посещаемость за неделю")
async def get_weekly_stats(
    weeks: int = Query(default=1, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Посещаемость по дням за последние N недель."""
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    query = await db.execute(
        select(
            func.date(AttendanceRecord.detected_at).label("day"),
            func.count(func.distinct(AttendanceRecord.person_id)).label("count"),
        )
        .where(
            AttendanceRecord.detected_at >= start_date,
            AttendanceRecord.status == AttendanceStatus.PRESENT,
        )
        .group_by(func.date(AttendanceRecord.detected_at))
        .order_by(func.date(AttendanceRecord.detected_at))
    )
    rows = query.fetchall()

    # Заполняем все дни (включая нули)
    data = {}
    current = start_date
    while current <= end_date:
        data[current.isoformat()] = 0
        current += timedelta(days=1)

    for row in rows:
        if str(row.day) in data:
            data[str(row.day)] = row.count

    return {
        "labels": list(data.keys()),
        "values": list(data.values()),
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
    }


@router.get("/heatmap", summary="Тепловая карта по парам")
async def get_heatmap(
    month: Optional[int] = Query(default=None),
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Тепловая карта посещаемости: строки = дни недели, столбцы = номер пары.
    Значения = % присутствующих.
    """
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    # Данные по сессиям за месяц
    query = await db.execute(
        select(AttendanceSession)
        .where(
            func.extract("month", AttendanceSession.date) == target_month,
            func.extract("year", AttendanceSession.date) == target_year,
            AttendanceSession.total_students > 0,
        )
    )
    sessions = query.scalars().all()

    # Группируем по (день_недели, номер_пары)
    heatmap = {}
    for session in sessions:
        day = session.date.weekday()  # 0=Пн .. 6=Вс
        # Определяем номер пары по времени (упрощённо)
        hour = session.date.hour if session.date else 9
        lesson_num = max(1, min(8, (hour - 7) // 2 + 1))

        key = (day, lesson_num)
        if key not in heatmap:
            heatmap[key] = []
        heatmap[key].append(session.attendance_rate)

    # Усредняем
    result = {}
    for (day, lesson), rates in heatmap.items():
        result[f"{day}_{lesson}"] = round(sum(rates) / len(rates), 1)

    return {
        "data": result,
        "month": target_month,
        "year": target_year,
    }


@router.get("/groups", summary="Посещаемость по группам")
async def get_groups_stats(
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Статистика посещаемости по учебным группам."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    query = await db.execute(
        select(
            Group.name,
            Group.id,
            func.count(func.distinct(AttendanceRecord.person_id)).label("present"),
            func.count(func.distinct(Person.id)).label("total"),
        )
        .join(Person, Person.group_id == Group.id)
        .outerjoin(
            AttendanceRecord,
            and_(
                AttendanceRecord.person_id == Person.id,
                func.date(AttendanceRecord.detected_at).between(date_from, date_to),
                AttendanceRecord.status == AttendanceStatus.PRESENT,
            )
        )
        .where(Group.is_active == True)
        .group_by(Group.id, Group.name)
        .order_by(Group.name)
    )
    rows = query.fetchall()

    groups = []
    for row in rows:
        rate = round((row.present / row.total * 100), 1) if row.total else 0
        groups.append({
            "id": str(row.id),
            "name": row.name,
            "present": row.present,
            "total": row.total,
            "rate": rate,
            "status": "good" if rate >= 75 else "warning" if rate >= 50 else "critical",
        })

    return {"groups": groups, "period": {"from": str(date_from), "to": str(date_to)}}


@router.get("/late-arrivals", summary="Топ опоздавших")
async def get_late_arrivals(
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=30),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Студенты с наибольшим числом опозданий за период."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = await db.execute(
        select(
            Person.id,
            Person.full_name,
            Person.photo_url,
            func.count(AttendanceRecord.id).label("late_count"),
        )
        .join(AttendanceRecord, AttendanceRecord.person_id == Person.id)
        .where(
            AttendanceRecord.status == AttendanceStatus.LATE,
            AttendanceRecord.detected_at >= since,
            Person.type == PersonType.STUDENT,
        )
        .group_by(Person.id, Person.full_name, Person.photo_url)
        .order_by(func.count(AttendanceRecord.id).desc())
        .limit(limit)
    )

    rows = query.fetchall()
    return {
        "students": [
            {
                "id": str(r.id),
                "name": r.full_name,
                "photo_url": r.photo_url,
                "late_count": r.late_count,
            }
            for r in rows
        ],
        "period_days": days,
    }
