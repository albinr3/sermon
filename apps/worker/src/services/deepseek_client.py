import json
import logging
from typing import Any

import requests

from src.services.llm_prompts import (
    full_context_system_prompt,
    full_context_user_prompt,
    scoring_system_prompt,
    scoring_user_prompt,
    selection_system_prompt,
    selection_user_prompt,
    windows_system_prompt,
    windows_user_prompt,
)

logger = logging.getLogger(__name__)

PROMPT_COST_PER_1M = 0.14
COMPLETION_COST_PER_1M = 0.28
FULL_CONTEXT_MAX_CHARS = 240_000


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


def _truncate_full_text(text: str, limit: int = FULL_CONTEXT_MAX_CHARS) -> str:
    if len(text) <= limit:
        return text
    if limit < 1000:
        return text[:limit]
    sep = "\n...\n"
    head_len = max(1000, (limit - len(sep)) // 2)
    tail_len = max(1000, limit - len(sep) - head_len)
    head = text[:head_len]
    tail = text[-tail_len:]
    return f"{head}{sep}{tail}"


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


def _get_usage_value(usage: dict, keys: list[str]) -> int | None:
    for key in keys:
        if key in usage and usage.get(key) is not None:
            try:
                return int(usage.get(key))
            except (TypeError, ValueError):
                return None
    return None


def _extract_token_usage(payload: dict) -> dict:
    usage = payload.get("usage") or {}
    prompt_tokens = _get_usage_value(usage, ["prompt_tokens", "input_tokens"]) or 0
    completion_tokens = _get_usage_value(
        usage, ["completion_tokens", "output_tokens"]
    ) or 0
    total_tokens = _get_usage_value(usage, ["total_tokens"])
    if total_tokens is None:
        total_tokens = prompt_tokens + completion_tokens
    output_tokens = _get_usage_value(usage, ["output_tokens"])
    if output_tokens is None:
        output_tokens = completion_tokens
    cache_hit_tokens = _get_usage_value(
        usage,
        [
            "prompt_cache_hit_tokens",
            "cache_hit_tokens",
            "cache_hit",
        ],
    )
    cache_miss_tokens = _get_usage_value(
        usage,
        [
            "prompt_cache_miss_tokens",
            "cache_miss_tokens",
            "cache_miss",
        ],
    )
    estimated_cost_usd = (
        (prompt_tokens / 1_000_000.0) * PROMPT_COST_PER_1M
        + (completion_tokens / 1_000_000.0) * COMPLETION_COST_PER_1M
    )
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "output_tokens": output_tokens,
        "cache_hit_tokens": cache_hit_tokens,
        "cache_miss_tokens": cache_miss_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimated_cost_usd,
    }


def _format_usage_value(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _log_token_usage(label: str, token_usage: dict) -> None:
    logger.info(
        "%s tokens - prompt=%s output=%s total=%s cache_hit=%s cache_miss=%s cost_usd=%.6f",
        label,
        token_usage.get("prompt_tokens", 0),
        token_usage.get("output_tokens", token_usage.get("completion_tokens", 0)),
        token_usage.get("total_tokens", 0),
        _format_usage_value(token_usage.get("cache_hit_tokens")),
        _format_usage_value(token_usage.get("cache_miss_tokens")),
        token_usage.get("estimated_cost_usd", 0.0),
    )


def score_clip_candidates(
    candidates: list[dict],
    *,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    timeout: float = 30.0,
) -> dict:
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

    system_prompt = scoring_system_prompt()
    user_prompt = scoring_user_prompt(prompt_candidates)

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

    token_usage = _extract_token_usage(data)
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

    _log_token_usage("Deepseek scoring", token_usage)
    return {"clips": results, "token_usage": token_usage}


def select_best_clips(
    candidates: list[dict],
    sermon_context: str,
    *,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    target_count: int = 10,
    timeout: float = 30.0,
) -> dict:
    if not api_key or not api_key.strip():
        raise DeepseekClientError("Deepseek API key not configured")
    if not base_url or not base_url.strip():
        raise DeepseekClientError("Deepseek base URL not configured")
    if not model or not model.strip():
        raise DeepseekClientError("Deepseek model not configured")

    prompt_candidates = [
        {"id": item["id"], "text": item.get("text", "")} for item in candidates
    ]
    sermon_context = sermon_context or ""

    system_prompt = selection_system_prompt(target_count=target_count)
    user_prompt = selection_user_prompt(
        sermon_context=sermon_context,
        prompt_candidates=prompt_candidates,
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

    token_usage = _extract_token_usage(data)
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
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            continue
        clip_id = str(item.get("id") or "").strip()
        if not clip_id:
            continue
        score = item.get("score")
        score_val = None
        if score is not None:
            try:
                score_val = float(score)
            except (TypeError, ValueError):
                score_val = None
        if score_val is None:
            score_val = float(max(0, 100 - index))
        reason = str(item.get("reason") or "").strip()
        results.append(
            {
                "id": clip_id,
                "score": max(0.0, min(100.0, score_val)),
                "reason": reason,
            }
        )

    if not results:
        raise DeepseekClientError("Deepseek returned no usable selections")

    _log_token_usage("Deepseek selection", token_usage)
    return {"clips": results, "token_usage": token_usage}


def generate_from_full_transcript(
    full_text: str,
    sermon_metadata: dict,
    *,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    timeout: float = 120.0,
) -> dict:
    if not api_key or not api_key.strip():
        raise DeepseekClientError("Deepseek API key not configured")
    if not base_url or not base_url.strip():
        raise DeepseekClientError("Deepseek base URL not configured")
    if not model or not model.strip():
        raise DeepseekClientError("Deepseek model not configured")

    title = str(sermon_metadata.get("title") or "")
    preacher = str(sermon_metadata.get("preacher") or "")
    duration_sec = sermon_metadata.get("duration_sec")
    duration_label = ""
    if duration_sec is not None:
        try:
            duration_label = f"{float(duration_sec):.1f}s"
        except (TypeError, ValueError):
            duration_label = ""

    trimmed_text = _truncate_full_text(full_text)
    system_prompt = full_context_system_prompt()
    user_prompt = full_context_user_prompt(
        title=title,
        preacher=preacher,
        duration_label=duration_label,
        transcript=trimmed_text,
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

    token_usage = _extract_token_usage(data)
    content = _extract_message_content(data)
    try:
        parsed = _coerce_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("Deepseek content not JSON: %s", content[:500])
        raise DeepseekClientError("Deepseek content invalid JSON") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("clips") or parsed.get("results") or []
    if not isinstance(parsed, list):
        raise DeepseekClientError("Deepseek JSON must be a list")

    results: list[dict] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            continue
        start_sec = item.get("start_sec")
        end_sec = item.get("end_sec")
        try:
            start_sec_val = float(start_sec)
            end_sec_val = float(end_sec)
        except (TypeError, ValueError):
            continue
        if end_sec_val <= start_sec_val:
            continue
        score = item.get("score")
        score_val = None
        if score is not None:
            try:
                score_val = float(score)
            except (TypeError, ValueError):
                score_val = None
        if score_val is None:
            score_val = float(max(0, 100 - index))
        reason = str(item.get("reason") or "").strip()
        theme = str(item.get("theme") or "").strip()
        results.append(
            {
                "start_sec": start_sec_val,
                "end_sec": end_sec_val,
                "score": max(0.0, min(100.0, score_val)),
                "reason": reason,
                "theme": theme,
            }
        )

    if not results:
        raise DeepseekClientError("Deepseek returned no usable clips")

    _log_token_usage("Deepseek full-context", token_usage)
    return {"clips": results, "token_usage": token_usage}


def generate_clip_suggestions(
    windows: list[dict],
    sermon_context: dict,
    *,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    timeout: float = 30.0,
) -> dict:
    if not api_key or not api_key.strip():
        raise DeepseekClientError("Deepseek API key not configured")
    if not base_url or not base_url.strip():
        raise DeepseekClientError("Deepseek base URL not configured")
    if not model or not model.strip():
        raise DeepseekClientError("Deepseek model not configured")

    prompt_windows = [
        {
            "id": item.get("id"),
            "start_ms": item.get("start_ms"),
            "end_ms": item.get("end_ms"),
            "text": _trim_text(item.get("text", ""), limit=2200),
        }
        for item in windows
    ]
    sermon_title = str(sermon_context.get("title") or "")
    sermon_intro = str(sermon_context.get("intro") or "")

    system_prompt = windows_system_prompt(count=len(prompt_windows))
    user_prompt = windows_user_prompt(
        sermon_title=sermon_title,
        sermon_intro=sermon_intro,
        prompt_windows=prompt_windows,
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

    token_usage = _extract_token_usage(data)
    content = _extract_message_content(data)
    try:
        parsed = _coerce_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("Deepseek content not JSON: %s", content[:500])
        raise DeepseekClientError("Deepseek content invalid JSON") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("clips") or parsed.get("results") or []
    if not isinstance(parsed, list):
        raise DeepseekClientError("Deepseek JSON must be a list")

    results: list[dict] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            continue
        window_id = str(item.get("window_id") or item.get("id") or "").strip()
        if not window_id:
            continue
        score = item.get("score")
        score_val = None
        if score is not None:
            try:
                score_val = float(score)
            except (TypeError, ValueError):
                score_val = None
        if score_val is None:
            score_val = float(max(0, 100 - index))
        reason = str(item.get("reason") or "").strip()
        theme = str(item.get("theme") or "").strip()
        timing_adjustment = item.get("timing_adjustment")
        results.append(
            {
                "window_id": window_id,
                "score": max(0.0, min(100.0, score_val)),
                "reason": reason,
                "theme": theme,
                "timing_adjustment": timing_adjustment
                if isinstance(timing_adjustment, dict)
                else None,
            }
        )

    if not results:
        raise DeepseekClientError("Deepseek returned no usable selections")

    _log_token_usage("Deepseek generation", token_usage)
    return {"clips": results, "token_usage": token_usage}
