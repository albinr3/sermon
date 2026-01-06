from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models import ClipStatus, SermonStatus


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


class ClipUpdate(BaseModel):
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    status: Optional[ClipStatus] = None
    output_url: Optional[str] = None


class ClipRead(BaseModel):
    id: int
    sermon_id: int
    start_ms: int
    end_ms: int
    output_url: Optional[str]
    download_url: Optional[str] = None
    status: ClipStatus
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptSegmentRead(BaseModel):
    id: int
    sermon_id: int
    start_ms: int
    end_ms: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True
