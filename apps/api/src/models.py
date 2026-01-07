from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Boolean,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class SermonStatus(str, Enum):
    pending = "pending"
    uploaded = "uploaded"
    processing = "processing"
    transcribed = "transcribed"
    suggested = "suggested"
    embedded = "embedded"
    error = "error"
    completed = "completed"
    failed = "failed"


class ClipStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class ClipSource(str, Enum):
    manual = "manual"
    auto = "auto"


class ClipReframeMode(str, Enum):
    center = "center"
    face = "face"


class ClipRenderType(str, Enum):
    preview = "preview"
    final = "final"


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


class TranscriptEmbedding(Base):
    __tablename__ = "transcript_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sermon_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    segment_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    config_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    clips: Mapped[List[Clip]] = relationship(back_populates="template")


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
    # Auto suggestions are stored in clips with source="auto" to avoid a parallel table.
    source: Mapped[ClipSource] = mapped_column(
        SqlEnum(ClipSource, name="clip_source"),
        default=ClipSource.manual,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_llm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    llm_trim: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    llm_trim_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    trim_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("templates.id"), nullable=True
    )
    reframe_mode: Mapped[ClipReframeMode] = mapped_column(
        SqlEnum(ClipReframeMode, name="clip_reframe_mode"),
        default=ClipReframeMode.center,
    )
    render_type: Mapped[ClipRenderType] = mapped_column(
        SqlEnum(ClipRenderType, name="clip_render_type"),
        default=ClipRenderType.final,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    sermon: Mapped[Sermon] = relationship(back_populates="clips")
    template: Mapped[Template | None] = relationship(back_populates="clips")


class ClipFeedback(Base):
    __tablename__ = "clip_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clip_id: Mapped[int] = mapped_column(ForeignKey("clips.id"), index=True)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
