import logging
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import settings
from src.db import get_session
from src.embeddings import embed_text
from src.models import (
    Clip,
    ClipSource,
    Sermon,
    SermonStatus,
    TranscriptEmbedding,
    TranscriptSegment,
)
from src.schemas import (
    ClipSuggestionsResponse,
    EmbedResponse,
    SearchResponse,
    SearchResult,
    SermonCreate,
    SermonCreateResponse,
    SermonRead,
    SermonUpdate,
    SuggestClipsResponse,
    TranscriptSegmentRead,
    UploadCompleteResponse,
)
from src.storage import create_presigned_get_url, create_presigned_put_url
from src.celery_app import celery_app

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=SermonCreateResponse, status_code=status.HTTP_201_CREATED)
def create_sermon(
    payload: SermonCreate, session: Session = Depends(get_session)
) -> SermonCreateResponse:
    sermon = Sermon(title=payload.title, progress=0)
    session.add(sermon)
    session.commit()
    session.refresh(sermon)

    filename = payload.filename or "upload.mp4"
    safe_name = os.path.basename(filename) or "upload.mp4"
    object_key = f"sermons/{sermon.id}/{uuid4().hex}-{safe_name}"

    try:
        upload_url = create_presigned_put_url(object_key, None, 3600)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to create upload URL") from exc

    sermon.source_url = object_key
    session.commit()
    session.refresh(sermon)

    return SermonCreateResponse(
        sermon=sermon, upload_url=upload_url, object_key=object_key
    )


@router.get("/", response_model=list[SermonRead])
def list_sermons(session: Session = Depends(get_session)) -> list[Sermon]:
    result = session.execute(select(Sermon).order_by(Sermon.id.desc()))
    return list(result.scalars().all())


@router.get("/{sermon_id}", response_model=SermonRead)
def get_sermon(sermon_id: int, session: Session = Depends(get_session)) -> Sermon:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    return sermon


@router.patch("/{sermon_id}", response_model=SermonRead)
def update_sermon(
    sermon_id: int, payload: SermonUpdate, session: Session = Depends(get_session)
) -> Sermon:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(sermon, key, value)

    session.commit()
    session.refresh(sermon)
    return sermon


@router.delete("/{sermon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sermon(sermon_id: int, session: Session = Depends(get_session)) -> None:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    session.delete(sermon)
    session.commit()


@router.get("/{sermon_id}/segments", response_model=list[TranscriptSegmentRead])
def list_segments(
    sermon_id: int, session: Session = Depends(get_session)
) -> list[TranscriptSegment]:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")

    result = session.execute(
        select(TranscriptSegment)
        .where(TranscriptSegment.sermon_id == sermon_id)
        .order_by(TranscriptSegment.start_ms.asc())
    )
    return list(result.scalars().all())


@router.post(
    "/{sermon_id}/upload-complete",
    response_model=UploadCompleteResponse,
    status_code=status.HTTP_200_OK,
)
def upload_complete(
    sermon_id: int, session: Session = Depends(get_session)
) -> UploadCompleteResponse:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    if not sermon.source_url:
        raise HTTPException(status_code=400, detail="Missing source object key")

    sermon.status = SermonStatus.uploaded
    sermon.progress = 5
    session.commit()
    session.refresh(sermon)

    try:
        celery_app.send_task(
            "worker.transcribe_sermon",
            args=[sermon.id],
            priority=settings.celery_priority_transcribe,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to enqueue transcribe") from exc

    return UploadCompleteResponse(sermon=sermon)


@router.post(
    "/{sermon_id}/embed",
    response_model=EmbedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def embed_sermon(
    sermon_id: int, session: Session = Depends(get_session)
) -> EmbedResponse:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")

    try:
        celery_app.send_task(
            "worker.generate_embeddings",
            args=[sermon.id],
            priority=settings.celery_priority_embed,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Failed to enqueue embeddings"
        ) from exc

    return EmbedResponse(sermon_id=sermon.id, status="queued")


@router.post(
    "/{sermon_id}/suggest",
    response_model=SuggestClipsResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def suggest_clips(
    sermon_id: int,
    use_llm: bool | None = None,
    session: Session = Depends(get_session),
) -> SuggestClipsResponse:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")

    try:
        use_llm_effective = (
            settings.use_llm_for_clip_suggestions if use_llm is None else use_llm
        )
        celery_app.send_task(
            "worker.suggest_clips",
            args=[sermon.id],
            kwargs={"use_llm": use_llm_effective},
            priority=settings.celery_priority_suggest,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Failed to enqueue clip suggestions"
        ) from exc

    return SuggestClipsResponse(sermon_id=sermon.id, status="enqueued")


@router.get(
    "/{sermon_id}/suggestions",
    response_model=ClipSuggestionsResponse,
)
def list_suggestions(
    sermon_id: int, session: Session = Depends(get_session)
) -> ClipSuggestionsResponse:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")

    result = session.execute(
        select(Clip)
        .where(Clip.sermon_id == sermon_id, Clip.source == ClipSource.auto)
        .order_by(Clip.score.desc().nullslast(), Clip.id.desc())
    )
    clips = list(result.scalars().all())
    for clip in clips:
        if clip.output_url:
            try:
                clip.download_url = create_presigned_get_url(clip.output_url, 3600)
            except Exception:
                logger.exception("Failed to create presigned URL for clip %s", clip.id)
    return ClipSuggestionsResponse(sermon_id=sermon_id, clips=clips)


@router.get(
    "/{sermon_id}/search",
    response_model=SearchResponse,
)
def search_sermon(
    sermon_id: int,
    q: str,
    k: int = 10,
    session: Session = Depends(get_session),
) -> SearchResponse:
    sermon = session.get(Sermon, sermon_id)
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    limit = min(max(k, 1), 50)

    query_vector = embed_text(query)
    stmt = (
        select(
            TranscriptEmbedding.segment_id,
            TranscriptSegment.text,
            TranscriptSegment.start_ms,
            TranscriptSegment.end_ms,
        )
        .join(
            TranscriptSegment,
            TranscriptEmbedding.segment_id == TranscriptSegment.id,
        )
        .where(TranscriptEmbedding.sermon_id == sermon_id)
        .order_by(TranscriptEmbedding.embedding.l2_distance(query_vector))
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    results = [
        SearchResult(
            segment_id=row.segment_id,
            text=row.text,
            start_ms=row.start_ms,
            end_ms=row.end_ms,
        )
        for row in rows
    ]
    return SearchResponse(sermon_id=sermon_id, query=query, results=results)
