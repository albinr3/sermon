from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.db import get_session
from src.models import Clip, ClipStatus
from src.schemas import ClipCreate, ClipRead, ClipUpdate
from src.storage import create_presigned_get_url

router = APIRouter()

MIN_DURATION_MS = 10_000
MAX_DURATION_MS = 120_000


@router.post("/", response_model=ClipRead, status_code=status.HTTP_201_CREATED)
def create_clip(payload: ClipCreate, session: Session = Depends(get_session)) -> Clip:
    if payload.end_ms <= payload.start_ms:
        raise HTTPException(status_code=400, detail="Invalid clip range")
    duration = payload.end_ms - payload.start_ms
    if duration < MIN_DURATION_MS or duration > MAX_DURATION_MS:
        raise HTTPException(status_code=400, detail="Clip duration out of bounds")

    clip = Clip(
        sermon_id=payload.sermon_id,
        start_ms=payload.start_ms,
        end_ms=payload.end_ms,
        status=ClipStatus.pending,
    )
    session.add(clip)
    session.commit()
    session.refresh(clip)

    try:
        celery_app.send_task("worker.render_clip", args=[clip.id])
    except Exception as exc:
        clip.status = ClipStatus.error
        session.commit()
        raise HTTPException(status_code=500, detail="Failed to enqueue clip") from exc

    return clip


@router.get("/", response_model=list[ClipRead])
def list_clips(session: Session = Depends(get_session)) -> list[Clip]:
    result = session.execute(select(Clip).order_by(Clip.id.desc()))
    clips = list(result.scalars().all())
    for clip in clips:
        if clip.output_url:
            clip.download_url = create_presigned_get_url(clip.output_url, 3600)
    return clips


@router.get("/{clip_id}", response_model=ClipRead)
def get_clip(clip_id: int, session: Session = Depends(get_session)) -> Clip:
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    if clip.output_url:
        clip.download_url = create_presigned_get_url(clip.output_url, 3600)
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
