from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.models import (
    ClipReframeMode,
    ClipRenderType,
    ClipSource,
    ClipStatus,
    SermonStatus,
)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ORMModel(StrictBaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, from_attributes=True)


class SermonCreate(StrictBaseModel):
    title: Optional[str] = None
    filename: Optional[str] = None


class SermonUpdate(StrictBaseModel):
    title: Optional[str] = None
    source_url: Optional[str] = None
    status: Optional[SermonStatus] = None


class SermonCreateResponse(StrictBaseModel):
    sermon: SermonRead
    upload_url: str
    object_key: str


class UploadCompleteResponse(StrictBaseModel):
    sermon: SermonRead


class SuggestClipsResponse(StrictBaseModel):
    sermon_id: int
    status: str


class EmbedResponse(StrictBaseModel):
    sermon_id: int
    status: str


class SermonRead(ORMModel):
    id: int
    title: Optional[str]
    source_url: Optional[str]
    source_download_url: Optional[str] = None
    progress: int
    status: SermonStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ClipCreate(StrictBaseModel):
    sermon_id: int
    start_ms: int
    end_ms: int
    source: Optional[ClipSource] = None
    score: Optional[float] = None
    rationale: Optional[str] = None
    template_id: Optional[str] = None
    reframe_mode: Optional[ClipReframeMode] = None
    render_type: Optional[ClipRenderType] = None


class ClipUpdate(StrictBaseModel):
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    status: Optional[ClipStatus] = None
    output_url: Optional[str] = None
    source: Optional[ClipSource] = None
    score: Optional[float] = None
    rationale: Optional[str] = None
    llm_trim: Optional[dict] = None
    llm_trim_confidence: Optional[float] = None
    trim_applied: Optional[bool] = None
    template_id: Optional[str] = None
    reframe_mode: Optional[ClipReframeMode] = None
    render_type: Optional[ClipRenderType] = None


class ClipRead(ORMModel):
    id: int
    sermon_id: int
    start_ms: int
    end_ms: int
    output_url: Optional[str]
    download_url: Optional[str] = None
    status: ClipStatus
    source: ClipSource
    score: Optional[float]
    rationale: Optional[str]
    use_llm: bool = False
    llm_trim: Optional[dict] = None
    llm_trim_confidence: Optional[float] = None
    trim_applied: bool = False
    template_id: Optional[str]
    reframe_mode: ClipReframeMode
    render_type: ClipRenderType
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ClipSuggestionsResponse(StrictBaseModel):
    sermon_id: int
    clips: list[ClipRead]


class ClipAcceptResponse(StrictBaseModel):
    suggestion_id: int
    clip: ClipRead


class ClipFeedbackCreate(StrictBaseModel):
    accepted: bool
    user_id: Optional[str] = None


class ClipFeedbackRead(ORMModel):
    id: int
    clip_id: int
    accepted: bool
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ClipRenderResponse(StrictBaseModel):
    clip_id: int
    status: str
    render_type: ClipRenderType


class TranscriptSegmentRead(ORMModel):
    id: int
    sermon_id: int
    start_ms: int
    end_ms: int
    text: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class SearchResult(StrictBaseModel):
    segment_id: int
    text: str
    start_ms: int
    end_ms: int


class SearchResponse(StrictBaseModel):
    sermon_id: int
    query: str
    results: list[SearchResult]


class TemplateConfig(StrictBaseModel):
    font: str
    font_size: int
    y_pos: int
    max_words_per_line: int
    highlight_mode: str
    safe_margins: dict


class TemplateCreate(StrictBaseModel):
    id: str
    name: str
    config_json: TemplateConfig


class TemplateRead(ORMModel):
    id: str
    name: str
    config_json: TemplateConfig
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
