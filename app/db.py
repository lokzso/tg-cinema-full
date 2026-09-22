from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    MetaData, Table, Column, Integer, BigInteger, String, Float, DateTime,
    UniqueConstraint, create_engine, select, update, delete, insert
)

from .config import settings


def _utcnow():
    return datetime.now(timezone.utc)


_url = settings.effective_database_url
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}
engine = create_engine(_url, pool_pre_ping=True, connect_args=_connect_args)
metadata = MetaData()

users = Table(
    "users", metadata,
    Column("id", BigInteger, primary_key=True),
    Column("username", String(255)),
    Column("first_name", String(255)),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

progress = Table(
    "progress", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, nullable=False, index=True),
    Column("title_id", String(255), nullable=False),
    Column("season", Integer, nullable=False),
    Column("episode", Integer, nullable=False),
    Column("position", Float, nullable=False, default=0),
    Column("duration", Float, nullable=False, default=0),
    Column("source_id", String(255)),
    Column("voice_id", String(255)),
    Column("quality", String(64)),
    Column("updated_at", DateTime(timezone=True), nullable=False, index=True),
    UniqueConstraint("user_id", "title_id", "season", "episode", name="uq_progress_item"),
)

favorites = Table(
    "favorites", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, nullable=False, index=True),
    Column("title_id", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("user_id", "title_id", name="uq_favorite_item"),
)


def init_db():
    metadata.create_all(engine)


def upsert_user(user_id: int, username: str | None, first_name: str | None):
    now = _utcnow()
    with engine.begin() as c:
        exists = c.execute(select(users.c.id).where(users.c.id == user_id)).first()
        if exists:
            c.execute(update(users).where(users.c.id == user_id).values(username=username, first_name=first_name))
        else:
            c.execute(insert(users).values(id=user_id, username=username, first_name=first_name, created_at=now))


def save_progress(p: dict):
    now = _utcnow()
    key = (
        (progress.c.user_id == p["user_id"]) &
        (progress.c.title_id == p["title_id"]) &
        (progress.c.season == p["season"]) &
        (progress.c.episode == p["episode"])
    )
    values = dict(
        position=p.get("position", 0), duration=p.get("duration", 0),
        source_id=p.get("source_id"), voice_id=p.get("voice_id"),
        quality=p.get("quality"), updated_at=now,
    )
    with engine.begin() as c:
        row = c.execute(select(progress.c.id).where(key)).first()
        if row:
            c.execute(update(progress).where(key).values(**values))
        else:
            c.execute(insert(progress).values(
                user_id=p["user_id"], title_id=p["title_id"], season=p["season"], episode=p["episode"], **values
            ))


def get_progress(user_id: int, title_id: str, season: int, episode: int):
    stmt = select(progress).where(
        (progress.c.user_id == user_id) &
        (progress.c.title_id == title_id) &
        (progress.c.season == season) &
        (progress.c.episode == episode)
    )
    with engine.connect() as c:
        row = c.execute(stmt).mappings().first()
        return dict(row) if row else None


def get_continue(user_id: int, limit: int = 20):
    stmt = select(progress).where(progress.c.user_id == user_id).order_by(progress.c.updated_at.desc()).limit(limit)
    with engine.connect() as c:
        return [dict(r) for r in c.execute(stmt).mappings().all()]


def toggle_favorite(user_id: int, title_id: str):
    stmt = select(favorites.c.id).where((favorites.c.user_id == user_id) & (favorites.c.title_id == title_id))
    with engine.begin() as c:
        row = c.execute(stmt).first()
        if row:
            c.execute(delete(favorites).where(favorites.c.id == row.id))
            return False
        c.execute(insert(favorites).values(user_id=user_id, title_id=title_id, created_at=_utcnow()))
        return True


def favorite_ids(user_id: int):
    stmt = select(favorites.c.title_id).where(favorites.c.user_id == user_id).order_by(favorites.c.created_at.desc())
    with engine.connect() as c:
        return [r[0] for r in c.execute(stmt).all()]


def database_kind() -> str:
    return engine.url.get_backend_name()
