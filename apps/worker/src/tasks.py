import os
import random
import re
import subprocess
import tempfile
import unicodedata
from datetime import datetime
from uuid import uuid4

from celery.utils.log import get_task_logger
from botocore.exceptions import BotoCoreError, ClientError
from faster_whisper import WhisperModel
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError

from src.ass import build_ass_from_segments
from src.celery_app import celery_app
from src.config import settings
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
from src.services.deepseek_client import DeepseekClientError, score_clip_candidates
from src.storage import download_object, upload_object

logger = get_task_logger(__name__)

MIN_CLIP_MS = 30_000
MAX_CLIP_MS = 120_000
MIN_SUGGESTIONS = 5
MAX_SUGGESTIONS = 15
LONG_GAP_MS = 1500
START_GAP_MS = 500
END_GAP_MS = 700
SENTENCE_ENDINGS = (".", "!", "?")
HOOK_HEAD_CHARS = 150
HOOK_MIN_SCORE = 0.30
HOOK_BONUS_SCALE = 1.5
HOOK_IMPACT_WORDS = (
    "increible",
    "sorprendente",
    "nunca",
    "siempre",
    "todos",
    "nadie",
    "secreto",
    "verdad",
    "descubre",
)
HOOK_IMPERATIVE_STARTS = (
    "imagina",
    "piensa",
    "considera",
    "mira",
    "escucha",
    "recuerda",
)
HOOK_CONTRAST_WORDS = ("pero", "sin embargo", "aunque", "a pesar de")
SEMANTIC_BREAKPOINT_SIMILARITY = 0.5
SEMANTIC_DEDUPE_SIMILARITY = 0.86
SEMANTIC_DEDUPE_MAX = 200
SEMANTIC_TYPE_MAX = 200
SEMANTIC_TYPE_EXAMPLES = {
    "exposition": "En este pasaje, Pablo explica...",
    "illustration": "Hace unos anos conoci a...",
    "application": "Entonces, que significa esto para ti?",
    "conclusion": "En resumen, hemos visto que...",
}
SEMANTIC_TYPE_SCORES = {
    "application": 1.5,
    "illustration": 1.2,
    "conclusion": 1.0,
    "exposition": 0.7,
}
DEFAULT_TEMPLATE_CONFIG = {
    "font": "Arial",
    "font_size": 64,
    "y_pos": 1500,
    "max_words_per_line": 4,
    "highlight_mode": "none",
    "safe_margins": {"top": 120, "bottom": 120, "left": 120, "right": 120},
}
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_BATCH_SIZE = 64
HEURISTIC_SCORE_WEIGHT = 0.3
LLM_SCORE_WEIGHT = 0.7
LLM_MAX_CANDIDATES = 15
LLM_TIMEOUT_SEC = 60.0
LLM_TRIM_CONFIDENCE_MIN = 0.8
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
RETRYABLE_EXCEPTIONS = (
    BotoCoreError,
    ClientError,
    ConnectionError,
    OSError,
    OperationalError,
    subprocess.CalledProcessError,
    TimeoutError,
)

_embedding_model = None


def _calculate_retry_delay(retries: int) -> int:
    base = max(1, settings.celery_retry_backoff_base)
    max_delay = max(base, settings.celery_retry_backoff_max)
    delay = min(max_delay, base * (2**retries))
    jitter = max(0, settings.celery_retry_jitter)
    if jitter:
        delay += random.uniform(0, jitter)
    return int(delay)


def _maybe_retry(task, exc: Exception, *, label: str) -> None:
    if not isinstance(exc, RETRYABLE_EXCEPTIONS):
        return
    max_retries = task.max_retries
    retries = task.request.retries
    if max_retries is not None and retries >= max_retries:
        return
    delay = _calculate_retry_delay(retries)
    logger.warning(
        "%s failed; retrying in %ss (attempt %s/%s)",
        label,
        delay,
        retries + 1,
        max_retries,
    )
    raise task.retry(exc=exc, countdown=delay)


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


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return stripped.lower()


def _is_hook_advanced(text: str) -> tuple[bool, float]:
    head = text.strip()[:HOOK_HEAD_CHARS]
    if not head:
        return False, 0.0
    normalized = _normalize_text(head)
    score = 0.0

    if "?" in head or re.search(r"\b(que|como|por\s+que|porque)\b", normalized):
        score += 0.35
    if re.search(r"\d+%|\d+\s+de\s+cada\s+\d+", normalized):
        score += 0.25
    if any(word in normalized for word in HOOK_IMPACT_WORDS):
        score += 0.20
    if normalized.startswith(HOOK_IMPERATIVE_STARTS):
        score += 0.15
    if any(word in normalized for word in HOOK_CONTRAST_WORDS):
        score += 0.10
    if "!" in head and len(head.split("!")[0].strip()) > 10:
        score += 0.15
    if _count_words(head) <= 8:
        score += 0.10

    score = min(1.0, score)
    return score >= HOOK_MIN_SCORE, score


def _ends_sentence(text: str) -> bool:
    stripped = text.rstrip()
    if not stripped:
        return False
    if stripped.endswith("..."):
        return True
    return stripped[-1] in SENTENCE_ENDINGS


def _starts_sentence(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped:
        return False
    first = stripped[0]
    return first.isupper() or first.isdigit()


def _is_clean_start(prev_gap_ms: int | None, text: str) -> bool:
    if prev_gap_ms is None:
        return True
    if prev_gap_ms >= START_GAP_MS:
        return True
    return _starts_sentence(text)


def _is_clean_end(next_gap_ms: int | None, text: str) -> bool:
    if _ends_sentence(text):
        return True
    if next_gap_ms is None:
        return True
    return next_gap_ms >= END_GAP_MS


def _score_candidate(
    text: str, gap_ms: int, start_clean: bool, end_clean: bool
) -> tuple[float, str, float]:
    word_count = _count_words(text)
    text_penalty = 2.0 if word_count < 8 else 1.0 if word_count < 15 else 0.0
    gap_penalty = min(2.0, gap_ms / 3000.0)
    _, hook_score = _is_hook_advanced(text)
    hook_bonus = HOOK_BONUS_SCALE * hook_score
    start_bonus = 0.3 if start_clean else -0.3
    end_bonus = 0.6 if end_clean else -0.6
    score = (
        (word_count / 10.0)
        + hook_bonus
        + start_bonus
        + end_bonus
        - text_penalty
        - gap_penalty
    )
    rationale = (
        "words={words}; gaps_ms={gaps}; hook={hook:.2f}; start={start}; end={end}".format(
            words=word_count,
            gaps=gap_ms,
            hook=hook_score,
            start="clean" if start_clean else "rough",
            end="clean" if end_clean else "rough",
        )
    )
    return score, rationale, hook_score


def _cosine_similarity(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    vec_a = np.asarray(a, dtype=np.float32)
    vec_b = np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    if denom <= 1e-8:
        return 0.0
    return float(np.dot(vec_a, vec_b) / denom)


_segment_type_embeddings: dict[str, np.ndarray] | None = None


def _get_segment_type_embeddings() -> dict[str, np.ndarray]:
    global _segment_type_embeddings
    if _segment_type_embeddings is None:
        model = _get_embedding_model()
        examples = list(SEMANTIC_TYPE_EXAMPLES.values())
        embeddings = model.encode(examples, normalize_embeddings=False)
        _segment_type_embeddings = {
            seg_type: np.asarray(embedding, dtype=np.float32)
            for seg_type, embedding in zip(SEMANTIC_TYPE_EXAMPLES.keys(), embeddings)
        }
    return _segment_type_embeddings


def _classify_segment_type(embedding: np.ndarray) -> tuple[str, float]:
    best_type = "exposition"
    best_sim = -1.0
    for seg_type, example_emb in _get_segment_type_embeddings().items():
        similarity = _cosine_similarity(embedding, example_emb)
        if similarity > best_sim:
            best_sim = similarity
            best_type = seg_type
    return best_type, best_sim


def _score_by_type(segment_type: str) -> float:
    return SEMANTIC_TYPE_SCORES.get(segment_type, 1.0)


def _overlap_ratio(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    overlap = max(0, min(a_end, b_end) - max(a_start, b_start))
    if overlap <= 0:
        return 0.0
    a_len = a_end - a_start
    b_len = b_end - b_start
    if a_len <= 0 or b_len <= 0:
        return 0.0
    return overlap / min(a_len, b_len)


def _attach_embeddings(
    session, segments: list[TranscriptSegment]
) -> bool:
    if not segments:
        return False
    segment_ids = [segment.id for segment in segments]
    rows = session.execute(
        select(TranscriptEmbedding.segment_id, TranscriptEmbedding.embedding).where(
            TranscriptEmbedding.segment_id.in_(segment_ids),
            TranscriptEmbedding.deleted_at.is_(None),
        )
    ).all()
    mapping = {row.segment_id: row.embedding for row in rows}
    for segment in segments:
        embedding = mapping.get(segment.id)
        if embedding is not None:
            segment.embedding = embedding
    return len(mapping) == len(segments)


def _build_embedding_prefix(
    segments: list[TranscriptSegment],
) -> np.ndarray | None:
    if not segments:
        return None
    embeddings: list[np.ndarray] = []
    for segment in segments:
        embedding = getattr(segment, "embedding", None)
        if embedding is None:
            return None
        embeddings.append(np.asarray(embedding, dtype=np.float32))
    matrix = np.vstack(embeddings)
    prefix = np.zeros((matrix.shape[0] + 1, matrix.shape[1]), dtype=np.float32)
    prefix[1:] = np.cumsum(matrix, axis=0)
    return prefix


def _candidate_embedding(
    prefix: np.ndarray | None, start_idx: int, end_idx: int
) -> np.ndarray | None:
    if prefix is None:
        return None
    if start_idx < 0 or end_idx + 1 >= prefix.shape[0]:
        return None
    count = end_idx - start_idx + 1
    if count <= 0:
        return None
    return (prefix[end_idx + 1] - prefix[start_idx]) / float(count)


def _find_breakpoints(segments: list[TranscriptSegment]) -> list[int]:
    if not segments:
        return [0]
    breakpoints = [0]
    for i in range(1, len(segments)):
        prev = segments[i - 1]
        curr = segments[i]
        gap = curr.start_ms - prev.end_ms
        if gap > LONG_GAP_MS:
            breakpoints.append(i)
            continue
        prev_emb = getattr(prev, "embedding", None)
        curr_emb = getattr(curr, "embedding", None)
        if prev_emb is not None and curr_emb is not None:
            similarity = _cosine_similarity(prev_emb, curr_emb)
            if similarity < SEMANTIC_BREAKPOINT_SIMILARITY:
                breakpoints.append(i)
    breakpoints.append(len(segments))
    cleaned: list[int] = []
    last = None
    for idx in breakpoints:
        if idx != last:
            cleaned.append(idx)
            last = idx
    return cleaned


def _apply_semantic_scoring(
    candidates: list[dict], embedding_prefix: np.ndarray | None
) -> None:
    if not candidates or embedding_prefix is None:
        return
    for candidate in candidates:
        start_idx = candidate.get("start_idx")
        end_idx = candidate.get("end_idx")
        if start_idx is None or end_idx is None:
            continue
        embedding = _candidate_embedding(embedding_prefix, start_idx, end_idx)
        if embedding is None:
            continue
        candidate["embedding"] = embedding
        segment_type, similarity = _classify_segment_type(embedding)
        type_score = _score_by_type(segment_type)
        candidate["segment_type"] = segment_type
        candidate["type_score"] = type_score
        candidate["type_similarity"] = similarity
        candidate["heuristic_score"] *= type_score
        candidate["heuristic_rationale"] += f"; type={segment_type}"


def _semantic_dedupe_candidates(candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []
    selected: list[dict] = []
    selected_embeddings: list[np.ndarray] = []
    for index, candidate in enumerate(candidates):
        if index >= SEMANTIC_DEDUPE_MAX:
            selected.extend(candidates[index:])
            break
        embedding = candidate.get("embedding")
        if embedding is None:
            selected.append(candidate)
            continue
        is_duplicate = False
        for chosen_emb in selected_embeddings:
            if _cosine_similarity(embedding, chosen_emb) >= SEMANTIC_DEDUPE_SIMILARITY:
                is_duplicate = True
                break
        if not is_duplicate:
            selected.append(candidate)
            selected_embeddings.append(embedding)
    return selected


def _build_candidates(
    segments: list[TranscriptSegment],
    *,
    strict_end: bool = True,
    breakpoints: list[int] | None = None,
) -> list[dict]:
    candidates: list[dict] = []
    total_segments = len(segments)
    if not breakpoints:
        breakpoints = [0, total_segments]
    for window_start, window_end in zip(breakpoints, breakpoints[1:]):
        if window_start >= window_end:
            continue
        for start_idx in range(window_start, window_end):
            start_segment = segments[start_idx]
            start_ms = start_segment.start_ms
            prev_gap_ms = None
            if start_idx > 0:
                prev_gap_ms = max(0, start_ms - segments[start_idx - 1].end_ms)
            start_clean = _is_clean_start(prev_gap_ms, start_segment.text)
            text_parts: list[str] = []
            gap_ms = 0
            prev_end = start_segment.end_ms
            for end_idx in range(start_idx, window_end):
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
                next_gap_ms = None
                if end_idx + 1 < total_segments:
                    next_gap_ms = max(
                        0, segments[end_idx + 1].start_ms - segment.end_ms
                    )
                end_clean = _is_clean_end(next_gap_ms, segment.text)
                if strict_end and not end_clean:
                    continue
                score, rationale, hook_score = _score_candidate(
                    text, gap_ms, start_clean=start_clean, end_clean=end_clean
                )
                candidates.append(
                    {
                        "start_ms": start_ms,
                        "end_ms": end_ms,
                        "start_idx": start_idx,
                        "end_idx": end_idx,
                        "heuristic_score": score,
                        "heuristic_rationale": rationale,
                        "text": text,
                        "hook_score": hook_score,
                        "gap_ms": gap_ms,
                        "start_clean": start_clean,
                        "end_clean": end_clean,
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


def _scale_heuristic_scores(candidates: list[dict]) -> None:
    if not candidates:
        return
    values = [candidate["heuristic_score"] for candidate in candidates]
    min_score = min(values)
    max_score = max(values)
    if abs(max_score - min_score) < 1e-6:
        for candidate in candidates:
            candidate["heuristic_scaled"] = 50.0
        return
    for candidate in candidates:
        candidate["heuristic_scaled"] = (
            (candidate["heuristic_score"] - min_score) / (max_score - min_score) * 100.0
        )


def _score_candidates_with_llm(candidates: list[dict]) -> None:
    llm_payload = []
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = f"c{index}"
        duration_sec = max(
            1, int(round((candidate["end_ms"] - candidate["start_ms"]) / 1000.0))
        )
        candidate["candidate_id"] = candidate_id
        candidate["approx_duration_sec"] = duration_sec
        llm_payload.append(
            {
                "id": candidate_id,
                "text": candidate["text"],
                "approx_duration_sec": duration_sec,
            }
        )

    results = score_clip_candidates(
        llm_payload,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=LLM_TIMEOUT_SEC,
    )
    result_map = {item["id"]: item for item in results}

    if len(result_map) != len(llm_payload):
        raise DeepseekClientError("Deepseek returned incomplete scores")

    for candidate in candidates:
        scored = result_map.get(candidate["candidate_id"])
        candidate["llm_score"] = scored["score"]
        candidate["llm_reason"] = scored.get("reason") or ""
        candidate["llm_trim"] = scored.get("trim_suggestion")
        candidate["llm_trim_confidence"] = scored.get("trim_confidence")


def _apply_trim_suggestions(
    candidates: list[dict], segments: list[TranscriptSegment]
) -> None:
    total_segments = len(segments)
    for candidate in candidates:
        trim = candidate.get("llm_trim")
        if not isinstance(trim, dict):
            continue
        trim_confidence = candidate.get("llm_trim_confidence")
        if trim_confidence is None:
            candidate["trim_applied"] = False
            continue
        try:
            trim_confidence_val = float(trim_confidence)
        except (TypeError, ValueError):
            candidate["trim_applied"] = False
            continue
        if trim_confidence_val < LLM_TRIM_CONFIDENCE_MIN:
            candidate["trim_applied"] = False
            continue
        start_offset = trim.get("start_offset_sec")
        end_offset = trim.get("end_offset_sec")
        try:
            start_offset_sec = max(0.0, float(start_offset or 0))
            end_offset_sec = abs(float(end_offset or 0))
        except (TypeError, ValueError):
            continue
        if start_offset_sec <= 0 and end_offset_sec <= 0:
            continue
        start_idx = candidate.get("start_idx")
        end_idx = candidate.get("end_idx")
        if start_idx is None or end_idx is None:
            continue
        if start_idx < 0 or end_idx >= total_segments or start_idx > end_idx:
            continue

        new_start_ms = candidate["start_ms"] + int(round(start_offset_sec * 1000))
        new_end_ms = candidate["end_ms"] - int(round(end_offset_sec * 1000))
        if new_end_ms <= new_start_ms:
            continue

        new_start_idx = None
        for idx in range(start_idx, end_idx + 1):
            if segments[idx].end_ms >= new_start_ms:
                new_start_idx = idx
                break
        if new_start_idx is None:
            continue

        new_end_idx = None
        for idx in range(end_idx, new_start_idx - 1, -1):
            if segments[idx].start_ms <= new_end_ms:
                new_end_idx = idx
                break
        if new_end_idx is None or new_end_idx < new_start_idx:
            continue

        adjusted_start_ms = segments[new_start_idx].start_ms
        adjusted_end_ms = segments[new_end_idx].end_ms
        duration_ms = adjusted_end_ms - adjusted_start_ms
        if duration_ms < MIN_CLIP_MS or duration_ms > MAX_CLIP_MS:
            continue

        candidate["start_ms"] = adjusted_start_ms
        candidate["end_ms"] = adjusted_end_ms
        candidate["start_idx"] = new_start_idx
        candidate["end_idx"] = new_end_idx
        candidate["trim_applied"] = True


def _resolve_template_config(session, clip: Clip) -> dict:
    if clip.template_id:
        template = session.get(Template, clip.template_id)
        if template and template.deleted_at is None and template.config_json:
            return template.config_json
        logger.warning("Template %s not found for clip %s", clip.template_id, clip.id)
    return DEFAULT_TEMPLATE_CONFIG


@celery_app.task(
    name="worker.transcribe_sermon",
    bind=True,
    max_retries=settings.celery_max_retries,
)
def transcribe_sermon(self, sermon_id: int) -> dict:
    session = SessionLocal()
    sermon = None
    try:
        sermon = session.get(Sermon, sermon_id)
        if not sermon:
            raise ValueError("Sermon not found")
        if sermon.deleted_at is not None:
            logger.info("Sermon %s is deleted; skipping transcription", sermon_id)
            return {"sermon_id": sermon_id, "status": "deleted"}
        if not sermon.source_url:
            raise ValueError("Sermon has no source_url")

        sermon.error_message = None
        sermon.status = SermonStatus.processing
        sermon.progress = 5
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

            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, info = model.transcribe(wav_path)
            total_duration = getattr(info, "duration", None)
            if total_duration is None and isinstance(info, dict):
                total_duration = info.get("duration")

            count = 0
            batch = []
            batch_size = 100
            last_progress = sermon.progress or 0
            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue
                batch.append(
                    TranscriptSegment(
                        sermon_id=sermon.id,
                        start_ms=int(segment.start * 1000),
                        end_ms=int(segment.end * 1000),
                        text=text,
                    )
                )
                count += 1
                if len(batch) >= batch_size:
                    session.bulk_save_objects(batch)
                    session.commit()
                    batch = []
                if total_duration:
                    progress = int(min(95, max(5, (segment.end / total_duration) * 90 + 5)))
                    if progress - last_progress >= 2:
                        sermon.progress = progress
                        session.commit()
                        last_progress = progress

            if batch:
                session.bulk_save_objects(batch)
                session.commit()

            session.commit()

        session.refresh(sermon)
        if sermon.deleted_at is not None:
            logger.info("Sermon %s deleted during transcription", sermon_id)
            return {"sermon_id": sermon_id, "status": "deleted"}
        sermon.status = SermonStatus.transcribed
        sermon.progress = 100
        sermon.error_message = None
        session.commit()
        return {"sermon_id": sermon.id, "segments": count}
    except Exception as exc:
        session.rollback()
        _maybe_retry(self, exc, label=f"Transcribe sermon {sermon_id}")
        if sermon is not None:
            sermon.status = SermonStatus.error
            sermon.error_message = str(exc)[:1000]
            session.commit()
        logger.exception("Failed to transcribe sermon %s", sermon_id)
        raise
    finally:
        session.close()


@celery_app.task(
    name="worker.suggest_clips",
    bind=True,
    max_retries=settings.celery_max_retries,
)
def suggest_clips(self, sermon_id: int, use_llm: bool | None = None) -> dict:
    session = SessionLocal()
    sermon = None
    try:
        sermon = session.get(Sermon, sermon_id)
        if not sermon:
            raise ValueError("Sermon not found")
        if sermon.deleted_at is not None:
            logger.info("Sermon %s is deleted; skipping suggestions", sermon_id)
            return {"sermon_id": sermon_id, "status": "deleted"}
        sermon.error_message = None
        session.commit()

        segments_query = (
            select(TranscriptSegment)
            .where(
                TranscriptSegment.sermon_id == sermon_id,
                TranscriptSegment.deleted_at.is_(None),
            )
            .order_by(TranscriptSegment.start_ms.asc())
        )
        segments = list(session.execute(segments_query).scalars().all())
        if not segments:
            raise ValueError("No transcript segments available")

        embeddings_ready = _attach_embeddings(session, segments)
        embedding_prefix = _build_embedding_prefix(segments) if embeddings_ready else None

        logger.info(
            "Suggesting clips for sermon %s using %s segments",
            sermon_id,
            len(segments),
        )

        breakpoints = _find_breakpoints(segments)
        candidates = _build_candidates(
            segments, strict_end=True, breakpoints=breakpoints
        )
        if not candidates:
            candidates = _build_candidates(
                segments, strict_end=False, breakpoints=breakpoints
            )
        if not candidates and breakpoints != [0, len(segments)]:
            candidates = _build_candidates(
                segments, strict_end=True, breakpoints=[0, len(segments)]
            )
            if not candidates:
                candidates = _build_candidates(
                    segments, strict_end=False, breakpoints=[0, len(segments)]
                )
        if not candidates:
            raise ValueError("No candidate clips generated")

        if embedding_prefix is not None and candidates:
            candidates.sort(key=lambda item: item["heuristic_score"], reverse=True)
            semantic_candidates = candidates[:SEMANTIC_TYPE_MAX]
            _apply_semantic_scoring(semantic_candidates, embedding_prefix)

        all_candidates = list(candidates)
        use_llm_effective = (
            settings.use_llm_for_clip_suggestions if use_llm is None else use_llm
        )
        llm_used = False

        if use_llm_effective:
            llm_candidates = sorted(
                all_candidates, key=lambda item: item["heuristic_score"], reverse=True
            )
            llm_candidates = llm_candidates[:LLM_MAX_CANDIDATES]
            try:
                _score_candidates_with_llm(llm_candidates)
                llm_used = True
                candidates = llm_candidates
            except DeepseekClientError as exc:
                logger.warning(
                    "Deepseek LLM unavailable, falling back to heuristics: %s", exc
                )
                candidates = all_candidates
        else:
            candidates = all_candidates

        if llm_used:
            _scale_heuristic_scores(candidates)
            _apply_trim_suggestions(candidates, segments)
            for candidate in candidates:
                candidate["score"] = (
                    HEURISTIC_SCORE_WEIGHT * candidate["heuristic_scaled"]
                    + LLM_SCORE_WEIGHT * candidate["llm_score"]
                )
                candidate["rationale"] = (
                    candidate["llm_reason"] or candidate["heuristic_rationale"]
                )
                candidate["use_llm"] = True
                candidate.setdefault("llm_trim", None)
                candidate.setdefault("llm_trim_confidence", None)
                candidate.setdefault("trim_applied", False)
        else:
            for candidate in candidates:
                candidate["score"] = candidate["heuristic_score"]
                candidate["rationale"] = candidate["heuristic_rationale"]
                candidate["use_llm"] = False
                candidate["llm_trim"] = None
                candidate["llm_trim_confidence"] = None
                candidate["trim_applied"] = False

        candidates.sort(key=lambda item: item["score"], reverse=True)
        candidates = _dedupe_candidates(candidates)
        candidates.sort(key=lambda item: item["score"], reverse=True)
        candidates = _semantic_dedupe_candidates(candidates)
        candidates = candidates[:MAX_SUGGESTIONS]

        logger.info(
            "Generated %s candidate clips after dedupe for sermon %s",
            len(candidates),
            sermon_id,
        )

        now = datetime.utcnow()
        session.execute(
            update(Clip)
            .where(
                Clip.sermon_id == sermon_id,
                Clip.source == ClipSource.auto,
                Clip.deleted_at.is_(None),
            )
            .values(deleted_at=now, updated_at=now)
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
                    use_llm=candidate["use_llm"],
                    llm_trim=candidate.get("llm_trim"),
                    llm_trim_confidence=candidate.get("llm_trim_confidence"),
                    trim_applied=bool(candidate.get("trim_applied")),
                    status=ClipStatus.pending,
                )
            )
            created += 1

        session.commit()

        session.refresh(sermon)
        if sermon.deleted_at is not None:
            logger.info("Sermon %s deleted during suggestions", sermon_id)
            return {"sermon_id": sermon_id, "status": "deleted"}
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
        _maybe_retry(self, exc, label=f"Suggest clips for sermon {sermon_id}")
        if sermon is not None:
            sermon.status = SermonStatus.error
            sermon.error_message = str(exc)[:1000]
            session.commit()
        logger.exception("Failed to suggest clips for sermon %s", sermon_id)
        raise
    finally:
        session.close()


@celery_app.task(
    name="worker.generate_embeddings",
    bind=True,
    max_retries=settings.celery_max_retries,
)
def generate_embeddings(self, sermon_id: int) -> dict:
    session = SessionLocal()
    sermon = None
    try:
        sermon = session.get(Sermon, sermon_id)
        if not sermon:
            raise ValueError("Sermon not found")
        if sermon.deleted_at is not None:
            logger.info("Sermon %s is deleted; skipping embeddings", sermon_id)
            return {"sermon_id": sermon_id, "status": "deleted"}
        sermon.error_message = None
        session.commit()

        segments = list(
            session.execute(
                select(TranscriptSegment)
                .where(
                    TranscriptSegment.sermon_id == sermon_id,
                    TranscriptSegment.deleted_at.is_(None),
                )
                .order_by(TranscriptSegment.start_ms.asc())
            ).scalars()
        )
        if not segments:
            raise ValueError("No transcript segments available")

        now = datetime.utcnow()
        session.execute(
            update(TranscriptEmbedding)
            .where(
                TranscriptEmbedding.sermon_id == sermon_id,
                TranscriptEmbedding.deleted_at.is_(None),
            )
            .values(deleted_at=now, updated_at=now)
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

        session.refresh(sermon)
        if sermon.deleted_at is not None:
            logger.info("Sermon %s deleted during embeddings", sermon_id)
            return {"sermon_id": sermon_id, "status": "deleted"}
        sermon.status = SermonStatus.embedded
        sermon.error_message = None
        session.commit()
        logger.info("Embedding complete for sermon %s", sermon_id)
        return {"sermon_id": sermon_id, "segments": total}
    except Exception as exc:
        session.rollback()
        _maybe_retry(self, exc, label=f"Generate embeddings for sermon {sermon_id}")
        if sermon is not None:
            sermon.status = SermonStatus.error
            sermon.error_message = str(exc)[:1000]
            session.commit()
        logger.exception("Failed to generate embeddings for sermon %s", sermon_id)
        raise
    finally:
        session.close()


@celery_app.task(
    name="worker.render_clip",
    bind=True,
    max_retries=settings.celery_max_retries,
)
def render_clip(self, clip_id: int) -> dict:
    session = SessionLocal()
    clip = None
    try:
        clip = session.get(Clip, clip_id)
        if not clip or clip.deleted_at is not None:
            raise ValueError("Clip not found")

        sermon = session.get(Sermon, clip.sermon_id)
        if not sermon or sermon.deleted_at is not None or not sermon.source_url:
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
            .where(TranscriptSegment.deleted_at.is_(None))
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
        _maybe_retry(self, exc, label=f"Render clip {clip_id}")
        if clip is not None:
            clip.status = ClipStatus.error
            session.commit()
        logger.exception("Failed to render clip %s", clip_id)
        raise
    finally:
        session.close()
