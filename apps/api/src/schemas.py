from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models import (
    ClipReframeMode,
    ClipRenderType,
    ClipSource,
    ClipStatus,
    SermonStatus,
)


class SermonCreate(BaseModel):
    title: Optional[str] = None
    filename: Optional[str] = None


class SermonUpdate(BaseModel):
    title: Optional[str] = None
    source_url: Optional[str] = None
    status: Optional[SermonStatus] = None


class SermonCreateResponse(BaseModel):
    sermon: SermonRead
    upload_url: str
    object_key: str


class UploadCompleteResponse(BaseModel):
    sermon: SermonRead


class SuggestClipsResponse(BaseModel):
    sermon_id: int
    status: str


class EmbedResponse(BaseModel):
    sermon_id: int
    status: str


class SermonRead(BaseModel):
    id: int
    title: Optional[str]
    source_url: Optional[str]
    progress: int
    status: SermonStatus
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClipCreate(BaseModel):
    sermon_id: int
    start_ms: int
    end_ms: int
    source: Optional[ClipSource] = None
    score: Optional[float] = None
    rationale: Optional[str] = None
    template_id: Optional[str] = None
    reframe_mode: Optional[ClipReframeMode] = None
    render_type: Optional[ClipRenderType] = None


class ClipUpdate(BaseModel):
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    status: Optional[ClipStatus] = None
    output_url: Optional[str] = None
    source: Optional[ClipSource] = None
    score: Optional[float] = None
    rationale: Optional[str] = None
    template_id: Optional[str] = None
    reframe_mode: Optional[ClipReframeMode] = None
    render_type: Optional[ClipRenderType] = None


class ClipRead(BaseModel):
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
    template_id: Optional[str]
    reframe_mode: ClipReframeMode
    render_type: ClipRenderType
    created_at: datetime

    class Config:
        from_attributes = True


class ClipSuggestionsResponse(BaseModel):
    sermon_id: int
    clips: list[ClipRead]


class ClipAcceptResponse(BaseModel):
    suggestion_id: int
    clip: ClipRead


class ClipRenderResponse(BaseModel):
    clip_id: int
    status: str
    render_type: ClipRenderType


class TranscriptSegmentRead(BaseModel):
    id: int
    sermon_id: int
    start_ms: int
    end_ms: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    segment_id: int
    text: str
    start_ms: int
    end_ms: int


class SearchResponse(BaseModel):
    sermon_id: int
    query: str
    results: list[SearchResult]


class TemplateConfig(BaseModel):
    font: str
    font_size: int
    y_pos: int
    max_words_per_line: int
    highlight_mode: str
    safe_margins: dict


class TemplateCreate(BaseModel):
    id: str
    name: str
    config_json: TemplateConfig


class TemplateRead(BaseModel):
    id: str
    name: str
    config_json: TemplateConfig
    created_at: datetime

    class Config:
        from_attributes = True
