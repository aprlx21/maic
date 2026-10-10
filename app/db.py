from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    select,
    update,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.budget import remaining_seconds
from app.config import settings


def now():
    return datetime.now(UTC).replace(tzinfo=None)


def new_id():
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    filename: Mapped[str] = mapped_column(String(255))
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_key: Mapped[str] = mapped_column(String(500))
    request: Mapped[dict] = mapped_column(JSON)
    mode: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(40), default="queued")
    current_revision: Mapped[str | None] = mapped_column(String(36), nullable=True)
    pending_command: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    runnable: Mapped[bool] = mapped_column(Boolean, default=True)
    lease_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    elapsed_seconds: Mapped[float] = mapped_column(Float, default=0)


class Revision(Base):
    __tablename__ = "revisions"
    __table_args__ = (UniqueConstraint("job_id", "number"), UniqueConstraint("job_id", "operation_key"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(String(36), index=True)
    number: Mapped[int] = mapped_column(Integer)
    operation_key: Mapped[str] = mapped_column(String(160))
    draft: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    artifacts: Mapped[dict] = mapped_column(JSON)
    reviews: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), index=True)
    stage: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Usage(Base):
    __tablename__ = "usage"
    __table_args__ = (UniqueConstraint("job_id", "call_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), index=True)
    call_key: Mapped[str] = mapped_column(String(64))
    stage: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0)
    full_context_tokens: Mapped[int] = mapped_column(Integer, default=0)
    selected_context_tokens: Mapped[int] = mapped_column(Integer, default=0)
    seconds: Mapped[float] = mapped_column(Float, default=0)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="reserved")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Publication(Base):
    __tablename__ = "publications"
    __table_args__ = (UniqueConstraint("job_id", "revision_id"), UniqueConstraint("job_id", "version"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(String(36), index=True)
    revision_id: Mapped[str] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer)
    approval_hash: Mapped[str] = mapped_column(String(64))
    teacher_name: Mapped[str] = mapped_column(String(120))
    approval: Mapped[dict] = mapped_column(JSON)
    artifacts: Mapped[dict] = mapped_column(JSON)
    package_key: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


@lru_cache
def engine():
    url = settings().database_url
    kwargs = {"connect_args": {"check_same_thread": False, "timeout": 30}} if url.startswith("sqlite") else {}
    return create_engine(url, **kwargs)


def init_db():
    from filelock import FileLock
    # Web and worker start together and share the data volume.
    with FileLock(str(settings().data_dir / "schema-init.lock")):
        Base.metadata.create_all(engine())


@contextmanager
def session():
    with sessionmaker(engine(), expire_on_commit=False)() as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise


def event(job_id, stage, message, details=None):
    with session() as db:
        db.add(Event(job_id=job_id, stage=stage, message=message, details=details or {}))


def set_status(job_id, status, message):
    remaining_seconds(job_id)
    with session() as db:
        job = db.get(Job, job_id)
        job.status = status
        job.updated_at = now()
        db.add(Event(job_id=job_id, stage=status, message=message, details={}))


def claim_job():
    token = new_id()
    with session() as db:
        eligible = (Job.runnable.is_(True), (Job.lease_until.is_(None) | (Job.lease_until < now())))
        job_id = db.scalar(select(Job.id).where(*eligible).order_by(Job.created_at).limit(1))
        if not job_id:
            return None
        result = db.execute(update(Job).where(Job.id == job_id, *eligible).values(
            lease_token=token, lease_until=now() + timedelta(seconds=90)))
        return (job_id, token) if result.rowcount else None


def heartbeat(job_id, token):
    with session() as db:
        db.execute(update(Job).where(Job.id == job_id, Job.lease_token == token).values(
            lease_until=now() + timedelta(seconds=90)))
