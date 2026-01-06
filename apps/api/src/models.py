from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SermonStatus(str, Enum):
    pending = "pending"
    uploaded = "uploaded"
    processing = "processing"
    transcribed = "transcribed"
    error = "error"
    completed = "completed"
    failed = "failed"


class ClipStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class Sermon(Base):
    __tablename__ = "sermons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[SermonStatus] = mapped_column(
        SqlEnum(SermonStatus, name="sermon_status"), default=SermonStatus.pending
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    segments: Mapped[List[TranscriptSegment]] = relationship(
        back_populates="sermon", cascade="all, delete-orphan"
    )
    clips: Mapped[List[Clip]] = relationship(
        back_populates="sermon", cascade="all, delete-orphan"
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sermon_id: Mapped[int] = mapped_column(ForeignKey("sermons.id"), index=True)
    start_ms: Mapped[int] = mapped_column(Integer)
    end_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    sermon: Mapped[Sermon] = relationship(back_populates="segments")


class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sermon_id: Mapped[int] = mapped_column(ForeignKey("sermons.id"), index=True)
    start_ms: Mapped[int] = mapped_column(Integer)
    end_ms: Mapped[int] = mapped_column(Integer)
    output_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[ClipStatus] = mapped_column(
        SqlEnum(ClipStatus, name="clip_status"), default=ClipStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    sermon: Mapped[Sermon] = relationship(back_populates="clips")
