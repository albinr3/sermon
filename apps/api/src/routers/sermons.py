import logging
import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from src.config import settings
from src.db import get_session
from src.embeddings import embed_text
from src.models import (
    Clip,
    ClipSource,
    ClipFeedback,
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
    sermon = Sermon(
        title=payload.title,
        description=payload.description,
        preacher=payload.preacher,
        series=payload.series,
        sermon_date=payload.sermon_date,
        tags=payload.tags,
        progress=0,
    )
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
def list_sermons(
    session: Session = Depends(get_session),
    limit: int | None = None,
    offset: int = 0,
    q: str | None = None,
    status: SermonStatus | None = None,
    tag: str | None = None,
) -> list[Sermon]:
    stmt = select(Sermon).where(Sermon.deleted_at.is_(None))
    if status is not None:
        stmt = stmt.where(Sermon.status == status)
    query = (q or "").strip()
    if query:
        term = f"%{query}%"
        clauses = [
            Sermon.title.ilike(term),
            Sermon.description.ilike(term),
            Sermon.preacher.ilike(term),
            Sermon.series.ilike(term),
        ]
        if query.isdigit():
            clauses.append(Sermon.id == int(query))
        stmt = stmt.where(or_(*clauses))
    tag_value = (tag or "").strip()
    if tag_value:
        stmt = stmt.where(Sermon.tags.contains([tag_value]))
    stmt = stmt.order_by(Sermon.sermon_date.desc().nullslast(), Sermon.id.desc())
    if offset > 0:
        stmt = stmt.offset(offset)
    if limit is not None and limit > 0:
        stmt = stmt.limit(min(limit, 200))
    result = session.execute(stmt)
    sermons = list(result.scalars().all())
    for sermon in sermons:
        if sermon.source_url:
            try:
                sermon.source_download_url = create_presigned_get_url(
                    sermon.source_url, 3600
                )
            except Exception:
                logger.exception(
                    "Failed to create presigned URL for sermon %s", sermon.id
                )
    return sermons


@router.get("/{sermon_id}", response_model=SermonRead)
def get_sermon(sermon_id: int, session: Session = Depends(get_session)) -> Sermon:
    sermon = session.get(Sermon, sermon_id)
    if not sermon or sermon.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sermon not found")
    if sermon.source_url:
        try:
            sermon.source_download_url = create_presigned_get_url(
                sermon.source_url, 3600
            )
        except Exception:
            logger.exception(
                "Failed to create presigned URL for sermon %s", sermon.id
            )
    return sermon


@router.patch("/{sermon_id}", response_model=SermonRead)
def update_sermon(
    sermon_id: int, payload: SermonUpdate, session: Session = Depends(get_session)
) -> Sermon:
    sermon = session.get(Sermon, sermon_id)
    if not sermon or sermon.deleted_at is not None:
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
    if not sermon or sermon.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sermon not found")
    now = datetime.utcnow()
    sermon.deleted_at = now
    sermon.updated_at = now
    session.execute(
        update(Clip)
        .where(Clip.sermon_id == sermon_id, Clip.deleted_at.is_(None))
        .values(deleted_at=now, updated_at=now)
    )
    session.execute(
        update(TranscriptSegment)
        .where(TranscriptSegment.sermon_id == sermon_id)
        .where(TranscriptSegment.deleted_at.is_(None))
        .values(deleted_at=now, updated_at=now)
    )
    session.execute(
        update(TranscriptEmbedding)
        .where(TranscriptEmbedding.sermon_id == sermon_id)
        .where(TranscriptEmbedding.deleted_at.is_(None))
        .values(deleted_at=now, updated_at=now)
    )
    clip_ids = select(Clip.id).where(Clip.sermon_id == sermon_id)
    session.execute(
        update(ClipFeedback)
        .where(ClipFeedback.clip_id.in_(clip_ids))
        .where(ClipFeedback.deleted_at.is_(None))
        .values(deleted_at=now, updated_at=now)
    )
    session.commit()


@router.get("/{sermon_id}/segments", response_model=list[TranscriptSegmentRead])
def list_segments(
    sermon_id: int,
    session: Session = Depends(get_session),
    limit: int | None = None,
    offset: int = 0,
) -> list[TranscriptSegment]:
    sermon = session.get(Sermon, sermon_id)
    if not sermon or sermon.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sermon not found")

    stmt = (
        select(TranscriptSegment)
        .where(
            TranscriptSegment.sermon_id == sermon_id,
            TranscriptSegment.deleted_at.is_(None),
        )
        .order_by(TranscriptSegment.start_ms.asc())
    )
    if offset > 0:
        stmt = stmt.offset(offset)
    if limit is not None and limit > 0:
        stmt = stmt.limit(min(limit, 1000))
    result = session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{sermon_id}/transcript-stats")
def transcript_stats(
    sermon_id: int, session: Session = Depends(get_session)
) -> dict:
    sermon = session.get(Sermon, sermon_id)
    if not sermon or sermon.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sermon not found")

    texts = session.execute(
        select(TranscriptSegment.text).where(
            TranscriptSegment.sermon_id == sermon_id,
            TranscriptSegment.deleted_at.is_(None),
        )
    ).scalars()
    word_count = 0
    char_count = 0
    for text in texts:
        if text:
            word_count += len(text.split())
            char_count += len(text)
    return {
        "sermon_id": sermon_id,
        "word_count": word_count,
        "char_count": char_count,
    }


@router.post(
    "/{sermon_id}/upload-complete",
    response_model=UploadCompleteResponse,
    status_code=status.HTTP_200_OK,
)
def upload_complete(
    sermon_id: int, session: Session = Depends(get_session)
) -> UploadCompleteResponse:
    sermon = session.get(Sermon, sermon_id)
    if not sermon or sermon.deleted_at is not None:
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
    if not sermon or sermon.deleted_at is not None:
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
    llm_method: str = Query(
        "scoring", regex="^(scoring|selection|generation|full-context)$"
    ),
    session: Session = Depends(get_session),
) -> SuggestClipsResponse:
    """Enqueue clip suggestions using LLM scoring or LLM selection."""
    sermon = session.get(Sermon, sermon_id)
    if not sermon or sermon.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sermon not found")

    try:
        use_llm_effective = (
            settings.use_llm_for_clip_suggestions if use_llm is None else use_llm
        )
        celery_app.send_task(
            "worker.suggest_clips",
            args=[sermon.id],
            kwargs={"use_llm": use_llm_effective, "llm_method": llm_method},
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
    if not sermon or sermon.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sermon not found")

    result = session.execute(
        select(Clip)
        .where(
            Clip.sermon_id == sermon_id,
            Clip.source == ClipSource.auto,
            Clip.deleted_at.is_(None),
        )
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


@router.delete(
    "/{sermon_id}/suggestions",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_suggestions(
    sermon_id: int, session: Session = Depends(get_session)
) -> None:
    sermon = session.get(Sermon, sermon_id)
    if not sermon or sermon.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sermon not found")

    now = datetime.utcnow()
    clip_ids = (
        select(Clip.id)
        .where(
            Clip.sermon_id == sermon_id,
            Clip.source == ClipSource.auto,
            Clip.deleted_at.is_(None),
        )
    )
    session.execute(
        update(Clip)
        .where(Clip.id.in_(clip_ids))
        .values(deleted_at=now, updated_at=now)
    )
    session.execute(
        update(ClipFeedback)
        .where(ClipFeedback.clip_id.in_(clip_ids))
        .where(ClipFeedback.deleted_at.is_(None))
        .values(deleted_at=now, updated_at=now)
    )
    session.commit()


@router.get(
    "/{sermon_id}/token-stats",
)
def token_stats(
    sermon_id: int, session: Session = Depends(get_session)
) -> dict:
    sermon = session.get(Sermon, sermon_id)
    if not sermon or sermon.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sermon not found")

    rows = session.execute(
        select(
            Clip.llm_method,
            func.count(Clip.id),
            func.coalesce(func.sum(Clip.llm_prompt_tokens), 0),
            func.coalesce(func.sum(Clip.llm_completion_tokens), 0),
            func.coalesce(func.sum(Clip.llm_total_tokens), 0),
            func.coalesce(func.sum(Clip.llm_estimated_cost), 0.0),
            func.coalesce(
                func.sum(Clip.llm_output_tokens),
                func.sum(Clip.llm_completion_tokens),
                0,
            ),
            func.coalesce(func.sum(Clip.llm_cache_hit_tokens), 0),
            func.coalesce(func.sum(Clip.llm_cache_miss_tokens), 0),
        )
        .where(
            Clip.sermon_id == sermon_id,
            Clip.source == ClipSource.auto,
            Clip.deleted_at.is_(None),
            Clip.llm_method.is_not(None),
        )
        .group_by(Clip.llm_method)
    ).all()

    methods: dict[str, dict] = {}
    for row in rows:
        method = row[0]
        methods[method] = {
            "clips": int(row[1] or 0),
            "prompt_tokens": int(row[2] or 0),
            "completion_tokens": int(row[3] or 0),
            "total_tokens": int(row[4] or 0),
            "estimated_cost_usd": float(row[5] or 0.0),
            "output_tokens": int(row[6] or 0),
            "cache_hit_tokens": int(row[7] or 0),
            "cache_miss_tokens": int(row[8] or 0),
        }

    comparison = None
    base_method = None
    compare_method = None
    if "selection" in methods and "full-context" in methods:
        base_method = "selection"
        compare_method = "full-context"
    elif "generation" in methods and "full-context" in methods:
        base_method = "generation"
        compare_method = "full-context"
    elif "scoring" in methods and "full-context" in methods:
        base_method = "scoring"
        compare_method = "full-context"
    elif "selection" in methods and "generation" in methods:
        base_method = "selection"
        compare_method = "generation"
    elif "scoring" in methods and "selection" in methods:
        base_method = "scoring"
        compare_method = "selection"
    elif "scoring" in methods and "generation" in methods:
        base_method = "scoring"
        compare_method = "generation"
    if base_method and compare_method:
        base = methods[base_method]
        compare = methods[compare_method]
        token_delta = compare["total_tokens"] - base["total_tokens"]
        cost_delta = compare["estimated_cost_usd"] - base["estimated_cost_usd"]
        token_pct_increase = None
        if base["total_tokens"] > 0:
            token_pct_increase = (token_delta / base["total_tokens"]) * 100.0
        comparison = {
            "base_method": base_method,
            "compare_method": compare_method,
            "token_delta": token_delta,
            "token_pct_increase": token_pct_increase,
            "cost_delta_usd": cost_delta,
        }

    return {"sermon_id": sermon_id, "methods": methods, "comparison": comparison}


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
    if not sermon or sermon.deleted_at is not None:
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
        .where(TranscriptEmbedding.deleted_at.is_(None))
        .where(TranscriptSegment.deleted_at.is_(None))
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
