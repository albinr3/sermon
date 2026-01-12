import os
import random
import re
import string
import subprocess
import tempfile
import time
import unicodedata
from datetime import datetime
from uuid import uuid4

from celery.utils.log import get_task_logger
from botocore.exceptions import BotoCoreError, ClientError
from faster_whisper import WhisperModel
import assemblyai as aai
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import OperationalError

from src.ass import build_ass_from_segments
from src.celery_app import celery_app
from src.config import settings
from src.db import SessionLocal
from src.models import (
    Clip,
    ClipRenderType,
    ClipSource,
    ClipStatus,
    Sermon,
    SermonStatus,
    Template,
    TranscriptEmbedding,
    TranscriptSegment,
    TranscriptUtterance,
)
from src.services.deepseek_client import (
    DeepseekClientError,
    generate_from_full_transcript as deepseek_generate_from_full_transcript,
    score_clip_candidates as deepseek_score_clip_candidates,
    select_best_clips as deepseek_select_best_clips,
    generate_clip_suggestions as deepseek_generate_clip_suggestions,
)
from src.services.openai_client import (
    OpenAIClientError,
    generate_from_full_transcript as openai_generate_from_full_transcript,
    score_clip_candidates as openai_score_clip_candidates,
    select_best_clips as openai_select_best_clips,
    generate_clip_suggestions as openai_generate_clip_suggestions,
)
from src.services.llm_prompts import (
    full_context_system_prompt,
    full_context_system_prompt_v2,
    full_context_system_prompt_v3,
    full_context_user_prompt,
)
from src.storage import download_object, upload_object, create_presigned_get_url

logger = get_task_logger(__name__)

IA_LOG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "logIA")
)

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
LLM_SELECTION_CANDIDATES = 50
GENERATION_WINDOW_DURATIONS_MS = (45_000, 60_000, 75_000, 90_000, 120_000)
LLM_TIMEOUT_SEC = 60.0
LLM_TRIM_CONFIDENCE_MIN = 0.8
PREVIEW_WARMUP_COUNT = 1
PREVIEW_SETTINGS = {
    "width": 360,
    "height": 640,
    "video_bitrate": "400k",
    "audio_bitrate": "64k",
    "maxrate": "500k",
    "bufsize": "1000k",
    "preset": "ultrafast",
    "crf": "28",
}
FINAL_SETTINGS = {
    "width": 1080,
    "height": 1920,
    "video_bitrate": "3500k",
    "audio_bitrate": "128k",
    "maxrate": "4000k",
    "bufsize": "8000k",
    "preset": "medium",
    "crf": "23",
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


def _normalize_text_for_search(text: str) -> str:
    """Normaliza texto para búsqueda flexible: minúsculas, sin puntuación simple."""
    normalized = _normalize_text(text)
    # Remover puntuación simple (.,!?;:)
    punctuation = string.punctuation.replace("'", "").replace("-", "")
    for char in punctuation:
        normalized = normalized.replace(char, " ")
    # Normalizar espacios múltiples
    normalized = " ".join(normalized.split())
    return normalized


def _find_timestamps_by_quote(
    segments: list[TranscriptSegment], quote_start: str, quote_end: str
) -> tuple[int | None, int | None]:
    """Busca timestamps usando quotes exactos del texto.
    
    Normaliza el texto (minúsculas, ignorar puntuación simple) para búsqueda flexible.
    Devuelve (start_ms, end_ms) o (None, None) si no encuentra alguno.
    """
    if not segments or not quote_start or not quote_end:
        return None, None
    
    # Normalizar quotes para búsqueda
    normalized_quote_start = _normalize_text_for_search(quote_start)
    normalized_quote_end = _normalize_text_for_search(quote_end)
    
    if not normalized_quote_start or not normalized_quote_end:
        return None, None
    
    # Buscar quote_start
    start_ms = None
    for segment in segments:
        normalized_segment_text = _normalize_text_for_search(segment.text)
        if normalized_quote_start in normalized_segment_text:
            start_ms = segment.start_ms
            break
    
    if start_ms is None:
        return None, None
    
    # Buscar quote_end después del inicio encontrado
    end_ms = None
    found_start = False
    for segment in segments:
        if segment.start_ms >= start_ms:
            found_start = True
        if found_start:
            normalized_segment_text = _normalize_text_for_search(segment.text)
            if normalized_quote_end in normalized_segment_text:
                end_ms = segment.end_ms
                break
    
    if end_ms is None or end_ms <= start_ms:
        return None, None
    
    return start_ms, end_ms


def _ensure_utterances(
    session, sermon_id: int, segments: list[TranscriptSegment], force_regenerate: bool = False
) -> list[TranscriptUtterance]:
    """Asegura que existan utterances para el sermon.
    
    Si ya existen y force_regenerate=False, las carga y devuelve ordenadas por idx.
    Si no existen o force_regenerate=True, las genera desde segments y las guarda.
    """
    # Verificar si ya existen utterances
    existing = list(
        session.execute(
            select(TranscriptUtterance)
            .where(
                TranscriptUtterance.sermon_id == sermon_id,
                TranscriptUtterance.deleted_at.is_(None),
            )
            .order_by(TranscriptUtterance.idx.asc())
        ).scalars().all()
    )
    
    if existing and not force_regenerate:
        logger.info("Found %d existing utterances for sermon %s", len(existing), sermon_id)
        return existing
    
    # Si force_regenerate=True, borrar utterances existentes (soft delete)
    if existing and force_regenerate:
        from datetime import datetime
        now = datetime.utcnow()
        session.execute(
            update(TranscriptUtterance)
            .where(
                TranscriptUtterance.sermon_id == sermon_id,
                TranscriptUtterance.deleted_at.is_(None),
            )
            .values(deleted_at=now, updated_at=now)
        )
        session.commit()
        logger.info("Force regenerating utterances for sermon %s (deleted %d existing)", sermon_id, len(existing))
    
    # Generar utterances desde segments
    logger.info("Generating utterances for sermon %s from %d segments", sermon_id, len(segments))
    utterances = []
    global_idx = 1
    
    for segment in segments:
        if not segment.text or segment.text.strip() == "":
            continue
        
        text = segment.text.strip()
        segment_duration = segment.end_ms - segment.start_ms
        
        if segment_duration <= 0:
            continue
        
        # Dividir en oraciones preservando puntuación
        # Patrón: captura texto hasta puntuación (incluyendo la puntuación) o texto sin puntuación al final
        sentences = re.findall(r"[^.!?]+[.!?]+|[^.!?]+$", text)
        if not sentences:
            # Fallback: si no hay matches, usar el texto completo como una oración
            sentences = [text]
        
        # Filtrar oraciones vacías
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            continue
        
        # Usar word timestamps si están disponibles (v3: timestamps exactos)
        # Si no, usar cálculo proporcional (fallback para v1 o faster-whisper)
        use_word_timestamps = segment.word_timestamps_json is not None and len(segment.word_timestamps_json) > 0
        
        if use_word_timestamps:
            # Calcular timestamps usando word timestamps exactos
            words = segment.word_timestamps_json
            current_start = segment.start_ms
            
            for i, sentence in enumerate(sentences):
                if not sentence:
                    continue
                
                is_last_sentence = (i == len(sentences) - 1)
                
                # Normalizar sentence para búsqueda (sin puntuación, minúsculas)
                sentence_normalized = _normalize_text_for_search(sentence)
                sentence_words = [w for w in sentence_normalized.split() if w]  # Filtrar palabras vacías
                
                if not sentence_words:
                    continue
                
                # Buscar las palabras de la sentence en los word timestamps
                sentence_start_ms = None
                sentence_end_ms = None
                word_idx = 0
                matched_words = []
                
                for word_data in words:
                    word_text = word_data.get("text", "").strip()
                    if not word_text:
                        continue
                    word_text_normalized = _normalize_text_for_search(word_text)
                    
                    # Buscar coincidencia con la primera palabra de la sentence
                    if word_idx == 0 and sentence_words and word_text_normalized == sentence_words[0]:
                        sentence_start_ms = word_data.get("start_ms")
                        matched_words.append(word_data)
                        word_idx = 1
                    elif word_idx > 0 and word_idx < len(sentence_words):
                        # Continuar buscando palabras de la sentence
                        if word_text_normalized == sentence_words[word_idx]:
                            matched_words.append(word_data)
                            word_idx += 1
                    
                    # Si encontramos todas las palabras, usar el end_ms de la última palabra
                    if word_idx >= len(sentence_words):
                        sentence_end_ms = matched_words[-1].get("end_ms") if matched_words else word_data.get("end_ms")
                        break
                
                # Si no encontramos timestamps exactos, usar fallback proporcional
                if sentence_start_ms is None or sentence_end_ms is None:
                    # Fallback a cálculo proporcional
                    total_chars = sum(len(s) for s in sentences)
                    if total_chars == 0:
                        continue
                    sentence_chars = len(sentence)
                    sentence_duration = int((sentence_chars / total_chars) * segment_duration)
                    sentence_duration = max(100, sentence_duration)
                    sentence_start_ms = current_start
                    sentence_end_ms = min(current_start + sentence_duration, segment.end_ms)
                
                # Asegurar que estén dentro del segmento
                sentence_start_ms = max(segment.start_ms, sentence_start_ms)
                sentence_end_ms = min(segment.end_ms, sentence_end_ms)
                
                # Si es la última oración, forzar end_ms = segment.end_ms
                if is_last_sentence:
                    sentence_end_ms = segment.end_ms
                
                # Validación final
                if sentence_end_ms <= sentence_start_ms:
                    continue
                
                utterance = TranscriptUtterance(
                    sermon_id=sermon_id,
                    idx=global_idx,
                    start_ms=sentence_start_ms,
                    end_ms=sentence_end_ms,
                    text=sentence,
                )
                utterances.append(utterance)
                global_idx += 1
                current_start = sentence_end_ms
                
                if is_last_sentence:
                    break
        else:
            # Método original: cálculo proporcional (para v1 o faster-whisper)
            total_chars = sum(len(s) for s in sentences)
            if total_chars == 0:
                continue
            
            current_start = segment.start_ms
            for i, sentence in enumerate(sentences):
                if not sentence:
                    continue
                
                # Si es la última oración del segmento, forzar end_ms = segment.end_ms
                is_last_sentence = (i == len(sentences) - 1)
                
                if is_last_sentence:
                    # Última utterance: termina exactamente en segment.end_ms
                    sentence_start = max(current_start, segment.start_ms)
                    sentence_end = segment.end_ms
                else:
                    # Calcular duración proporcional
                    sentence_chars = len(sentence)
                    sentence_duration = int((sentence_chars / total_chars) * segment_duration)
                    
                    # Asegurar mínimo de 100ms por utterance
                    sentence_duration = max(100, sentence_duration)
                    
                    sentence_end = min(current_start + sentence_duration, segment.end_ms)
                    
                    # Asegurar end_ms > start_ms
                    if sentence_end <= current_start:
                        sentence_end = current_start + 100
                    
                    # Clamp dentro del segmento
                    sentence_start = max(current_start, segment.start_ms)
                    sentence_end = min(sentence_end, segment.end_ms)
                
                # Validación final: asegurar end_ms > start_ms
                if sentence_end <= sentence_start:
                    continue
                
                utterance = TranscriptUtterance(
                    sermon_id=sermon_id,
                    idx=global_idx,
                    start_ms=sentence_start,
                    end_ms=sentence_end,
                    text=sentence,
                )
                utterances.append(utterance)
                global_idx += 1
                current_start = sentence_end
                
                # Si es la última oración, ya terminamos
                if is_last_sentence:
                    break
    
    if not utterances:
        logger.warning("No utterances generated for sermon %s", sermon_id)
        return []
    
    # Guardar en batch
    session.bulk_save_objects(utterances)
    session.commit()
    
    logger.info("Generated and saved %d utterances for sermon %s", len(utterances), sermon_id)
    return utterances


def _build_text_for_utterance_range(
    utterances: list[TranscriptUtterance], start_u: int, end_u: int
) -> str:
    """Construye texto concatenando utterances desde start_u hasta end_u (inclusive)."""
    if not utterances:
        return ""
    
    # start_u y end_u son índices 1-based (idx en DB)
    parts = []
    for utterance in utterances:
        if utterance.idx >= start_u and utterance.idx <= end_u:
            text = (utterance.text or "").strip()
            if text:
                parts.append(text)
    
    return " ".join(parts).strip()


def _looks_like_needs_context(text: str) -> bool:
    """Detecta si el texto empieza con frases que requieren contexto previo.
    
    Retorna True si el texto normalizado empieza con conectores o referencias
    que indican que necesita contexto anterior.
    """
    if not text:
        return False
    
    normalized = text.strip().lower()
    if not normalized:
        return False
    
    # Patrones de conectores que requieren contexto
    context_patterns = [
        r"^(pero|entonces|y|porque|o sea|asi que|así que|como te dije|como te decía|como dije|recuerda que|mira|ahora|bueno)\b",
        r"^(eso|esto|esa|ese|aqui|ahí|alli|allí)\b",
    ]
    
    for pattern in context_patterns:
        if re.match(pattern, normalized):
            return True
    
    return False


def _looks_like_clean_end(text: str) -> bool:
    """Detecta si el texto termina de forma limpia (conclusión completa).
    
    Retorna True si termina con puntuación de cierre (., !, ?, ...).
    Retorna False si termina con conectores que indican continuación.
    """
    if not text:
        return False
    
    stripped = text.strip()
    if not stripped:
        return False
    
    # Verificar si termina con conectores que indican continuación
    continuation_pattern = re.compile(r"\b(y|pero|porque|entonces|asi que|así que|o sea)$", re.IGNORECASE)
    if continuation_pattern.search(stripped):
        return False
    
    # Verificar si termina con puntuación de cierre
    if stripped.endswith(('.', '!', '?', '...')):
        return True
    
    return False


def _looks_like_incomplete_end(text: str) -> bool:
    """Detecta si el texto termina de forma incompleta (requiere extensión).
    
    Retorna True si:
    - Termina con conectores que indican continuación
    - NO termina con puntuación de cierre (., !, ?, ...)
    """
    if not text:
        return True
    
    normalized = text.strip().lower()
    if not normalized:
        return True
    
    # Verificar si termina con conectores que indican continuación
    continuation_pattern = re.compile(r"\b(y|pero|porque|entonces|asi que|así que|o sea|para que|cuando|si)\s*$")
    if continuation_pattern.search(normalized):
        return True
    
    # Verificar si NO termina con puntuación de cierre
    if not normalized.endswith(('.', '!', '?', '...')):
        return True
    
    return False


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


def _score_candidates_with_llm(
    candidates: list[dict], *, llm_provider: str = "deepseek"
) -> dict | None:
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

    if llm_provider == "openai":
        api_key = settings.openai_api_key
        base_url = settings.openai_base_url
        model = settings.openai_model
        score_fn = openai_score_clip_candidates
        error_class = OpenAIClientError
        provider_name = "OpenAI"
    else:
        api_key = settings.deepseek_api_key
        base_url = settings.deepseek_base_url
        model = settings.deepseek_model
        score_fn = deepseek_score_clip_candidates
        error_class = DeepseekClientError
        provider_name = "Deepseek"

    response = score_fn(
        llm_payload,
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout=LLM_TIMEOUT_SEC,
    )
    results = response.get("clips") or []
    token_usage = response.get("token_usage")
    result_map = {item["id"]: item for item in results}

    if len(result_map) != len(llm_payload):
        raise error_class(f"{provider_name} returned incomplete scores")

    for candidate in candidates:
        scored = result_map.get(candidate["candidate_id"])
        candidate["llm_score"] = scored["score"]
        candidate["llm_reason"] = scored.get("reason") or ""
        candidate["llm_trim"] = scored.get("trim_suggestion")
        candidate["llm_trim_confidence"] = scored.get("trim_confidence")
    return token_usage


def _select_candidates_with_llm(
    candidates: list[dict],
    sermon_context: str,
    *,
    target_count: int = 10,
    llm_provider: str = "deepseek",
) -> tuple[list[dict], dict | None]:
    llm_payload = []
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = f"c{index}"
        candidate["candidate_id"] = candidate_id
        llm_payload.append({"id": candidate_id, "text": candidate["text"]})

    if llm_provider == "openai":
        api_key = settings.openai_api_key
        base_url = settings.openai_base_url
        model = settings.openai_model
        select_fn = openai_select_best_clips
        error_class = OpenAIClientError
        provider_name = "OpenAI"
    else:
        api_key = settings.deepseek_api_key
        base_url = settings.deepseek_base_url
        model = settings.deepseek_model
        select_fn = deepseek_select_best_clips
        error_class = DeepseekClientError
        provider_name = "Deepseek"

    response = select_fn(
        llm_payload,
        sermon_context,
        api_key=api_key,
        base_url=base_url,
        model=model,
        target_count=target_count,
        timeout=LLM_TIMEOUT_SEC,
    )
    results = response.get("clips") or []
    token_usage = response.get("token_usage")
    result_map = {item["id"]: item for item in results}
    if not result_map:
        raise error_class(f"{provider_name} returned no selections")

    selected: list[dict] = []
    for candidate in candidates:
        scored = result_map.get(candidate["candidate_id"])
        if not scored:
            continue
        candidate["llm_score"] = scored.get("score")
        candidate["llm_reason"] = scored.get("reason") or ""
        selected.append(candidate)
    return selected, token_usage


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


def _build_text_for_range(
    segments: list[TranscriptSegment], start_ms: int, end_ms: int
) -> str:
    if not segments:
        return ""
    parts: list[str] = []
    for segment in segments:
        if segment.start_ms >= end_ms:
            break
        if segment.end_ms <= start_ms:
            continue
        text = (segment.text or "").strip()
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _create_sliding_windows(
    segments: list[TranscriptSegment],
    min_ms: int,
    max_ms: int,
    step_ms: int = 15_000,
) -> list[dict]:
    if not segments:
        return []
    durations = [ms for ms in GENERATION_WINDOW_DURATIONS_MS if min_ms <= ms <= max_ms]
    if not durations:
        return []
    first_start = segments[0].start_ms
    last_end = segments[-1].end_ms
    windows: list[dict] = []
    window_id = 1
    start_ms = first_start
    while start_ms + min_ms <= last_end:
        for duration in durations:
            end_ms = start_ms + duration
            if end_ms > last_end:
                continue
            text = _build_text_for_range(segments, start_ms, end_ms)
            if not text:
                continue
            windows.append(
                {
                    "id": f"w{window_id}",
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "text": text,
                }
            )
            window_id += 1
        start_ms += step_ms
    if len(windows) > 200:
        stride = max(1, len(windows) // 200)
        windows = windows[::stride][:200]
    return windows


def _adjust_to_segment_boundaries(
    segments: list[TranscriptSegment], start_ms: int, end_ms: int
) -> tuple[int, int]:
    if not segments:
        return start_ms, end_ms
    start_candidates = [segment.start_ms for segment in segments]
    end_candidates = [segment.end_ms for segment in segments]
    adjusted_start = min(start_candidates, key=lambda val: abs(val - start_ms))
    adjusted_end = min(end_candidates, key=lambda val: abs(val - end_ms))
    if adjusted_end <= adjusted_start:
        return start_ms, end_ms
    return adjusted_start, adjusted_end


def _adjust_to_segment_boundaries_v3(
    segments: list[TranscriptSegment], start_ms: int, end_ms: int
) -> tuple[int, int]:
    """Snapping asimétrico: ceil para start, floor para end.
    
    - start_ms -> primer segment.start_ms >= start propuesto (ceil)
    - end_ms -> último segment.end_ms <= end propuesto (floor)
    
    Esto evita que el clip empiece antes del hook o termine después.
    """
    if not segments:
        return start_ms, end_ms
    
    starts = [s.start_ms for s in segments]
    ends = [s.end_ms for s in segments]
    
    # Ceil: primer start >= start propuesto
    start_candidates = [v for v in starts if v >= start_ms]
    # Floor: último end <= end propuesto
    end_candidates = [v for v in ends if v <= end_ms]
    
    adjusted_start = min(start_candidates) if start_candidates else max(starts)
    adjusted_end = max(end_candidates) if end_candidates else min(ends)
    
    if adjusted_end <= adjusted_start:
        return start_ms, end_ms
    return adjusted_start, adjusted_end


def _backfill_candidates(
    selected: list[dict],
    pool: list[dict],
    target_count: int,
) -> list[dict]:
    if len(selected) >= target_count:
        return selected
    ordered_pool = sorted(
        pool,
        key=lambda item: item.get("score", item.get("heuristic_score", 0.0)),
        reverse=True,
    )
    for candidate in ordered_pool:
        if len(selected) >= target_count:
            break
        has_overlap = any(
            _overlap_ratio(
                candidate["start_ms"],
                candidate["end_ms"],
                chosen["start_ms"],
                chosen["end_ms"],
            )
            > 0.6
            for chosen in selected
        )
        if has_overlap:
            continue
        fallback = dict(candidate)
        fallback["score"] = fallback.get("score", fallback.get("heuristic_score", 0.0))
        fallback["rationale"] = fallback.get(
            "rationale", fallback.get("heuristic_rationale", "")
        )
        fallback["use_llm"] = False
        fallback["llm_method"] = None
        fallback["llm_trim"] = None
        fallback["llm_trim_confidence"] = None
        fallback["trim_applied"] = False
        selected.append(fallback)
    return selected


def _build_sermon_context(
    segments: list[TranscriptSegment], limit_chars: int = 2000
) -> str:
    if not segments:
        return ""
    parts: list[str] = []
    total = 0
    for segment in segments:
        text = (segment.text or "").strip()
        if not text:
            continue
        if total > 0:
            if total + 1 > limit_chars:
                break
            parts.append(" ")
            total += 1
        remaining = limit_chars - total
        if remaining <= 0:
            break
        if len(text) > remaining:
            parts.append(text[:remaining])
            total += remaining
            break
        parts.append(text)
        total += len(text)
        if total >= limit_chars:
            break
    return "".join(parts)


def _split_token_usage(token_usage: dict | None, count: int) -> dict | None:
    if not token_usage or count <= 0:
        return None
    prompt_tokens = token_usage.get("prompt_tokens")
    completion_tokens = token_usage.get("completion_tokens")
    output_tokens = token_usage.get("output_tokens", completion_tokens)
    cache_hit_tokens = token_usage.get("cache_hit_tokens")
    cache_miss_tokens = token_usage.get("cache_miss_tokens")
    total_tokens = token_usage.get("total_tokens")
    estimated_cost = token_usage.get("estimated_cost_usd")

    def _split_int(value):
        if value is None:
            return None
        try:
            return int(round(value / count))
        except (TypeError, ValueError):
            return None

    prompt_tokens_val = _split_int(prompt_tokens)
    completion_tokens_val = _split_int(completion_tokens)
    output_tokens_val = _split_int(output_tokens)
    cache_hit_tokens_val = _split_int(cache_hit_tokens)
    cache_miss_tokens_val = _split_int(cache_miss_tokens)
    total_tokens_val = _split_int(total_tokens)
    try:
        estimated_cost_val = float(estimated_cost or 0.0) / count
    except (TypeError, ValueError):
        estimated_cost_val = None
    return {
        "prompt_tokens": prompt_tokens_val,
        "completion_tokens": completion_tokens_val,
        "output_tokens": output_tokens_val,
        "cache_hit_tokens": cache_hit_tokens_val,
        "cache_miss_tokens": cache_miss_tokens_val,
        "total_tokens": total_tokens_val,
        "estimated_cost_usd": estimated_cost_val,
    }


def _merge_token_usage(base: dict | None, extra: dict | None) -> dict | None:
    if not base and not extra:
        return None
    if not base:
        return dict(extra)
    if not extra:
        return dict(base)

    def _merge_value(key: str) -> int | None:
        value_base = base.get(key)
        value_extra = extra.get(key)
        if value_base is None and value_extra is None:
            return None
        return int((value_base or 0) + (value_extra or 0))

    def _merge_float(key: str) -> float | None:
        value_base = base.get(key)
        value_extra = extra.get(key)
        if value_base is None and value_extra is None:
            return None
        return float((value_base or 0.0) + (value_extra or 0.0))

    return {
        "prompt_tokens": _merge_value("prompt_tokens"),
        "completion_tokens": _merge_value("completion_tokens"),
        "output_tokens": _merge_value("output_tokens"),
        "cache_hit_tokens": _merge_value("cache_hit_tokens"),
        "cache_miss_tokens": _merge_value("cache_miss_tokens"),
        "total_tokens": _merge_value("total_tokens"),
        "estimated_cost_usd": _merge_float("estimated_cost_usd"),
    }


def _backfill_with_selection(
    selected: list[dict],
    pool: list[dict],
    sermon_context: str,
    target_count: int,
    *,
    llm_provider: str = "deepseek",
) -> tuple[list[dict], dict | None]:
    if len(selected) >= target_count:
        return selected, None
    llm_candidates = sorted(
        pool,
        key=lambda item: item["heuristic_score"],
        reverse=True,
    )
    llm_candidates = llm_candidates[:LLM_SELECTION_CANDIDATES]
    try:
        candidates, token_usage = _select_candidates_with_llm(
            llm_candidates, sermon_context, target_count=target_count, llm_provider=llm_provider
        )
    except (DeepseekClientError, OpenAIClientError) as exc:
        logger.warning("Selection backfill failed: %s", exc)
        return selected, None
    if not candidates:
        return selected, token_usage
    candidates.sort(key=lambda item: item.get("llm_score", 0), reverse=True)
    for candidate in candidates:
        if len(selected) >= target_count:
            break
        has_overlap = any(
            _overlap_ratio(
                candidate["start_ms"],
                candidate["end_ms"],
                chosen["start_ms"],
                chosen["end_ms"],
            )
            > 0.6
            for chosen in selected
        )
        if has_overlap:
            continue
        llm_score = candidate.get("llm_score")
        candidate["score"] = (
            llm_score
            if isinstance(llm_score, (int, float))
            else candidate.get("heuristic_score", 0.0)
        )
        candidate["rationale"] = (
            candidate.get("llm_reason") or candidate.get("heuristic_rationale", "")
        )
        candidate["use_llm"] = True
        candidate["llm_method"] = "selection"
        candidate["llm_trim"] = None
        candidate["llm_trim_confidence"] = None
        candidate["trim_applied"] = False
        selected.append(candidate)
    return selected, token_usage


def _log_llm_usage(sermon_id: int, method: str, token_usage: dict | None) -> None:
    _append_ia_log(_format_ia_report(sermon_id, method, token_usage))
    logger.info("===================================")
    logger.info("SERMON %s - TOKEN USAGE REPORT", sermon_id)
    logger.info("Method: %s", method)
    if not token_usage:
        logger.info("Token usage: unavailable")
        logger.info("===================================")
        return
    total_tokens = token_usage.get("total_tokens", 0)
    prompt_tokens = token_usage.get("prompt_tokens", 0)
    output_tokens = token_usage.get(
        "output_tokens", token_usage.get("completion_tokens", 0)
    )
    cache_hit_tokens = token_usage.get("cache_hit_tokens")
    cache_miss_tokens = token_usage.get("cache_miss_tokens")
    try:
        tokens_display = f"{int(total_tokens):,}"
    except (TypeError, ValueError):
        tokens_display = "0"
    cost = token_usage.get("estimated_cost_usd", 0.0) or 0.0
    logger.info("Prompt tokens: %s", prompt_tokens)
    logger.info("Output tokens: %s", output_tokens)
    logger.info("Total tokens: %s", tokens_display)
    logger.info(
        "Cache hit tokens: %s",
        cache_hit_tokens if cache_hit_tokens is not None else "n/a",
    )
    logger.info(
        "Cache miss tokens: %s",
        cache_miss_tokens if cache_miss_tokens is not None else "n/a",
    )
    logger.info("Cost: $%.6f", cost)
    logger.info("===================================")


def _append_ia_log(message: str) -> None:
    try:
        with open(IA_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(message)
            if not message.endswith("\n"):
                handle.write("\n")
    except Exception:
        logger.exception("Failed to write IA log file")


def _format_ia_report(
    sermon_id: int, method: str, token_usage: dict | None
) -> str:
    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    lines = [
        "===================================",
        f"{timestamp} SERMON {sermon_id} - TOKEN USAGE REPORT",
        f"Method: {method}",
    ]
    if not token_usage:
        lines.append("Token usage: unavailable")
        lines.append("===================================")
        return "\n".join(lines) + "\n"
    total_tokens = token_usage.get("total_tokens", 0)
    prompt_tokens = token_usage.get("prompt_tokens", 0)
    output_tokens = token_usage.get(
        "output_tokens", token_usage.get("completion_tokens", 0)
    )
    cache_hit_tokens = token_usage.get("cache_hit_tokens")
    cache_miss_tokens = token_usage.get("cache_miss_tokens")
    cost = token_usage.get("estimated_cost_usd", 0.0) or 0.0
    lines.extend(
        [
            f"Prompt tokens: {prompt_tokens}",
            f"Output tokens: {output_tokens}",
            f"Total tokens: {total_tokens}",
            f"Cache hit tokens: {cache_hit_tokens if cache_hit_tokens is not None else 'n/a'}",
            f"Cache miss tokens: {cache_miss_tokens if cache_miss_tokens is not None else 'n/a'}",
            f"Cost: ${cost:.6f}",
            "===================================",
        ]
    )
    return "\n".join(lines) + "\n"


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

        transcription_model = (sermon.transcription_model or "faster_whisper").strip().lower()
        language = (sermon.language or "").strip().lower()
        
        # Log inicial con información del usuario
        logger.info("=" * 60)
        logger.info("USUARIO SUBIENDO VIDEO - Sermon ID: %s", sermon_id)
        logger.info("  Idioma seleccionado: %s", language.upper() if language else "No especificado")
        logger.info("  Modelo de transcripcion: %s", transcription_model.upper())
        logger.info("=" * 60)
        
        count = 0
        batch = []
        batch_size = 100
        last_progress = sermon.progress or 0
        total_duration = None

        with tempfile.TemporaryDirectory() as tmpdir:
            mp4_path = f"{tmpdir}/input.mp4"
            wav_path = f"{tmpdir}/audio.wav"

            download_object(sermon.source_url, mp4_path)

            # Obtener duración del video con ffprobe
            try:
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        mp4_path,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                video_duration = float(result.stdout.strip())
                sermon.video_duration_sec = video_duration
                session.commit()
                logger.info(
                    "Video duration for sermon %s: %.1fs",
                    sermon_id,
                    video_duration,
                )
                total_duration = video_duration
            except Exception as exc:
                logger.warning("Failed to get video duration: %s", exc)
                video_duration = None

            if transcription_model == "assemblyai":
                # Transcripcion con AssemblyAI
                if not settings.assemblyai_api_key:
                    raise ValueError("ASSEMBLYAI_API_KEY no esta configurada")
                
                transcription_start_time = time.time()
                
                aai.settings.api_key = settings.assemblyai_api_key
                transcriber = aai.Transcriber()
                
                # Configurar idioma si esta especificado
                config = aai.TranscriptionConfig()
                if language:
                    if language == "es":
                        config.language_code = aai.LanguageCode.es
                    elif language == "en":
                        config.language_code = aai.LanguageCode.en
                
                # Habilitar word timestamps para v3 (requerido para timestamps exactos)
                # Nota: word_level_timestamps puede requerir configuración adicional
                # Verificar documentación de AssemblyAI para habilitar words
                
                logger.info("Enviando video a AssemblyAI para transcripcion...")
                
                # Transcribir usando el archivo local (mp4_path ya está descargado)
                transcript = transcriber.transcribe(mp4_path, config=config)
                
                if transcript.status == aai.TranscriptStatus.error:
                    raise ValueError(f"AssemblyAI transcription error: {transcript.error}")
                
                # Esperar hasta que este completa
                while transcript.status not in (aai.TranscriptStatus.completed, aai.TranscriptStatus.error):
                    time.sleep(2)
                    transcript = transcriber.get_transcript(transcript.id)
                    if transcript.status == aai.TranscriptStatus.error:
                        raise ValueError(f"AssemblyAI transcription error: {transcript.error}")
                    # Actualizar progreso durante el polling
                    if total_duration and total_duration > 0:
                        estimated_progress = min(90, last_progress + 5)
                        if estimated_progress - last_progress >= 5:
                            sermon.progress = estimated_progress
                            session.commit()
                            last_progress = estimated_progress
                
                transcription_end_time = time.time()
                transcription_duration = transcription_end_time - transcription_start_time
                transcription_minutes = transcription_duration / 60.0
                
                logger.info("AssemblyAI devolvio la transcripcion en %.2f minutos (%.1f segundos)", transcription_minutes, transcription_duration)
                
                # Log para debug: verificar qué devuelve AssemblyAI
                has_utterances = bool(transcript.utterances)
                has_words = bool(transcript.words)
                utterances_count = len(transcript.utterances) if transcript.utterances else 0
                words_count = len(transcript.words) if transcript.words else 0
                logger.info("AssemblyAI transcript: utterances=%s (%d), words=%s (%d)", 
                           has_utterances, utterances_count, has_words, words_count)
                
                # Procesar segmentos usando utterances (frases completas)
                if transcript.utterances:
                    # Mapear words por utterance para timestamps precisos (v3)
                    words_by_utterance = {}
                    if transcript.words:
                        # Agrupar words por utterance usando timestamps
                        for word in transcript.words:
                            word_start_ms = int(word.start)
                            word_end_ms = int(word.end)
                            # Encontrar el utterance que contiene esta palabra
                            for idx, utterance in enumerate(transcript.utterances):
                                utt_start_ms = int(utterance.start)
                                utt_end_ms = int(utterance.end)
                                if word_start_ms >= utt_start_ms and word_end_ms <= utt_end_ms:
                                    if idx not in words_by_utterance:
                                        words_by_utterance[idx] = []
                                    words_by_utterance[idx].append({
                                        "text": word.text.strip(),
                                        "start_ms": word_start_ms,
                                        "end_ms": word_end_ms
                                    })
                                    break
                        
                        logger.info("AssemblyAI: Mapped %d words to %d utterances", words_count, len(words_by_utterance))
                    else:
                        logger.warning("AssemblyAI: transcript.utterances exists but transcript.words is None/empty - word timestamps no disponibles")
                    
                    segments_with_word_timestamps = 0
                    for idx, utterance in enumerate(transcript.utterances):
                        text = utterance.text.strip()
                        if not text:
                            continue
                        start_ms = int(utterance.start)
                        end_ms = int(utterance.end)
                        
                        # Guardar word timestamps si están disponibles (para v3)
                        word_timestamps = words_by_utterance.get(idx)
                        if word_timestamps:
                            segments_with_word_timestamps += 1
                        
                        batch.append(
                            TranscriptSegment(
                                sermon_id=sermon.id,
                                start_ms=start_ms,
                                end_ms=end_ms,
                                text=text,
                                word_timestamps_json=word_timestamps if word_timestamps else None,
                            )
                        )
                        count += 1
                        if len(batch) >= batch_size:
                            session.bulk_save_objects(batch)
                            session.commit()
                            batch = []
                        
                        if total_duration and total_duration > 0:
                            progress = int(min(95, max(5, (utterance.end / total_duration) * 90 + 5)))
                            if progress - last_progress >= 2:
                                sermon.progress = progress
                                session.commit()
                                last_progress = progress
                    
                    logger.info("AssemblyAI: Saved %d/%d segments with word timestamps", segments_with_word_timestamps, len(transcript.utterances))
                elif transcript.words:
                    # Fallback: usar palabras si no hay utterances
                    # Agrupar palabras en segmentos y guardar word timestamps para v3
                    current_text = []
                    current_words = []  # Para guardar word timestamps del segmento actual
                    current_start = None
                    current_end = None
                    
                    for word in transcript.words:
                        word_text = word.text.strip()
                        if not word_text:
                            continue
                        word_start_ms = int(word.start)
                        word_end_ms = int(word.end)
                        
                        if current_start is None:
                            current_start = word_start_ms
                            current_text = [word_text]
                            current_words = [{
                                "text": word_text,
                                "start_ms": word_start_ms,
                                "end_ms": word_end_ms
                            }]
                        elif (word_start_ms - current_end) < 2000:  # Agrupar si hay menos de 2 segundos de diferencia
                            current_text.append(word_text)
                            current_words.append({
                                "text": word_text,
                                "start_ms": word_start_ms,
                                "end_ms": word_end_ms
                            })
                        else:
                            # Guardar el segmento actual con word timestamps
                            if current_text:
                                batch.append(
                                    TranscriptSegment(
                                        sermon_id=sermon.id,
                                        start_ms=current_start,
                                        end_ms=current_end,
                                        text=" ".join(current_text),
                                        word_timestamps_json=current_words if current_words else None,
                                    )
                                )
                                count += 1
                                if len(batch) >= batch_size:
                                    session.bulk_save_objects(batch)
                                    session.commit()
                                    batch = []
                            # Iniciar nuevo segmento
                            current_start = word_start_ms
                            current_text = [word_text]
                            current_words = [{
                                "text": word_text,
                                "start_ms": word_start_ms,
                                "end_ms": word_end_ms
                            }]
                        
                        current_end = word_end_ms
                        
                        if total_duration and total_duration > 0:
                            progress = int(min(95, max(5, (word_end_ms / total_duration) * 90 + 5)))
                            if progress - last_progress >= 2:
                                sermon.progress = progress
                                session.commit()
                                last_progress = progress
                    
                    # Guardar el ultimo segmento con word timestamps
                    if current_text and current_start is not None and current_end is not None:
                        batch.append(
                            TranscriptSegment(
                                sermon_id=sermon.id,
                                start_ms=current_start,
                                end_ms=current_end,
                                text=" ".join(current_text),
                                word_timestamps_json=current_words if current_words else None,
                            )
                        )
                        count += 1
                    
                    logger.info("AssemblyAI: Saved %d segments from words (all with word timestamps)", count)
                else:
                    raise ValueError("AssemblyAI transcription completed but no utterances or words found")
            else:
                # Transcripcion con faster-whisper (default)
                # Medir tiempo de conversion video a audio
                audio_conversion_start_time = time.time()
                logger.info("Convirtiendo video a audio...")
                
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
                
                audio_conversion_end_time = time.time()
                audio_conversion_duration = audio_conversion_end_time - audio_conversion_start_time
                audio_conversion_minutes = audio_conversion_duration / 60.0
                logger.info("Conversion video->audio completada en %.2f minutos (%.1f segundos)", audio_conversion_minutes, audio_conversion_duration)
                
                # Medir tiempo de transcripcion
                transcription_start_time = time.time()
                logger.info("Transcribiendo audio con Faster-Whisper...")

                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                transcribe_kwargs = {}
                if language:
                    transcribe_kwargs["language"] = language
                segments, info = model.transcribe(wav_path, **transcribe_kwargs)
                
                transcription_end_time = time.time()
                transcription_duration = transcription_end_time - transcription_start_time
                transcription_minutes = transcription_duration / 60.0
                
                seg_total_duration = getattr(info, "duration", None)
                if seg_total_duration is None and isinstance(info, dict):
                    seg_total_duration = info.get("duration")
                if seg_total_duration and not total_duration:
                    total_duration = seg_total_duration

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
                
                total_time = audio_conversion_duration + transcription_duration
                total_minutes = total_time / 60.0
                
                logger.info("Faster-Whisper completó la transcripcion en %.2f minutos (%.1f segundos)", transcription_minutes, transcription_duration)
                logger.info("Tiempo total del proceso: %.2f minutos (%.1f segundos)", total_minutes, total_time)

            if batch:
                session.bulk_save_objects(batch)
                session.commit()

            session.commit()

        transcription_ok = True
        error_details: list[str] = []

        if sermon.video_duration_sec and count > 0:
            last_segment = session.execute(
                select(TranscriptSegment)
                .where(
                    TranscriptSegment.sermon_id == sermon_id,
                    TranscriptSegment.deleted_at.is_(None),
                )
                .order_by(TranscriptSegment.end_ms.desc())
                .limit(1)
            ).scalar_one_or_none()

            if last_segment:
                transcribed_duration_sec = last_segment.end_ms / 1000.0
                expected_duration_sec = sermon.video_duration_sec
                if expected_duration_sec > 0:
                    coverage_percent = (
                        transcribed_duration_sec / expected_duration_sec
                    ) * 100
                    logger.info(
                        "Sermon %s coverage: %.1f%% (%.1fs / %.1fs)",
                        sermon_id,
                        coverage_percent,
                        transcribed_duration_sec,
                        expected_duration_sec,
                    )
                    if coverage_percent < 95:
                        transcription_ok = False
                        missing_seconds = expected_duration_sec - transcribed_duration_sec
                        error_details.append(
                            "Transcripcion incompleta: {coverage:.1f}% (faltan {missing:.1f} segundos)".format(
                                coverage=coverage_percent,
                                missing=missing_seconds,
                            )
                        )
        elif count == 0:
            # Si no hay segmentos generados, es un error
            transcription_ok = False
            error_details.append("No se generaron segmentos de transcripcion")
        
        # Nota: NO validamos cantidad de segmentos basado en video_duration_sec / 3
        # porque Whisper genera segmentos de duración variable (1-10+ segundos) dependiendo
        # del contenido del audio (pausas, silencios, velocidad de habla, etc.)
        # La validación de cobertura de duración (arriba) es la métrica correcta.

        session.refresh(sermon)
        if sermon.deleted_at is not None:
            logger.info("Sermon %s deleted during transcription", sermon_id)
            return {"sermon_id": sermon_id, "status": "deleted"}

        if transcription_ok:
            sermon.status = SermonStatus.transcribed
            sermon.progress = 100
            sermon.error_message = None
            logger.info(
                "Sermon %s transcribed successfully: %s segments", sermon_id, count
            )
        else:
            sermon.status = SermonStatus.error
            sermon.progress = 50
            sermon.error_message = " | ".join(error_details)
            logger.error("Sermon %s incomplete: %s", sermon_id, sermon.error_message)

        session.commit()
        return {
            "sermon_id": sermon.id,
            "segments": count,
            "complete": transcription_ok,
        }
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
def suggest_clips(
    self,
    sermon_id: int,
    use_llm: bool | None = None,
    llm_method: str = "scoring",
    llm_provider: str = "deepseek",
    full_context_prompt_version: str = "v1",
) -> dict:
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
        
        # Validar word timestamps para v3
        if full_context_prompt_version == "v3":
            segments_with_word_timestamps = [s for s in segments if s.word_timestamps_json is not None and len(s.word_timestamps_json) > 0]
            if not segments_with_word_timestamps:
                error_msg = (
                    "v3 requiere word timestamps exactos de AssemblyAI. "
                    "Este sermon no tiene word timestamps. "
                    "Usa AssemblyAI para transcribir o usa v1/v2 que no requieren word timestamps."
                )
                sermon.error_message = error_msg
                session.commit()
                raise ValueError(error_msg)
            
            # Verificar que al menos el 80% de los segments tengan word timestamps
            coverage = len(segments_with_word_timestamps) / len(segments) if segments else 0
            if coverage < 0.8:
                error_msg = (
                    f"v3 requiere word timestamps exactos. "
                    f"Solo {coverage*100:.1f}% de los segments tienen word timestamps. "
                    f"Usa AssemblyAI para transcribir o usa v1/v2."
                )
                sermon.error_message = error_msg
                session.commit()
                raise ValueError(error_msg)
            
            logger.info("v3: Validated word timestamps - %d/%d segments have word timestamps (%.1f%%)", 
                       len(segments_with_word_timestamps), len(segments), coverage * 100)

        embeddings_ready = _attach_embeddings(session, segments)
        embedding_prefix = _build_embedding_prefix(segments) if embeddings_ready else None

        use_llm_effective = (
            settings.use_llm_for_clip_suggestions if use_llm is None else use_llm
        )
        llm_provider_effective = llm_provider if llm_provider in ("deepseek", "openai") else "deepseek"
        
        if use_llm_effective:
            provider_name = "OpenAI" if llm_provider_effective == "openai" else "Deepseek"
            logger.info("Generando sugerencias de clips usando IA (%s) para sermon %s", provider_name, sermon_id)
        else:
            logger.info("Generando sugerencias de clips usando heuristica para sermon %s", sermon_id)

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
        llm_provider_effective = llm_provider if llm_provider in ("deepseek", "openai") else "deepseek"
        llm_used = False
        token_usage = None
        token_usage_by_method: dict[str, dict] = {}
        llm_method_effective = llm_method if llm_method in ("scoring", "selection", "generation", "full-context") else "full-context"

        # Pre-cargar utterances para v3 (reutilizar después)
        utterances_for_v3 = None
        if use_llm_effective and llm_method_effective == "full-context" and full_context_prompt_version == "v3":
            try:
                # Usar force_regenerate solo si está habilitado en settings
                force_regenerate = getattr(settings, "force_regenerate_utterances", False)
                utterances_for_v3 = _ensure_utterances(session, sermon_id, segments, force_regenerate=force_regenerate)
                if utterances_for_v3:
                    logger.info("v3: Pre-loaded %d utterances for transcript and mapping (force_regenerate=%s)", len(utterances_for_v3), force_regenerate)
            except Exception as exc:
                logger.warning("v3: Error pre-loading utterances: %s", exc)
                utterances_for_v3 = None
        
        if use_llm_effective and llm_method_effective == "full-context":
            # v3 usa utterances, v1/v2 usan segments
            if full_context_prompt_version == "v3":
                if utterances_for_v3:
                    full_text = "\n".join(
                        f"[u{utterance.idx} {utterance.start_ms}-{utterance.end_ms}] {utterance.text}"
                        for utterance in utterances_for_v3
                        if utterance.text
                    )
                    logger.info("v3: Using utterances format for transcript: %d utterances", len(utterances_for_v3))
                else:
                    # Fallback a segments si no hay utterances
                    logger.warning("v3: No utterances available, falling back to segments format")
                    full_text = "\n".join(
                        f"[{segment.start_ms / 1000:.1f}s] {segment.text}"
                        for segment in segments
                        if segment.text
                    )
            else:
                # v1/v2: formato original con segments
                full_text = "\n".join(
                    f"[{segment.start_ms / 1000:.1f}s] {segment.text}"
                    for segment in segments
                    if segment.text
                )
            word_count = len(full_text.split())
            metadata = {
                "title": sermon.title,
                "preacher": sermon.preacher,
                "duration_sec": segments[-1].end_ms / 1000.0,
            }
            try:
                if llm_provider_effective == "openai":
                    generate_fn = openai_generate_from_full_transcript
                    api_key = settings.openai_api_key
                    base_url = settings.openai_base_url
                    model = settings.openai_model
                    error_class = OpenAIClientError
                    provider_name = "OpenAI"
                else:
                    generate_fn = deepseek_generate_from_full_transcript
                    api_key = settings.deepseek_api_key
                    base_url = settings.deepseek_base_url
                    model = settings.deepseek_model
                    error_class = DeepseekClientError
                    provider_name = "Deepseek"

                llm_start_time = time.time()
                logger.info("Enviando a %s un transcript de %d palabras para sugerencias de clips...", provider_name, word_count)
                
                # Escribir transcript completo a transcript.md en la raíz
                try:
                    from pathlib import Path
                    # Desde apps/worker/src/tasks.py -> apps/worker/src -> apps/worker -> apps -> raíz
                    root_dir = Path(__file__).resolve().parents[3]
                    transcript_path = root_dir / "transcript.md"
                    
                    # Construir el user_prompt completo que se enviará
                    if full_context_prompt_version == "v3":
                        system_prompt = full_context_system_prompt_v3()
                    elif full_context_prompt_version == "v2":
                        system_prompt = full_context_system_prompt_v2()
                    else:
                        system_prompt = full_context_system_prompt()
                    
                    duration_label = f"{metadata.get('duration_sec', 0):.1f}s"
                    user_prompt = full_context_user_prompt(
                        title=metadata.get("title", ""),
                        preacher=metadata.get("preacher", ""),
                        duration_label=duration_label,
                        transcript=full_text,
                    )
                    
                    transcript_content = f"""# Transcript enviado a {provider_name}

## Metadata
- Sermon ID: {sermon_id}
- Título: {metadata.get('title', 'N/A')}
- Predicador: {metadata.get('preacher', 'N/A')}
- Duración: {duration_label}
- Prompt Version: {full_context_prompt_version}
- Provider: {provider_name}
- Model: {model}
- Palabras: {word_count}

## System Prompt

{system_prompt}

## User Prompt

{user_prompt}

## Transcript Completo (sin truncar)

{full_text}
"""
                    
                    with open(transcript_path, "w", encoding="utf-8") as f:
                        f.write(transcript_content)
                    logger.info("Transcript completo guardado en %s", transcript_path)
                except Exception as exc:
                    logger.warning("Error al guardar transcript.md: %s", exc)
                
                response = generate_fn(
                    full_text,
                    metadata,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    timeout=120.0,
                    prompt_version=full_context_prompt_version,
                )
                
                llm_end_time = time.time()
                llm_duration = llm_end_time - llm_start_time
                llm_minutes = llm_duration / 60.0
                
                token_usage = response.get("token_usage")
                if token_usage:
                    token_usage_by_method["full-context"] = _merge_token_usage(
                        token_usage_by_method.get("full-context"),
                        token_usage,
                    )
                suggestions = response.get("clips") or []
                candidates = []
                
                # Para v3, reutilizar utterances ya cargadas (no recargar)
                utterances = None
                if full_context_prompt_version == "v3":
                    if utterances_for_v3:
                        utterances = utterances_for_v3
                        logger.info("v3: Reusing utterances list for mapping (no re-fetch)")
                    else:
                        try:
                            utterances = _ensure_utterances(session, sermon_id, segments)
                            logger.warning("v3: Had to reload utterances for mapping (should not happen)")
                        except Exception as exc:
                            logger.warning("v3: Error loading utterances for mapping: %s", exc)
                            utterances = None
                
                # Log ejemplo de suggestion cruda (solo v3, solo una vez, truncado)
                if full_context_prompt_version == "v3" and suggestions:
                    example = dict(suggestions[0])
                    # Truncar strings largas
                    for key, value in example.items():
                        if isinstance(value, str) and len(value) > 300:
                            example[key] = value[:300] + "..."
                    logger.debug("v3: raw_suggestion_example=%s", example)
                
                for suggestion in suggestions:
                    used_utterances = False
                    
                    # v3: intentar usar start_u/end_u primero
                    if full_context_prompt_version == "v3" and utterances:
                        start_u = suggestion.get("start_u")
                        end_u = suggestion.get("end_u")
                        
                        if start_u is not None and end_u is not None:
                            try:
                                start_u_val = int(start_u)
                                end_u_val = int(end_u)
                                
                                # Validar rango de IDs (1..len(utterances))
                                utterances_len = len(utterances)
                                if start_u_val < 1 or start_u_val > utterances_len or end_u_val < 1 or end_u_val > utterances_len:
                                    logger.warning(
                                        "v3: INVALID_UTTERANCE_RANGE start_u=%d end_u=%d utterances_len=%d -> falling back",
                                        start_u_val, end_u_val, utterances_len
                                    )
                                    # Continuar al fallback
                                else:
                                    # Validar que los IDs existan
                                    start_utterance = next(
                                        (u for u in utterances if u.idx == start_u_val), None
                                    )
                                    end_utterance = next(
                                        (u for u in utterances if u.idx == end_u_val), None
                                    )
                                    
                                    if start_utterance and end_utterance:
                                        start_ms = start_utterance.start_ms
                                        end_ms = end_utterance.end_ms
                                        
                                        if end_ms <= start_ms:
                                            logger.debug("v3: Invalid utterance range (end <= start): start_u=%d end_u=%d", start_u_val, end_u_val)
                                            continue
                                        
                                        # Pre/post roll removido de aquí - se aplicará al final después de todos los guardrails
                                        sermon_end_ms = segments[-1].end_ms if segments else end_ms
                                        duration_ms = end_ms - start_ms
                                        
                                        if duration_ms < MIN_CLIP_MS or duration_ms > MAX_CLIP_MS:
                                            logger.debug("v3: Duration out of range: %dms (start_u=%d end_u=%d)", duration_ms, start_u_val, end_u_val)
                                            continue
                                        
                                        # Construir texto desde utterances (sin snapping)
                                        text = _build_text_for_utterance_range(utterances, start_u_val, end_u_val)
                                        if not text:
                                            logger.debug("v3: Empty text for utterance range: start_u=%d end_u=%d", start_u_val, end_u_val)
                                            continue
                                        
                                        # Context guardrail: ajustar start_u si el clip empieza con frases que requieren contexto
                                        original_start_u = start_u_val
                                        if _looks_like_needs_context(start_utterance.text):
                                            adjusted = False
                                            for back in [1, 2, 3]:
                                                candidate_start_u = start_u_val - back
                                                if candidate_start_u < 1:
                                                    break
                                                
                                                candidate_start_utterance = next(
                                                    (u for u in utterances if u.idx == candidate_start_u), None
                                                )
                                                if not candidate_start_utterance:
                                                    break
                                                
                                                # Calcular nueva duración
                                                candidate_start_ms = candidate_start_utterance.start_ms
                                                candidate_duration_ms = end_ms - candidate_start_ms
                                                
                                                # Validar que no exceda MAX_CLIP_MS
                                                if candidate_duration_ms > MAX_CLIP_MS:
                                                    logger.debug(
                                                        "v3: Context guardrail: candidate start_u=%d would exceed MAX_CLIP_MS (%d > %d), skipping",
                                                        candidate_start_u, candidate_duration_ms, MAX_CLIP_MS
                                                    )
                                                    continue
                                                
                                                # Validar que no sea menor que MIN_CLIP_MS (aunque normalmente crecerá)
                                                if candidate_duration_ms < MIN_CLIP_MS:
                                                    logger.debug(
                                                        "v3: Context guardrail: candidate start_u=%d would be below MIN_CLIP_MS (%d < %d), skipping",
                                                        candidate_start_u, candidate_duration_ms, MIN_CLIP_MS
                                                    )
                                                    continue
                                                
                                                # Reconstruir texto con el candidato para validar
                                                candidate_text = _build_text_for_utterance_range(utterances, candidate_start_u, end_u_val)
                                                if not candidate_text:
                                                    logger.debug(
                                                        "v3: Context guardrail: candidate start_u=%d produces empty text, skipping",
                                                        candidate_start_u
                                                    )
                                                    continue
                                                
                                                # Aceptar el primer candidato válido
                                                start_u_val = candidate_start_u
                                                start_ms = candidate_start_ms
                                                duration_ms = candidate_duration_ms
                                                text = candidate_text
                                                
                                                logger.info(
                                                    "v3: CONTEXT_GUARD adjusted start_u %d->%d (reason=needs_context) duration_ms=%d",
                                                    original_start_u, start_u_val, duration_ms
                                                )
                                                adjusted = True
                                                break
                                            
                                            if not adjusted:
                                                logger.debug(
                                                    "v3: Context guardrail: could not adjust start_u=%d (no valid candidates within limits)",
                                                    original_start_u
                                                )
                                        
                                        # Hook guardrail: mejorar hooks flojos
                                        _, current_hook_score = _is_hook_advanced(start_utterance.text)
                                        if current_hook_score < 0.35:
                                            # Evaluar primeras 6 utterances del rango
                                            eval_end_u = min(start_u_val + 5, end_u_val)
                                            best_hook_score = current_hook_score
                                            best_hook_idx = start_u_val
                                            
                                            for eval_idx in range(start_u_val, eval_end_u + 1):
                                                if eval_idx > utterances_len:
                                                    break
                                                eval_utterance = next(
                                                    (u for u in utterances if u.idx == eval_idx), None
                                                )
                                                if not eval_utterance:
                                                    continue
                                                
                                                _, eval_hook_score = _is_hook_advanced(eval_utterance.text)
                                                if eval_hook_score >= 0.45 and eval_hook_score > best_hook_score:
                                                    best_hook_score = eval_hook_score
                                                    # Si el mejor hook está después del start actual, usar el anterior como setup
                                                    if eval_idx > start_u_val:
                                                        best_hook_idx = eval_idx - 1
                                                    else:
                                                        best_hook_idx = eval_idx
                                            
                                            if best_hook_idx != start_u_val:
                                                # Ajustar start_u hacia atrás o adelante según el mejor hook
                                                candidate_start_u = best_hook_idx
                                                candidate_start_utterance = next(
                                                    (u for u in utterances if u.idx == candidate_start_u), None
                                                )
                                                
                                                if candidate_start_utterance:
                                                    candidate_start_ms = candidate_start_utterance.start_ms
                                                    candidate_duration_ms = end_ms - candidate_start_ms
                                                    
                                                    if candidate_duration_ms <= MAX_CLIP_MS and candidate_duration_ms >= MIN_CLIP_MS:
                                                        candidate_text = _build_text_for_utterance_range(utterances, candidate_start_u, end_u_val)
                                                        if candidate_text:
                                                            old_start_u = start_u_val
                                                            start_u_val = candidate_start_u
                                                            start_ms = candidate_start_ms
                                                            duration_ms = candidate_duration_ms
                                                            text = candidate_text
                                                            start_utterance = candidate_start_utterance
                                                            
                                                            logger.info(
                                                                "v3: HOOK_GUARD adjusted start_u %d->%d hook_score %.2f->%.2f duration_ms=%d",
                                                                old_start_u, start_u_val, current_hook_score, best_hook_score, duration_ms
                                                            )
                                        
                                        # CLOSING_GUARD mejorado: cerrar idea si termina incompleto
                                        original_end_u = end_u_val
                                        if _looks_like_incomplete_end(end_utterance.text):
                                            # Intentar extender end_u hasta +10 o hasta encontrar cierre natural
                                            for extend in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                                                candidate_end_u = end_u_val + extend
                                                if candidate_end_u > utterances_len:
                                                    break
                                                
                                                candidate_end_utterance = next(
                                                    (u for u in utterances if u.idx == candidate_end_u), None
                                                )
                                                if not candidate_end_utterance:
                                                    break
                                                
                                                candidate_end_ms = candidate_end_utterance.end_ms
                                                candidate_duration_ms = candidate_end_ms - start_ms
                                                
                                                if candidate_duration_ms > MAX_CLIP_MS:
                                                    break
                                                
                                                candidate_text = _build_text_for_utterance_range(utterances, start_u_val, candidate_end_u)
                                                if not candidate_text:
                                                    break
                                                
                                                # Verificar si el nuevo end es clean (puntuación fuerte y NO conector)
                                                if _looks_like_clean_end(candidate_end_utterance.text):
                                                    end_u_val = candidate_end_u
                                                    end_ms = candidate_end_ms
                                                    duration_ms = candidate_duration_ms
                                                    text = candidate_text
                                                    end_utterance = candidate_end_utterance
                                                    
                                                    logger.info(
                                                        "v3: CLOSING_GUARD extended end_u %d->%d duration_ms=%d reason=incomplete_end",
                                                        original_end_u, end_u_val, duration_ms
                                                    )
                                                    break
                                        
                                        # Si end_u ya es limpio pero el texto termina corto, permitir extender 1-3 utterances
                                        if _looks_like_clean_end(end_utterance.text):
                                            # Verificar si el texto final es muy corto o suena abierto
                                            final_text_len = len(end_utterance.text.strip())
                                            if final_text_len < 20:  # Texto muy corto
                                                for extend in [1, 2, 3]:
                                                    candidate_end_u = end_u_val + extend
                                                    if candidate_end_u > utterances_len:
                                                        break
                                                    
                                                    candidate_end_utterance = next(
                                                        (u for u in utterances if u.idx == candidate_end_u), None
                                                    )
                                                    if not candidate_end_utterance:
                                                        break
                                                    
                                                    candidate_end_ms = candidate_end_utterance.end_ms
                                                    candidate_duration_ms = candidate_end_ms - start_ms
                                                    
                                                    if candidate_duration_ms > MAX_CLIP_MS:
                                                        break
                                                    
                                                    candidate_text = _build_text_for_utterance_range(utterances, start_u_val, candidate_end_u)
                                                    if not candidate_text:
                                                        break
                                                    
                                                    # Verificar que el nuevo end también sea clean
                                                    if _looks_like_clean_end(candidate_end_utterance.text):
                                                        end_u_val = candidate_end_u
                                                        end_ms = candidate_end_ms
                                                        duration_ms = candidate_duration_ms
                                                        text = candidate_text
                                                        end_utterance = candidate_end_utterance
                                                        
                                                        logger.info(
                                                            "v3: CLOSING_GUARD extended end_u %d->%d duration_ms=%d reason=short_final",
                                                            original_end_u, end_u_val, duration_ms
                                                        )
                                                        break
                                        
                                        # POST_ROLL mejorado: evitar cortar palabras sin pasarse al siguiente tema
                                        PAD_MS = 800  # Aumentado de 300 a 800ms
                                        original_end_ms_before_roll = end_ms
                                        
                                        # Calcular next_start_ms del siguiente utterance (si existe)
                                        next_utterance = next(
                                            (u for u in utterances if u.idx == end_u_val + 1), None
                                        )
                                        next_start_ms = next_utterance.start_ms if next_utterance else None
                                        
                                        # Aplicar post-roll con clamp inteligente
                                        candidate_end_ms = end_ms + PAD_MS
                                        
                                        # Clamp por sermon_end_ms
                                        candidate_end_ms = min(candidate_end_ms, sermon_end_ms)
                                        
                                        # Clamp por siguiente utterance SOLO si hay gap real >= 500ms
                                        # Esto permite arreglar cortes de palabra cuando end_ms cae en mitad de palabra
                                        clamped_by_next = False
                                        if next_start_ms is not None:
                                            gap_ms = next_start_ms - end_ms
                                            if gap_ms >= 500:
                                                # Hay gap real, aplicar clamp para no pasarse al siguiente tema
                                                candidate_end_ms = min(candidate_end_ms, next_start_ms - 50)
                                                clamped_by_next = True
                                            # Si gap < 500ms, NO clamps (permite arreglar cortes de palabra)
                                        
                                        candidate_duration_ms = candidate_end_ms - start_ms
                                        
                                        # Validar que no exceda MAX_CLIP_MS
                                        if candidate_duration_ms <= MAX_CLIP_MS:
                                            end_ms = candidate_end_ms
                                            duration_ms = candidate_duration_ms
                                            
                                            logger.debug(
                                                "v3: END_PAD applied pad_ms=%d end_ms %d->%d clamped_by_next=%s (gap=%s)",
                                                PAD_MS, original_end_ms_before_roll, end_ms, clamped_by_next,
                                                f"{next_start_ms - original_end_ms_before_roll}ms" if next_start_ms else "N/A"
                                            )
                                        else:
                                            # Revertir post-roll si excede
                                            logger.debug(
                                                "v3: END_PAD skipped (would exceed MAX_CLIP_MS: %d > %d)",
                                                candidate_duration_ms, MAX_CLIP_MS
                                            )
                                        
                                        # Safety net: snap final a boundary real de TranscriptSegment
                                        if segments:
                                            # Buscar el segment end_ms inmediato >= end_ms (ceil)
                                            candidate_end_ms = None
                                            min_diff = float('inf')
                                            
                                            for segment in segments:
                                                if segment.end_ms >= end_ms:
                                                    diff = segment.end_ms - end_ms
                                                    if diff <= 800 and diff < min_diff:
                                                        candidate_end_ms = segment.end_ms
                                                        min_diff = diff
                                            
                                            if candidate_end_ms is not None:
                                                original_end_ms_before_snap = end_ms
                                                end_ms = candidate_end_ms
                                                duration_ms = end_ms - start_ms
                                                
                                                # Validar que no exceda MAX_CLIP_MS
                                                if duration_ms <= MAX_CLIP_MS:
                                                    logger.info(
                                                        "v3: END_SNAP_SEGMENT end_ms %d->%d",
                                                        original_end_ms_before_snap, end_ms
                                                    )
                                                else:
                                                    # Revertir snap si excede
                                                    end_ms = original_end_ms_before_snap
                                                    duration_ms = end_ms - start_ms
                                        
                                        # START_PAD robusto: aplicar al final después de todos los guardrails
                                        START_PAD_MS = 400
                                        original_start_ms_before_pad = start_ms
                                        
                                        # Aplicar pre-roll
                                        candidate_start_ms = max(0, start_ms - START_PAD_MS)
                                        
                                        # Clamp inteligente por prev_utterance (solo si hay silencio real)
                                        prev_utterance = next(
                                            (u for u in utterances if u.idx == start_u_val - 1), None
                                        )
                                        clamped_by_prev = False
                                        gap_prev = None
                                        
                                        if prev_utterance:
                                            gap_prev = start_utterance.start_ms - prev_utterance.end_ms
                                            if gap_prev >= 600:  # Silencio real
                                                # Clamp para no cortar sílabas en el silencio
                                                candidate_start_ms = max(candidate_start_ms, prev_utterance.end_ms + 50)
                                                clamped_by_prev = True
                                            # Si gap < 600ms, NO clamps (permite arreglar cortes de palabra)
                                        
                                        candidate_duration_ms = end_ms - candidate_start_ms
                                        
                                        # Validar que no exceda MAX_CLIP_MS ni sea menor que MIN_CLIP_MS
                                        if candidate_duration_ms <= MAX_CLIP_MS and candidate_duration_ms >= MIN_CLIP_MS:
                                            start_ms = candidate_start_ms
                                            duration_ms = candidate_duration_ms
                                            
                                            logger.debug(
                                                "v3: START_PAD applied pad_ms=%d start_ms %d->%d clamped_by_prev=%s (gap_prev=%s)",
                                                START_PAD_MS, original_start_ms_before_pad, start_ms, clamped_by_prev,
                                                f"{gap_prev}ms" if gap_prev is not None else "N/A"
                                            )
                                        else:
                                            # Revertir pre-roll si excede límites
                                            logger.debug(
                                                "v3: START_PAD skipped (would exceed limits: duration_ms=%d, MIN=%d MAX=%d)",
                                                candidate_duration_ms, MIN_CLIP_MS, MAX_CLIP_MS
                                            )
                                        
                                        # Safety net opcional: START_SNAP_SEGMENT (solo si cercano)
                                        if segments:
                                            # Buscar el segment start_ms inmediato <= start_ms (floor)
                                            candidate_start_ms_snap = None
                                            min_diff = float('inf')
                                            
                                            for segment in segments:
                                                if segment.start_ms <= start_ms:
                                                    diff = start_ms - segment.start_ms
                                                    if diff <= 800 and diff < min_diff:
                                                        candidate_start_ms_snap = segment.start_ms
                                                        min_diff = diff
                                            
                                            if candidate_start_ms_snap is not None:
                                                original_start_ms_before_snap = start_ms
                                                candidate_start_ms_snap_final = candidate_start_ms_snap
                                                candidate_duration_ms_snap = end_ms - candidate_start_ms_snap_final
                                                
                                                # Validar que no exceda MAX_CLIP_MS ni sea menor que MIN_CLIP_MS
                                                if candidate_duration_ms_snap <= MAX_CLIP_MS and candidate_duration_ms_snap >= MIN_CLIP_MS:
                                                    start_ms = candidate_start_ms_snap_final
                                                    duration_ms = candidate_duration_ms_snap
                                                    
                                                    logger.info(
                                                        "v3: START_SNAP_SEGMENT start_ms %d->%d",
                                                        original_start_ms_before_snap, start_ms
                                                    )
                                        
                                        reason = suggestion.get("reason") or ""
                                        theme = suggestion.get("theme") or ""
                                        rationale = (
                                            f"{reason} (theme: {theme})" if theme else str(reason)
                                        )
                                        candidates.append(
                                            {
                                                "start_ms": start_ms,
                                                "end_ms": end_ms,
                                                "text": text,
                                                "llm_score": suggestion.get("score"),
                                                "llm_reason": rationale,
                                                "llm_method": "full-context",
                                            }
                                        )
                                        logger.info(
                                            "v3: USING_UTTERANCE_IDS start_u=%d end_u=%d -> start_ms=%d end_ms=%d duration_ms=%d",
                                            start_u_val, end_u_val, start_ms, end_ms, duration_ms
                                        )
                                        used_utterances = True
                                        continue
                                    else:
                                        logger.warning(
                                            "v3: INVALID_UTTERANCE_RANGE start_u=%d end_u=%d utterances_len=%d (IDs not found) -> falling back",
                                            start_u_val, end_u_val, utterances_len
                                        )
                            except (TypeError, ValueError) as exc:
                                logger.debug("v3: Invalid utterance IDs (type error): start_u=%s end_u=%s: %s", start_u, end_u, exc)
                        
                        # Si llegamos aquí y no se usaron utterances, loguear fallback
                        if not used_utterances and full_context_prompt_version == "v3":
                            suggestion_keys = list(suggestion.keys())
                            logger.warning(
                                "v3: FALLBACK_MISSING_UTTERANCE_IDS suggestion_keys=%s (using timestamps/quotes + snapping)",
                                suggestion_keys
                            )
                    
                    # Fallback: quotes (v2) o timestamps (v1/v3)
                    quote_start = suggestion.get("quote_start")
                    quote_end = suggestion.get("quote_end")
                    start_sec = suggestion.get("start_sec")
                    end_sec = suggestion.get("end_sec")
                    
                    # Intentar usar quotes primero (v2)
                    start_ms = None
                    end_ms = None
                    if quote_start and quote_end:
                        start_ms, end_ms = _find_timestamps_by_quote(
                            segments, quote_start, quote_end
                        )
                    
                    # Fallback a timestamps si quotes no funcionaron o no existen (v1/v3)
                    if start_ms is None or end_ms is None:
                        if start_sec is not None and end_sec is not None:
                            try:
                                start_ms = int(round(float(start_sec) * 1000))
                                end_ms = int(round(float(end_sec) * 1000))
                            except (TypeError, ValueError):
                                continue
                        else:
                            continue
                    
                    # v3 usa snapping asimétrico (ceil/floor), v1/v2 usan nearest
                    if full_context_prompt_version == "v3":
                        start_ms, end_ms = _adjust_to_segment_boundaries_v3(
                            segments, start_ms, end_ms
                        )
                    else:
                        start_ms, end_ms = _adjust_to_segment_boundaries(
                            segments, start_ms, end_ms
                        )
                    duration_ms = end_ms - start_ms
                    if duration_ms < MIN_CLIP_MS or duration_ms > MAX_CLIP_MS:
                        continue
                    text = _build_text_for_range(segments, start_ms, end_ms)
                    if not text:
                        continue
                    reason = suggestion.get("reason") or ""
                    theme = suggestion.get("theme") or ""
                    rationale = (
                        f"{reason} (theme: {theme})" if theme else str(reason)
                    )
                    candidates.append(
                        {
                            "start_ms": start_ms,
                            "end_ms": end_ms,
                            "text": text,
                            "llm_score": suggestion.get("score"),
                            "llm_reason": rationale,
                            "llm_method": "full-context",
                        }
                    )
                if not candidates:
                    raise error_class(
                        f"{provider_name} returned no usable full-context clips"
                    )
                logger.info("%s respondio en %.2f minutos y sugirio %d clips", provider_name, llm_minutes, len(candidates))
                llm_used = True
            except (DeepseekClientError, OpenAIClientError) as exc:
                logger.error(
                    "%s full-context unavailable, falling back to heuristics: %s (type=%s, args=%s)",
                    provider_name if llm_provider_effective == "openai" else "Deepseek",
                    exc,
                    type(exc).__name__,
                    exc.args if hasattr(exc, 'args') else None,
                )
                # Log el error original si está disponible
                if hasattr(exc, '__cause__') and exc.__cause__:
                    logger.error("Original error: %s: %s", type(exc.__cause__).__name__, exc.__cause__)
                candidates = all_candidates
                llm_used = False
                token_usage = None
        else:
            candidates = all_candidates

        if use_llm_effective and llm_method_effective == "scoring" and not llm_used:
            try:
                token_usage_scoring = _score_candidates_with_llm(
                    candidates, llm_provider=llm_provider_effective
                )
                if token_usage_scoring:
                    token_usage_by_method["scoring"] = _merge_token_usage(
                        token_usage_by_method.get("scoring"),
                        token_usage_scoring,
                    )
                    token_usage = _merge_token_usage(token_usage, token_usage_scoring)
                llm_used = True
            except (DeepseekClientError, OpenAIClientError) as exc:
                logger.warning("Scoring failed, falling back to heuristics: %s", exc)
                llm_used = False
                token_usage = None

        if llm_used:
            if llm_method_effective == "scoring":
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
                    candidate["llm_method"] = llm_method_effective
                    candidate.setdefault("llm_trim", None)
                    candidate.setdefault("llm_trim_confidence", None)
                    candidate.setdefault("trim_applied", False)
            else:
                for candidate in candidates:
                    llm_score = candidate.get("llm_score")
                    candidate["score"] = (
                        llm_score
                        if isinstance(llm_score, (int, float))
                        else candidate.get("heuristic_score", 0.0)
                    )
                    candidate["rationale"] = (
                        candidate.get("llm_reason")
                        or candidate.get("heuristic_rationale", "")
                    )
                    candidate["use_llm"] = True
                    candidate.setdefault("llm_method", llm_method_effective)
                    candidate["llm_trim"] = None
                    candidate["llm_trim_confidence"] = None
                    candidate["trim_applied"] = False
        else:
            for candidate in candidates:
                candidate["score"] = candidate["heuristic_score"]
                candidate["rationale"] = candidate["heuristic_rationale"]
                candidate["use_llm"] = False
                candidate["llm_method"] = None
                candidate["llm_trim"] = None
                candidate["llm_trim_confidence"] = None
                candidate["trim_applied"] = False

        candidates.sort(key=lambda item: item["score"], reverse=True)
        candidates = _dedupe_candidates(candidates)
        candidates.sort(key=lambda item: item["score"], reverse=True)
        candidates = _semantic_dedupe_candidates(candidates)
        if len(candidates) < MIN_SUGGESTIONS:
            if llm_used and use_llm_effective:
                sermon_context = _build_sermon_context(segments, limit_chars=2000)
                candidates, selection_usage = _backfill_with_selection(
                    candidates,
                    all_candidates,
                    sermon_context,
                    MIN_SUGGESTIONS,
                    llm_provider=llm_provider_effective,
                )
                if selection_usage:
                    token_usage_by_method["selection"] = _merge_token_usage(
                        token_usage_by_method.get("selection"),
                        selection_usage,
                    )
                    token_usage = _merge_token_usage(token_usage, selection_usage)
            else:
                candidates = _backfill_candidates(
                    candidates, all_candidates, MIN_SUGGESTIONS
                )
        candidates = candidates[:MAX_SUGGESTIONS]

        if llm_used:
            if token_usage_by_method:
                for method, usage in token_usage_by_method.items():
                    _log_llm_usage(sermon_id, method, usage)
            else:
                _log_llm_usage(sermon_id, llm_method_effective, token_usage)
        token_share_map: dict[str, dict] = {}
        if llm_used and token_usage_by_method:
            for method, usage in token_usage_by_method.items():
                method_count = sum(
                    1
                    for candidate in candidates
                    if candidate.get("use_llm")
                    and candidate.get("llm_method") == method
                )
                token_share_map[method] = _split_token_usage(usage, method_count)
        llm_count = sum(1 for candidate in candidates if candidate.get("use_llm"))
        token_share = None
        if llm_used and not token_usage_by_method:
            token_share = _split_token_usage(token_usage, llm_count)

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
        preview_ids = []
        for index, candidate in enumerate(candidates):
            should_warmup = index < PREVIEW_WARMUP_COUNT
            token_share_for_clip = None
            if candidate.get("use_llm"):
                if token_share_map:
                    token_share_for_clip = token_share_map.get(
                        candidate.get("llm_method")
                    )
                else:
                    token_share_for_clip = token_share
            clip = Clip(
                sermon_id=sermon_id,
                start_ms=candidate["start_ms"],
                end_ms=candidate["end_ms"],
                source=ClipSource.auto,
                score=candidate["score"],
                rationale=candidate["rationale"],
                use_llm=candidate["use_llm"],
                llm_method=candidate.get("llm_method"),
                llm_prompt_tokens=token_share_for_clip.get("prompt_tokens")
                if token_share_for_clip
                else None,
                llm_completion_tokens=token_share_for_clip.get("completion_tokens")
                if token_share_for_clip
                else None,
                llm_output_tokens=token_share_for_clip.get("output_tokens")
                if token_share_for_clip
                else None,
                llm_cache_hit_tokens=token_share_for_clip.get("cache_hit_tokens")
                if token_share_for_clip
                else None,
                llm_cache_miss_tokens=token_share_for_clip.get("cache_miss_tokens")
                if token_share_for_clip
                else None,
                llm_total_tokens=token_share_for_clip.get("total_tokens")
                if token_share_for_clip
                else None,
                llm_estimated_cost=token_share_for_clip.get("estimated_cost_usd")
                if token_share_for_clip
                else None,
                llm_trim=candidate.get("llm_trim"),
                llm_trim_confidence=candidate.get("llm_trim_confidence"),
                trim_applied=bool(candidate.get("trim_applied")),
                status=ClipStatus.pending,
                render_type=ClipRenderType.preview
                if should_warmup
                else ClipRenderType.final,
            )
            session.add(clip)
            session.flush()
            if token_share_for_clip:
                _append_ia_log(
                    "\n".join(
                        [
                            "-----------------------------------",
                            f"{datetime.utcnow().isoformat(timespec='seconds')} CLIP {clip.id} TOKENS",
                            f"Sermon: {sermon_id}",
                            f"Method: {candidate.get('llm_method')}",
                            f"Prompt tokens: {token_share_for_clip.get('prompt_tokens', 0)}",
                            "Output tokens: {value}".format(
                                value=token_share_for_clip.get(
                                    "output_tokens",
                                    token_share_for_clip.get("completion_tokens", 0),
                                )
                            ),
                            f"Total tokens: {token_share_for_clip.get('total_tokens', 0)}",
                            "Cache hit tokens: {value}".format(
                                value=token_share_for_clip.get("cache_hit_tokens")
                                if token_share_for_clip.get("cache_hit_tokens")
                                is not None
                                else "n/a"
                            ),
                            "Cache miss tokens: {value}".format(
                                value=token_share_for_clip.get("cache_miss_tokens")
                                if token_share_for_clip.get("cache_miss_tokens")
                                is not None
                                else "n/a"
                            ),
                            "-----------------------------------",
                            "",
                        ]
                    )
                )
                logger.info(
                    "Clip %s tokens - prompt=%s output=%s total=%s cache_hit=%s cache_miss=%s",
                    clip.id,
                    token_share_for_clip.get("prompt_tokens", 0),
                    token_share_for_clip.get(
                        "output_tokens",
                        token_share_for_clip.get("completion_tokens", 0),
                    ),
                    token_share_for_clip.get("total_tokens", 0),
                    token_share_for_clip.get("cache_hit_tokens")
                    if token_share_for_clip.get("cache_hit_tokens") is not None
                    else "n/a",
                    token_share_for_clip.get("cache_miss_tokens")
                    if token_share_for_clip.get("cache_miss_tokens") is not None
                    else "n/a",
                )
            if should_warmup:
                preview_ids.append(clip.id)
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

        if preview_ids:
            logger.info(
                "Auto-generating %s previews for sermon %s",
                len(preview_ids),
                sermon_id,
            )
            for index, clip_id in enumerate(preview_ids):
                try:
                    signature = celery_app.signature(
                        "worker.render_clip",
                        args=[clip_id],
                    ).set(
                        queue="previews",
                        priority=settings.celery_priority_render_preview,
                    )
                    if index == 0:
                        callback = celery_app.signature(
                            "worker.enqueue_pending_previews",
                            args=[sermon_id],
                        ).set(
                            queue="previews",
                            priority=settings.celery_priority_render_preview,
                            immutable=True,
                        )
                        signature.link(callback)
                    signature.apply_async()
                except Exception:
                    logger.exception(
                        "Failed to enqueue preview render for clip %s", clip_id
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
    name="worker.enqueue_pending_previews",
    bind=True,
    max_retries=settings.celery_max_retries,
)
def enqueue_pending_previews(self, sermon_id: int) -> dict:
    session = SessionLocal()
    try:
        pending_ids = list(
            session.execute(
                select(Clip.id)
                .where(Clip.sermon_id == sermon_id)
                .where(Clip.source == ClipSource.auto)
                .where(
                    or_(
                        Clip.render_type == ClipRenderType.preview,
                        Clip.render_type == ClipRenderType.final,
                        Clip.render_type.is_(None),
                    )
                )
                .where(Clip.output_url.is_(None))
                .where(Clip.status == ClipStatus.pending)
                .where(Clip.deleted_at.is_(None))
            ).scalars()
        )
        if not pending_ids:
            return {"sermon_id": sermon_id, "queued": 0}

        session.execute(
            update(Clip)
            .where(Clip.id.in_(pending_ids))
            .values(render_type=ClipRenderType.preview)
        )
        session.commit()

        enqueued_ids = []
        for clip_id in pending_ids:
            try:
                self.app.send_task(
                    "worker.render_clip",
                    args=[clip_id],
                    queue="previews",
                    priority=settings.celery_priority_render_preview,
                )
                enqueued_ids.append(clip_id)
            except Exception:
                logger.exception(
                    "Failed to enqueue preview render for clip %s",
                    clip_id,
                )

        if enqueued_ids:
            session.execute(
                update(Clip)
                .where(Clip.id.in_(enqueued_ids))
                .values(status=ClipStatus.processing)
            )
            session.commit()

        logger.info(
            "Queued %s background previews for sermon %s",
            len(enqueued_ids),
            sermon_id,
        )
        return {"sermon_id": sermon_id, "queued": len(enqueued_ids)}
    except Exception as exc:
        session.rollback()
        _maybe_retry(self, exc, label=f"Enqueue previews for sermon {sermon_id}")
        logger.exception("Failed to enqueue previews for sermon %s", sermon_id)
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
        render_settings = _render_settings(render_type)
        target_width = render_settings["width"]
        target_height = render_settings["height"]
        video_bitrate = render_settings["video_bitrate"]
        audio_bitrate = render_settings["audio_bitrate"]
        maxrate = render_settings["maxrate"]
        bufsize = render_settings["bufsize"]
        preset = render_settings.get("preset", "veryfast")
        crf = render_settings.get("crf")

        with tempfile.TemporaryDirectory() as tmpdir:
            ass_path = f"{tmpdir}/captions.ass"
            output_path = f"{tmpdir}/output.mp4"

            template_config = _resolve_template_config(session, clip)
            with open(ass_path, "w", encoding="utf-8") as handle:
                handle.write(build_ass_from_segments(caption_segments, template_config))

            start_sec = clip.start_ms / 1000.0
            end_sec = clip.end_ms / 1000.0
            duration_sec = end_sec - start_sec

            # Usar presigned URL para streaming directo (no descarga el video completo)
            presigned_url = create_presigned_get_url(
                sermon.source_url, expires_in=3600, use_public_endpoint=False
            )

            # Input seeking (-ss ANTES de -i) es mucho mas rapido que output seeking
            # FFmpeg salta directamente al punto de corte sin procesar frames anteriores
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",                  # INPUT SEEKING - salta directo al timestamp
                    str(start_sec),
                    "-i",
                    presigned_url,          # Streaming directo desde MinIO
                    "-t",                   # Duracion (en lugar de -to que es timestamp absoluto)
                    str(duration_sec),
                    "-vf",
                    f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
                    f"crop={target_width}:{target_height}",  # subtitles desactivados temporalmente: ,subtitles=captions.ass
                    "-c:v",
                    "libx264",
                    "-preset",
                    preset,
                    *(["-crf", crf] if crf else []),
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

        if (
            clip.render_type == ClipRenderType.preview
            and clip.source == ClipSource.auto
            and clip.deleted_at is None
        ):
            done_count = session.execute(
                select(func.count())
                .where(Clip.sermon_id == clip.sermon_id)
                .where(Clip.source == ClipSource.auto)
                .where(Clip.render_type == ClipRenderType.preview)
                .where(Clip.output_url.is_not(None))
                .where(Clip.deleted_at.is_(None))
            ).scalar()
            done_count = int(done_count or 0)
            if done_count >= PREVIEW_WARMUP_COUNT:
                background_ids = list(
                    session.execute(
                        select(Clip.id)
                        .where(Clip.sermon_id == clip.sermon_id)
                        .where(Clip.source == ClipSource.auto)
                        .where(
                            or_(
                                Clip.render_type == ClipRenderType.final,
                                Clip.render_type.is_(None),
                            )
                        )
                        .where(Clip.output_url.is_(None))
                        .where(Clip.status == ClipStatus.pending)
                        .where(Clip.deleted_at.is_(None))
                    ).scalars()
                )
                if background_ids:
                    session.execute(
                        update(Clip)
                        .where(Clip.id.in_(background_ids))
                        .values(render_type=ClipRenderType.preview)
                    )
                    session.commit()
                    enqueued_ids = []
                    for clip_id in background_ids:
                        try:
                            celery_app.send_task(
                                "worker.render_clip",
                                args=[clip_id],
                                queue="previews",
                                priority=settings.celery_priority_render_preview,
                            )
                            enqueued_ids.append(clip_id)
                        except Exception:
                            logger.exception(
                                "Failed to enqueue preview render for clip %s",
                                clip_id,
                            )
                    if enqueued_ids:
                        session.execute(
                            update(Clip)
                            .where(Clip.id.in_(enqueued_ids))
                            .values(status=ClipStatus.processing)
                        )
                        session.commit()
                    logger.info(
                        "Queued %s background previews for sermon %s",
                        len(enqueued_ids),
                        clip.sermon_id,
                    )

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
