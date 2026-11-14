from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Exercise(Base):
    __tablename__ = "exercises"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    language: Mapped[str] = mapped_column(String(20), index=True)
    difficulty: Mapped[str] = mapped_column(String(20))
    author: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    files: Mapped[list] = mapped_column(JSON)
    flaws: Mapped[list] = mapped_column(JSON)  # never sent to the client before submit


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id"), index=True)
    comments: Mapped[list] = mapped_column(JSON)
    score: Mapped[int] = mapped_column(Integer)
    result: Mapped[dict] = mapped_column(JSON)
    xp_gain: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
