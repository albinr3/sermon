import json
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class DeepseekClientError(RuntimeError):
    pass


def _resolve_endpoint(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions") or base.endswith("/v1/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _trim_text(text: str, limit: int = 1500) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= limit:
        return normalized
    if limit < 300:
        return normalized[:limit]
    sep = " ... "
    part_len = max(200, (limit - 2 * len(sep)) // 3)
    middle_len = max(50, limit - part_len * 2 - 2 * len(sep))
    middle_start = max(0, len(normalized) // 2 - middle_len // 2)
    middle_end = min(len(normalized), middle_start + middle_len)
    head = normalized[:part_len]
    middle = normalized[middle_start:middle_end]
    tail = normalized[-part_len:]
    combined = f"{head}{sep}{middle}{sep}{tail}"
    return combined[:limit]


def _extract_message_content(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise DeepseekClientError("Deepseek response missing choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise DeepseekClientError("Deepseek response missing content")
    return content


def _coerce_json(content: str) -> Any:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
        raise


def score_clip_candidates(
    candidates: list[dict],
    *,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    timeout: float = 30.0,
) -> list[dict]:
    if not api_key or not api_key.strip():
        raise DeepseekClientError("Deepseek API key not configured")
    if not base_url or not base_url.strip():
        raise DeepseekClientError("Deepseek base URL not configured")
    if not model or not model.strip():
        raise DeepseekClientError("Deepseek model not configured")

    prompt_candidates = [
        {
            "id": item["id"],
            "text": _trim_text(item.get("text", "")),
            "approx_duration_sec": item.get("approx_duration_sec"),
        }
        for item in candidates
    ]

    # Adjust these prompts to tune the scoring behavior for your domain.
    system_prompt = (
        "Eres un experto en evaluar clips de sermones para redes sociales. "
        "Criterios de evaluacion (0-100): "
        "1. HOOK (0-25): captura atencion en los primeros segundos. "
        "2. CLARIDAD (0-25): se entiende sin contexto previo. "
        "3. APLICABILIDAD (0-25): relevante para la vida diaria. "
        "4. EMOCION (0-25): genera respuesta emocional. "
        "Prioriza clips que sean autonomos, con conclusion clara, "
        "compartibles en redes sociales y conecten emocionalmente. "
        "Devuelve SOLO JSON (sin markdown) como una lista de objetos con: "
        "id, score (0-100), reason, y opcional trim_suggestion "
        "(start_offset_sec, end_offset_sec, confidence). "
        "Los offsets son segundos a recortar desde inicio y fin (>=0), "
        "confidence es de 0 a 1. "
        "Si sugieres recortes, mantenlos pequenos y evita cortar palabras."
    )
    user_prompt = (
        "Candidates JSON:\n"
        f"{json.dumps(prompt_candidates, ensure_ascii=True)}\n\n"
        "Return a JSON array with one entry per candidate id."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    endpoint = _resolve_endpoint(base_url)
    try:
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise DeepseekClientError("Deepseek request failed") from exc

    if response.status_code >= 300:
        logger.warning(
            "Deepseek HTTP error %s: %s", response.status_code, response.text[:500]
        )
        raise DeepseekClientError(f"Deepseek HTTP error {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("Deepseek response not JSON: %s", response.text[:500])
        raise DeepseekClientError("Deepseek response invalid JSON") from exc

    content = _extract_message_content(data)
    try:
        parsed = _coerce_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("Deepseek content not JSON: %s", content[:500])
        raise DeepseekClientError("Deepseek content invalid JSON") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("results") or parsed.get("clips") or []
    if not isinstance(parsed, list):
        raise DeepseekClientError("Deepseek JSON must be a list")

    results: list[dict] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        clip_id = str(item.get("id") or "").strip()
        if not clip_id:
            continue
        score = item.get("score")
        try:
            score_val = float(score)
        except (TypeError, ValueError):
            continue
        reason = str(item.get("reason") or "").strip()
        trim = item.get("trim_suggestion")
        trim_confidence = item.get("trim_confidence")
        if trim_confidence is None and isinstance(trim, dict):
            trim_confidence = trim.get("confidence")
        trim_confidence_val = None
        if trim_confidence is not None:
            try:
                trim_confidence_val = float(trim_confidence)
            except (TypeError, ValueError):
                trim_confidence_val = None
        results.append(
            {
                "id": clip_id,
                "score": max(0.0, min(100.0, score_val)),
                "reason": reason,
                "trim_suggestion": trim if isinstance(trim, dict) else None,
                "trim_confidence": trim_confidence_val,
            }
        )

    if not results:
        raise DeepseekClientError("Deepseek returned no usable scores")

    return results
