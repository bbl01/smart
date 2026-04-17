"""Initial migration — create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-04-16 09:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'teacher', 'staff', 'viewer', name='userrole'), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # ── groups ─────────────────────────────────────────────────────────────
    op.create_table(
        'groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('specialty', sa.String(255), nullable=True),
        sa.Column('course', sa.Integer(), nullable=True),
        sa.Column('academic_year', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── persons ────────────────────────────────────────────────────────────
    op.create_table(
        'persons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.Enum('student', 'teacher', 'staff', name='persontype'), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),
        sa.Column('face_embedding', sa.LargeBinary(), nullable=True),
        sa.Column('face_embedding_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('student_id', sa.String(50), nullable=True, unique=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id'), nullable=True),
        sa.Column('admission_year', sa.Integer(), nullable=True),
        sa.Column('department', sa.String(255), nullable=True),
        sa.Column('position', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('extra_data', postgresql.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_persons_type', 'persons', ['type'])

    # ── subjects ───────────────────────────────────────────────────────────
    op.create_table(
        'subjects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=True, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id'), nullable=True),
        sa.Column('hours_per_semester', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── schedules ──────────────────────────────────────────────────────────
    op.create_table(
        'schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id'), nullable=False),
        sa.Column('room', sa.String(50), nullable=True),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('lesson_number', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.String(5), nullable=False),
        sa.Column('end_time', sa.String(5), nullable=False),
        sa.Column('lesson_type', sa.String(50), server_default='lecture'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── cameras ────────────────────────────────────────────────────────────
    op.create_table(
        'cameras',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('rtsp_url', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('status', sa.Enum('online', 'offline', 'error', 'maintenance', name='camerastatus'), server_default='offline'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('resolution', sa.String(20), server_default='1920x1080'),
        sa.Column('fps', sa.Integer(), server_default='25'),
        sa.Column('extra_config', postgresql.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── attendance_sessions ────────────────────────────────────────────────
    op.create_table(
        'attendance_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schedules.id'), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_students', sa.Integer(), server_default='0'),
        sa.Column('present_count', sa.Integer(), server_default='0'),
        sa.Column('attendance_rate', sa.Float(), server_default='0.0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── attendance_records ─────────────────────────────────────────────────
    op.create_table(
        'attendance_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('attendance_sessions.id'), nullable=True),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id'), nullable=False),
        sa.Column('camera_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cameras.id'), nullable=True),
        sa.Column('status', sa.Enum('present', 'absent', 'late', 'excused', 'unknown', name='attendancestatus'), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('snapshot_url', sa.String(500), nullable=True),
        sa.Column('is_manual', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_attendance_person', 'attendance_records', ['person_id'])
    op.create_index('ix_attendance_detected_at', 'attendance_records', ['detected_at'])

    # ── notifications ──────────────────────────────────────────────────────
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('data', postgresql.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('attendance_records')
    op.drop_table('attendance_sessions')
    op.drop_table('cameras')
    op.drop_table('schedules')
    op.drop_table('subjects')
    op.drop_table('persons')
    op.drop_table('groups')
    op.drop_table('users')

    # Удаляем enum типы
    for enum_name in ['userrole', 'persontype', 'camerastatus', 'attendancestatus']:
        op.execute(f'DROP TYPE IF EXISTS {enum_name}')
