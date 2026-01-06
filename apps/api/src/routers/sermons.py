import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import get_session
from src.models import Sermon, SermonStatus, TranscriptSegment
from src.schemas import (
    SermonCreate,
    SermonCreateResponse,
    SermonRead,
    SermonUpdate,
    TranscriptSegmentRead,
    UploadCompleteResponse,
)
from src.storage import create_presigned_put_url
from src.celery_app import celery_app

router = APIRouter()


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
        celery_app.send_task("worker.transcribe_sermon", args=[sermon.id])
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to enqueue transcribe") from exc

    return UploadCompleteResponse(sermon=sermon)
