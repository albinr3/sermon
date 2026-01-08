import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.config import settings
from src.db import get_session
from src.models import (
    Clip,
    ClipFeedback,
    ClipRenderType,
    ClipSource,
    ClipStatus,
    Template,
    TranscriptSegment,
)
from src.schemas import (
    ClipAcceptResponse,
    ClipFeedbackCreate,
    ClipFeedbackRead,
    ClipCreate,
    ClipRead,
    ClipRenderResponse,
    ClipUpdate,
)
from src.storage import create_presigned_get_url

router = APIRouter()
logger = logging.getLogger(__name__)

MIN_DURATION_MS = 10_000
MAX_DURATION_MS = 120_000


@router.post("/", response_model=ClipRead, status_code=status.HTTP_201_CREATED)
def create_clip(payload: ClipCreate, session: Session = Depends(get_session)) -> Clip:
    if payload.end_ms <= payload.start_ms:
        raise HTTPException(status_code=400, detail="Invalid clip range")
    duration = payload.end_ms - payload.start_ms
    if duration < MIN_DURATION_MS or duration > MAX_DURATION_MS:
        raise HTTPException(status_code=400, detail="Clip duration out of bounds")

    if payload.template_id:
        template = session.get(Template, payload.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

    clip = Clip(
        sermon_id=payload.sermon_id,
        start_ms=payload.start_ms,
        end_ms=payload.end_ms,
        status=ClipStatus.pending,
        template_id=payload.template_id,
        render_type=payload.render_type,
        reframe_mode=payload.reframe_mode,
    )
    session.add(clip)
    session.commit()
    session.refresh(clip)

    return clip


@router.get("/", response_model=list[ClipRead])
def list_clips(session: Session = Depends(get_session)) -> list[Clip]:
    result = session.execute(select(Clip).order_by(Clip.id.desc()))
    clips = list(result.scalars().all())
    for clip in clips:
        if clip.output_url:
            try:
                clip.download_url = create_presigned_get_url(clip.output_url, 3600)
            except Exception:
                logger.exception("Failed to create presigned URL for clip %s", clip.id)
    return clips


@router.get("/{clip_id}", response_model=ClipRead)
def get_clip(clip_id: int, session: Session = Depends(get_session)) -> Clip:
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    if clip.output_url:
        try:
            clip.download_url = create_presigned_get_url(clip.output_url, 3600)
        except Exception:
            logger.exception("Failed to create presigned URL for clip %s", clip.id)
    return clip


@router.patch("/{clip_id}", response_model=ClipRead)
def update_clip(
    clip_id: int, payload: ClipUpdate, session: Session = Depends(get_session)
) -> Clip:
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(clip, key, value)

    session.commit()
    session.refresh(clip)
    return clip


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clip(clip_id: int, session: Session = Depends(get_session)) -> None:
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    session.delete(clip)
    session.commit()


@router.post(
    "/{clip_id}/accept",
    response_model=ClipAcceptResponse,
    status_code=status.HTTP_201_CREATED,
)
def accept_clip(
    clip_id: int, session: Session = Depends(get_session)
) -> ClipAcceptResponse:
    suggestion = session.get(Clip, clip_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Clip not found")
    if suggestion.source != ClipSource.auto:
        raise HTTPException(status_code=400, detail="Clip is not a suggestion")

    duration = suggestion.end_ms - suggestion.start_ms
    if duration < MIN_DURATION_MS or duration > MAX_DURATION_MS:
        raise HTTPException(status_code=400, detail="Clip duration out of bounds")

    clip = Clip(
        sermon_id=suggestion.sermon_id,
        start_ms=suggestion.start_ms,
        end_ms=suggestion.end_ms,
        source=ClipSource.manual,
        status=ClipStatus.pending,
        template_id=suggestion.template_id,
        reframe_mode=suggestion.reframe_mode,
        render_type=suggestion.render_type,
    )
    session.add(clip)
    session.add(
        ClipFeedback(clip_id=suggestion.id, accepted=True, user_id=None)
    )
    session.commit()
    session.refresh(clip)

    return ClipAcceptResponse(suggestion_id=suggestion.id, clip=clip)


@router.post(
    "/{clip_id}/feedback",
    response_model=ClipFeedbackRead,
    status_code=status.HTTP_201_CREATED,
)
def record_feedback(
    clip_id: int,
    payload: ClipFeedbackCreate,
    session: Session = Depends(get_session),
) -> ClipFeedback:
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    feedback = ClipFeedback(
        clip_id=clip_id,
        accepted=payload.accepted,
        user_id=payload.user_id,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


@router.post(
    "/{clip_id}/apply-trim",
    response_model=ClipRead,
    status_code=status.HTTP_200_OK,
)
def apply_trim_suggestion(
    clip_id: int, session: Session = Depends(get_session)
) -> Clip:
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    if clip.source != ClipSource.auto:
        raise HTTPException(status_code=400, detail="Clip is not a suggestion")
    if clip.trim_applied:
        return clip
    trim = clip.llm_trim
    if not isinstance(trim, dict):
        raise HTTPException(status_code=400, detail="No trim suggestion available")
    start_offset = trim.get("start_offset_sec")
    end_offset = trim.get("end_offset_sec")
    try:
        start_offset_sec = max(0.0, float(start_offset or 0))
        end_offset_sec = abs(float(end_offset or 0))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid trim suggestion") from exc

    if start_offset_sec <= 0 and end_offset_sec <= 0:
        raise HTTPException(status_code=400, detail="Trim offsets are empty")

    new_start_ms = clip.start_ms + int(round(start_offset_sec * 1000))
    new_end_ms = clip.end_ms - int(round(end_offset_sec * 1000))
    if new_end_ms <= new_start_ms:
        raise HTTPException(status_code=400, detail="Trim range is invalid")

    segments = list(
        session.execute(
            select(TranscriptSegment)
            .where(TranscriptSegment.sermon_id == clip.sermon_id)
            .where(TranscriptSegment.start_ms < clip.end_ms)
            .where(TranscriptSegment.end_ms > clip.start_ms)
            .order_by(TranscriptSegment.start_ms.asc())
        )
        .scalars()
        .all()
    )
    if segments:
        new_start_idx = None
        for idx, segment in enumerate(segments):
            if segment.end_ms >= new_start_ms:
                new_start_idx = idx
                break
        new_end_idx = None
        for idx in range(len(segments) - 1, -1, -1):
            if segments[idx].start_ms <= new_end_ms:
                new_end_idx = idx
                break
        if new_start_idx is not None and new_end_idx is not None:
            if new_end_idx >= new_start_idx:
                new_start_ms = segments[new_start_idx].start_ms
                new_end_ms = segments[new_end_idx].end_ms
    duration = new_end_ms - new_start_ms
    if duration < MIN_DURATION_MS or duration > MAX_DURATION_MS:
        raise HTTPException(status_code=400, detail="Clip duration out of bounds")

    clip.start_ms = new_start_ms
    clip.end_ms = new_end_ms
    clip.trim_applied = True
    session.commit()
    session.refresh(clip)
    return clip


@router.post(
    "/{clip_id}/render",
    response_model=ClipRenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def render_clip(
    clip_id: int,
    type: ClipRenderType = Query(..., alias="type"),
    session: Session = Depends(get_session),
) -> ClipRenderResponse:
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    duration = clip.end_ms - clip.start_ms
    if duration < MIN_DURATION_MS or duration > MAX_DURATION_MS:
        raise HTTPException(status_code=400, detail="Clip duration out of bounds")

    clip.render_type = type
    clip.status = ClipStatus.pending
    session.commit()

    queue = "previews" if type == ClipRenderType.preview else "renders"
    priority = (
        settings.celery_priority_render_preview
        if type == ClipRenderType.preview
        else settings.celery_priority_render_final
    )
    try:
        celery_app.send_task(
            "worker.render_clip",
            args=[clip.id],
            queue=queue,
            priority=priority,
        )
    except Exception as exc:
        clip.status = ClipStatus.error
        session.commit()
        raise HTTPException(status_code=500, detail="Failed to enqueue clip") from exc

    return ClipRenderResponse(clip_id=clip.id, status="queued", render_type=type)
