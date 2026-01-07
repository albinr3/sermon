import os
import subprocess
import tempfile
from uuid import uuid4

from celery.utils.log import get_task_logger
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer
from sqlalchemy import delete, select

from src.ass import build_ass_from_segments
from src.celery_app import celery_app
from src.db import SessionLocal
from src.models import (
    Clip,
    ClipReframeMode,
    ClipRenderType,
    ClipSource,
    ClipStatus,
    Sermon,
    SermonStatus,
    Template,
    TranscriptEmbedding,
    TranscriptSegment,
)
from src.reframe import (
    build_segment_centers,
    compute_crop_x,
    compute_scaled_dims,
    detect_face_track,
    get_video_metadata,
)
from src.storage import download_object, upload_object

logger = get_task_logger(__name__)

MIN_CLIP_MS = 20_000
MAX_CLIP_MS = 60_000
MIN_SUGGESTIONS = 5
MAX_SUGGESTIONS = 15
LONG_GAP_MS = 1500
DEFAULT_TEMPLATE_CONFIG = {
    "font": "Arial",
    "font_size": 64,
    "y_pos": 1500,
    "max_words_per_line": 4,
    "highlight_mode": "none",
    "safe_margins": {"top": 120, "bottom": 120, "left": 120, "right": 120},
}
EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"
EMBEDDING_BATCH_SIZE = 64
PREVIEW_SETTINGS = {
    "width": 540,
    "height": 960,
    "video_bitrate": "900k",
    "audio_bitrate": "96k",
    "maxrate": "1000k",
    "bufsize": "2000k",
}
FINAL_SETTINGS = {
    "width": 1080,
    "height": 1920,
    "video_bitrate": "3500k",
    "audio_bitrate": "128k",
    "maxrate": "4000k",
    "bufsize": "8000k",
}

_embedding_model = None


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def _render_settings(render_type: ClipRenderType) -> dict:
    if render_type == ClipRenderType.preview:
        return PREVIEW_SETTINGS
    return FINAL_SETTINGS


def _count_words(text: str) -> int:
    return len([chunk for chunk in text.replace("\n", " ").split(" ") if chunk])


def _is_hook(text: str) -> bool:
    head = text.strip()[:80]
    if "!" in head or "?" in head:
        return True
    return _count_words(head) <= 6


def _score_candidate(text: str, gap_ms: int) -> tuple[float, str]:
    word_count = _count_words(text)
    text_penalty = 2.0 if word_count < 8 else 1.0 if word_count < 15 else 0.0
    gap_penalty = min(2.0, gap_ms / 3000.0)
    hook = _is_hook(text)
    hook_bonus = 1.5 if hook else 0.0
    score = (word_count / 10.0) + hook_bonus - text_penalty - gap_penalty
    rationale = (
        f"words={word_count}; gaps_ms={gap_ms}; hook={'yes' if hook else 'no'}"
    )
    return score, rationale


def _overlap_ratio(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    overlap = max(0, min(a_end, b_end) - max(a_start, b_start))
    if overlap <= 0:
        return 0.0
    a_len = a_end - a_start
    b_len = b_end - b_start
    if a_len <= 0 or b_len <= 0:
        return 0.0
    return overlap / min(a_len, b_len)


def _build_candidates(segments: list[TranscriptSegment]) -> list[dict]:
    candidates: list[dict] = []
    total_segments = len(segments)
    for start_idx in range(total_segments):
        start_ms = segments[start_idx].start_ms
        text_parts: list[str] = []
        gap_ms = 0
        prev_end = segments[start_idx].end_ms
        for end_idx in range(start_idx, total_segments):
            segment = segments[end_idx]
            if end_idx > start_idx:
                gap = max(0, segment.start_ms - prev_end)
                if gap > LONG_GAP_MS:
                    gap_ms += gap
                prev_end = segment.end_ms
            text_parts.append(segment.text)
            end_ms = segment.end_ms
            duration = end_ms - start_ms
            if duration < MIN_CLIP_MS:
                continue
            if duration > MAX_CLIP_MS:
                break
            text = " ".join(text_parts).strip()
            if not text:
                continue
            score, rationale = _score_candidate(text, gap_ms)
            candidates.append(
                {
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "score": score,
                    "rationale": rationale,
                }
            )
    return candidates


def _dedupe_candidates(candidates: list[dict]) -> list[dict]:
    selected: list[dict] = []
    for candidate in candidates:
        is_duplicate = False
        for chosen in selected:
            overlap = _overlap_ratio(
                candidate["start_ms"],
                candidate["end_ms"],
                chosen["start_ms"],
                chosen["end_ms"],
            )
            if overlap > 0.6:
                is_duplicate = True
                break
        if not is_duplicate:
            selected.append(candidate)
    return selected


def _resolve_template_config(session, clip: Clip) -> dict:
    if clip.template_id:
        template = session.get(Template, clip.template_id)
        if template and template.config_json:
            return template.config_json
        logger.warning("Template %s not found for clip %s", clip.template_id, clip.id)
    return DEFAULT_TEMPLATE_CONFIG


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


@celery_app.task(name="worker.suggest_clips")
def suggest_clips(sermon_id: int) -> dict:
    session = SessionLocal()
    sermon = None
    try:
        sermon = session.get(Sermon, sermon_id)
        if not sermon:
            raise ValueError("Sermon not found")

        segments_query = (
            select(TranscriptSegment)
            .where(TranscriptSegment.sermon_id == sermon_id)
            .order_by(TranscriptSegment.start_ms.asc())
        )
        segments = list(session.execute(segments_query).scalars().all())
        if not segments:
            raise ValueError("No transcript segments available")

        logger.info(
            "Suggesting clips for sermon %s using %s segments",
            sermon_id,
            len(segments),
        )

        candidates = _build_candidates(segments)
        if not candidates:
            raise ValueError("No candidate clips generated")

        candidates.sort(key=lambda item: item["score"], reverse=True)
        candidates = _dedupe_candidates(candidates)
        candidates.sort(key=lambda item: item["score"], reverse=True)
        candidates = candidates[:MAX_SUGGESTIONS]

        logger.info(
            "Generated %s candidate clips after dedupe for sermon %s",
            len(candidates),
            sermon_id,
        )

        session.execute(
            delete(Clip).where(
                Clip.sermon_id == sermon_id, Clip.source == ClipSource.auto
            )
        )

        created = 0
        for candidate in candidates:
            session.add(
                Clip(
                    sermon_id=sermon_id,
                    start_ms=candidate["start_ms"],
                    end_ms=candidate["end_ms"],
                    source=ClipSource.auto,
                    score=candidate["score"],
                    rationale=candidate["rationale"],
                    status=ClipStatus.pending,
                )
            )
            created += 1

        session.commit()

        if created >= MIN_SUGGESTIONS:
            sermon.status = SermonStatus.suggested
        else:
            logger.warning(
                "Only %s suggestions generated for sermon %s",
                created,
                sermon_id,
            )
            sermon.status = SermonStatus.suggested
        session.commit()

        logger.info(
            "Saved %s clip suggestions for sermon %s",
            created,
            sermon_id,
        )
        return {"sermon_id": sermon_id, "suggestions": created}
    except Exception as exc:
        session.rollback()
        if sermon is not None:
            sermon.status = SermonStatus.error
            sermon.error_message = str(exc)[:1000]
            session.commit()
        logger.exception("Failed to suggest clips for sermon %s", sermon_id)
        raise
    finally:
        session.close()


@celery_app.task(name="worker.generate_embeddings")
def generate_embeddings(sermon_id: int) -> dict:
    session = SessionLocal()
    sermon = None
    try:
        sermon = session.get(Sermon, sermon_id)
        if not sermon:
            raise ValueError("Sermon not found")

        segments = list(
            session.execute(
                select(TranscriptSegment)
                .where(TranscriptSegment.sermon_id == sermon_id)
                .order_by(TranscriptSegment.start_ms.asc())
            ).scalars()
        )
        if not segments:
            raise ValueError("No transcript segments available")

        session.execute(
            delete(TranscriptEmbedding).where(
                TranscriptEmbedding.sermon_id == sermon_id
            )
        )
        session.commit()

        model = _get_embedding_model()
        total = len(segments)
        processed = 0

        for start in range(0, total, EMBEDDING_BATCH_SIZE):
            batch = segments[start : start + EMBEDDING_BATCH_SIZE]
            texts = [segment.text for segment in batch]
            embeddings = model.encode(texts, normalize_embeddings=False)

            for segment, embedding in zip(batch, embeddings):
                session.add(
                    TranscriptEmbedding(
                        sermon_id=sermon_id,
                        segment_id=segment.id,
                        text=segment.text,
                        embedding=embedding.tolist(),
                    )
                )
            session.commit()
            processed += len(batch)
            logger.info(
                "Embedded %s/%s transcript segments for sermon %s",
                processed,
                total,
                sermon_id,
            )

        sermon.status = SermonStatus.embedded
        session.commit()
        logger.info("Embedding complete for sermon %s", sermon_id)
        return {"sermon_id": sermon_id, "segments": total}
    except Exception as exc:
        session.rollback()
        if sermon is not None:
            sermon.status = SermonStatus.error
            sermon.error_message = str(exc)[:1000]
            session.commit()
        logger.exception("Failed to generate embeddings for sermon %s", sermon_id)
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

        caption_segments = []
        for segment in segments:
            start_ms = max(segment.start_ms, clip.start_ms) - clip.start_ms
            end_ms = min(segment.end_ms, clip.end_ms) - clip.start_ms
            if end_ms <= 0:
                continue
            caption_segments.append((start_ms, end_ms, segment.text))

        if not caption_segments:
            raise ValueError("Empty transcript for clip range")

        render_type = clip.render_type or ClipRenderType.final
        settings = _render_settings(render_type)
        target_width = settings["width"]
        target_height = settings["height"]
        video_bitrate = settings["video_bitrate"]
        audio_bitrate = settings["audio_bitrate"]
        maxrate = settings["maxrate"]
        bufsize = settings["bufsize"]

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = f"{tmpdir}/input.mp4"
            ass_path = f"{tmpdir}/captions.ass"
            output_path = f"{tmpdir}/output.mp4"

            download_object(sermon.source_url, input_path)

            template_config = _resolve_template_config(session, clip)
            with open(ass_path, "w", encoding="utf-8") as handle:
                handle.write(build_ass_from_segments(caption_segments, template_config))

            start_sec = clip.start_ms / 1000.0
            end_sec = clip.end_ms / 1000.0

            if clip.reframe_mode == ClipReframeMode.face:
                clip_path = f"{tmpdir}/clip_input.mp4"
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
                        "-c:v",
                        "libx264",
                        "-preset",
                        "veryfast",
                        "-b:v",
                        video_bitrate,
                        "-maxrate",
                        maxrate,
                        "-bufsize",
                        bufsize,
                        "-c:a",
                        "aac",
                        "-b:a",
                        audio_bitrate,
                        clip_path,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                metadata = get_video_metadata(clip_path)
                track = detect_face_track(clip_path, target_fps=2.0, smooth_window=5)
                segment_files: list[str] = []

                if not track or not metadata:
                    logger.warning(
                        "Face tracking unavailable for clip %s, using center crop",
                        clip_id,
                    )
                else:
                    scale_w, scale_h = compute_scaled_dims(
                        metadata.width,
                        metadata.height,
                        target_width=target_width,
                        target_height=target_height,
                    )
                    duration_ms = int((end_sec - start_sec) * 1000)
                    segment_ms = 500
                    centers = build_segment_centers(
                        track, duration_ms, segment_ms=segment_ms, default_center=0.5
                    )

                    segments_dir = f"{tmpdir}/segments"
                    os.makedirs(segments_dir, exist_ok=True)
                    for index, (t_ms, center_norm) in enumerate(centers):
                        seg_start = t_ms / 1000.0
                        seg_duration = min(segment_ms, duration_ms - t_ms) / 1000.0
                        if seg_duration <= 0:
                            continue
                        crop_x = compute_crop_x(center_norm, scale_w, target_width)
                        segment_path = f"{segments_dir}/seg_{index:04d}.mp4"
                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-ss",
                                str(seg_start),
                                "-t",
                                str(seg_duration),
                                "-i",
                                clip_path,
                                "-vf",
                                f"scale={scale_w}:{scale_h},crop={target_width}:{target_height}:{crop_x}:0",
                                "-c:v",
                                "libx264",
                                "-preset",
                                "veryfast",
                                "-b:v",
                                video_bitrate,
                                "-maxrate",
                                maxrate,
                                "-bufsize",
                                bufsize,
                                "-c:a",
                                "aac",
                                "-b:a",
                                audio_bitrate,
                                segment_path,
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        segment_files.append(segment_path)

                    if segment_files:
                        concat_path = f"{tmpdir}/concat.txt"
                        with open(concat_path, "w", encoding="utf-8") as handle:
                            for path in segment_files:
                                handle.write(f"file '{path}'\n")

                        concat_output = f"{tmpdir}/concat.mp4"
                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-f",
                                "concat",
                                "-safe",
                                "0",
                                "-i",
                                concat_path,
                                "-c:v",
                                "libx264",
                                "-preset",
                                "veryfast",
                                "-b:v",
                                video_bitrate,
                                "-maxrate",
                                maxrate,
                                "-bufsize",
                                bufsize,
                                "-c:a",
                                "aac",
                                "-b:a",
                                audio_bitrate,
                                concat_output,
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )

                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-i",
                                concat_output,
                                "-vf",
                                "subtitles=captions.ass",
                                "-c:v",
                                "libx264",
                                "-preset",
                                "veryfast",
                                "-b:v",
                                video_bitrate,
                                "-maxrate",
                                maxrate,
                                "-bufsize",
                                bufsize,
                                "-c:a",
                                "aac",
                                "-b:a",
                                audio_bitrate,
                                output_path,
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                            cwd=tmpdir,
                        )
                    else:
                        logger.warning(
                            "Face tracking yielded no segments for clip %s, using center crop",
                            clip_id,
                        )

                if not track or not metadata or not segment_files:
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
                            f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
                            f"crop={target_width}:{target_height},subtitles=captions.ass",
                            "-c:v",
                            "libx264",
                            "-preset",
                            "veryfast",
                            "-b:v",
                            video_bitrate,
                            "-maxrate",
                            maxrate,
                            "-bufsize",
                            bufsize,
                            "-c:a",
                            "aac",
                            "-b:a",
                            audio_bitrate,
                            output_path,
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=tmpdir,
                    )
            else:
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
                        f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
                        f"crop={target_width}:{target_height},subtitles=captions.ass",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "veryfast",
                        "-b:v",
                        video_bitrate,
                        "-maxrate",
                        maxrate,
                        "-bufsize",
                        bufsize,
                        "-c:a",
                        "aac",
                        "-b:a",
                        audio_bitrate,
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
