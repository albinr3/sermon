import subprocess
import tempfile
from uuid import uuid4

from celery.utils.log import get_task_logger
from faster_whisper import WhisperModel
from sqlalchemy import select

from src.celery_app import celery_app
from src.db import SessionLocal
from src.models import Clip, ClipStatus, Sermon, SermonStatus, TranscriptSegment
from src.srt import build_srt
from src.storage import download_object, upload_object

logger = get_task_logger(__name__)


@celery_app.task(name="worker.transcribe_sermon")
def transcribe_sermon(sermon_id: int) -> dict:
    session = SessionLocal()
    sermon = None
    try:
        sermon = session.get(Sermon, sermon_id)
        if not sermon:
            raise ValueError("Sermon not found")
        if not sermon.source_url:
            raise ValueError("Sermon has no source_url")

        sermon.status = SermonStatus.processing
        sermon.progress = 5
        sermon.error_message = None
        session.commit()

        with tempfile.TemporaryDirectory() as tmpdir:
            mp4_path = f"{tmpdir}/input.mp4"
            wav_path = f"{tmpdir}/audio.wav"

            download_object(sermon.source_url, mp4_path)

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    mp4_path,
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    wav_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            model = WhisperModel("small", device="cpu", compute_type="int8")
            segments, info = model.transcribe(wav_path)
            total_duration = getattr(info, "duration", None)
            if total_duration is None and isinstance(info, dict):
                total_duration = info.get("duration")

            count = 0
            last_progress = sermon.progress or 0
            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue
                session.add(
                    TranscriptSegment(
                        sermon_id=sermon.id,
                        start_ms=int(segment.start * 1000),
                        end_ms=int(segment.end * 1000),
                        text=text,
                    )
                )
                count += 1
                if total_duration:
                    progress = int(min(95, max(5, (segment.end / total_duration) * 90 + 5)))
                    if progress - last_progress >= 2:
                        sermon.progress = progress
                        session.commit()
                        last_progress = progress

            session.commit()

        sermon.status = SermonStatus.transcribed
        sermon.progress = 100
        session.commit()
        return {"sermon_id": sermon.id, "segments": count}
    except Exception as exc:
        session.rollback()
        if sermon is not None:
            sermon.status = SermonStatus.error
            sermon.error_message = str(exc)[:1000]
            session.commit()
        logger.exception("Failed to transcribe sermon %s", sermon_id)
        raise
    finally:
        session.close()


@celery_app.task(name="worker.render_clip")
def render_clip(clip_id: int) -> dict:
    session = SessionLocal()
    clip = None
    try:
        clip = session.get(Clip, clip_id)
        if not clip:
            raise ValueError("Clip not found")

        sermon = session.get(Sermon, clip.sermon_id)
        if not sermon or not sermon.source_url:
            raise ValueError("Sermon source not available")

        if clip.end_ms <= clip.start_ms:
            raise ValueError("Invalid clip range")

        clip.status = ClipStatus.processing
        session.commit()

        segments_query = (
            select(TranscriptSegment)
            .where(TranscriptSegment.sermon_id == clip.sermon_id)
            .where(TranscriptSegment.start_ms < clip.end_ms)
            .where(TranscriptSegment.end_ms > clip.start_ms)
            .order_by(TranscriptSegment.start_ms.asc())
        )
        segments = list(session.execute(segments_query).scalars().all())
        if not segments:
            raise ValueError("No transcript segments in range")

        srt_segments = []
        for segment in segments:
            start_ms = max(segment.start_ms, clip.start_ms) - clip.start_ms
            end_ms = min(segment.end_ms, clip.end_ms) - clip.start_ms
            if end_ms <= 0:
                continue
            srt_segments.append((start_ms, end_ms, segment.text))

        if not srt_segments:
            raise ValueError("Empty transcript for clip range")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = f"{tmpdir}/input.mp4"
            srt_path = f"{tmpdir}/captions.srt"
            output_path = f"{tmpdir}/output.mp4"

            download_object(sermon.source_url, input_path)

            with open(srt_path, "w", encoding="utf-8") as handle:
                handle.write(build_srt(srt_segments))

            start_sec = clip.start_ms / 1000.0
            end_sec = clip.end_ms / 1000.0

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    input_path,
                    "-ss",
                    str(start_sec),
                    "-to",
                    str(end_sec),
                    "-vf",
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,subtitles=captions.srt",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    output_path,
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )

            object_key = f"clips/{clip.id}/{uuid4().hex}.mp4"
            upload_object(output_path, object_key, "video/mp4")

        clip.output_url = object_key
        clip.status = ClipStatus.done
        session.commit()
        return {"clip_id": clip.id, "output_key": object_key}
    except Exception as exc:
        session.rollback()
        if clip is not None:
            clip.status = ClipStatus.error
            session.commit()
        logger.exception("Failed to render clip %s", clip_id)
        raise
    finally:
        session.close()
