import json
import logging
from typing import Any

import requests

from src.services.llm_prompts import (
    full_context_system_prompt,
    full_context_system_prompt_v2,
    full_context_system_prompt_v3,
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


class OpenAIClientError(RuntimeError):
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
        raise OpenAIClientError("OpenAI response missing choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise OpenAIClientError("OpenAI response missing content")
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
    # Logs de tokens deshabilitados
    pass


def score_clip_candidates(
    candidates: list[dict],
    *,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    timeout: float = 30.0,
) -> dict:
    if not api_key or not api_key.strip():
        raise OpenAIClientError("OpenAI API key not configured")
    if not base_url or not base_url.strip():
        raise OpenAIClientError("OpenAI base URL not configured")
    if not model or not model.strip():
        raise OpenAIClientError("OpenAI model not configured")

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
        raise OpenAIClientError("OpenAI request failed") from exc

    if response.status_code >= 300:
        logger.warning(
            "OpenAI HTTP error %s: %s", response.status_code, response.text[:500]
        )
        raise OpenAIClientError(f"OpenAI HTTP error {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("OpenAI response not JSON: %s", response.text[:500])
        raise OpenAIClientError("OpenAI response invalid JSON") from exc

    token_usage = _extract_token_usage(data)
    content = _extract_message_content(data)
    try:
        parsed = _coerce_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("OpenAI content not JSON: %s", content[:500])
        raise OpenAIClientError("OpenAI content invalid JSON") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("results") or parsed.get("clips") or []
    if not isinstance(parsed, list):
        raise OpenAIClientError("OpenAI JSON must be a list")

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
        raise OpenAIClientError("OpenAI returned no usable scores")

    _log_token_usage("OpenAI scoring", token_usage)
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
        raise OpenAIClientError("OpenAI API key not configured")
    if not base_url or not base_url.strip():
        raise OpenAIClientError("OpenAI base URL not configured")
    if not model or not model.strip():
        raise OpenAIClientError("OpenAI model not configured")

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
        raise OpenAIClientError("OpenAI request failed") from exc

    if response.status_code >= 300:
        logger.warning(
            "OpenAI HTTP error %s: %s", response.status_code, response.text[:500]
        )
        raise OpenAIClientError(f"OpenAI HTTP error {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("OpenAI response not JSON: %s", response.text[:500])
        raise OpenAIClientError("OpenAI response invalid JSON") from exc

    token_usage = _extract_token_usage(data)
    content = _extract_message_content(data)
    try:
        parsed = _coerce_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("OpenAI content not JSON: %s", content[:500])
        raise OpenAIClientError("OpenAI content invalid JSON") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("results") or parsed.get("clips") or []
    if not isinstance(parsed, list):
        raise OpenAIClientError("OpenAI JSON must be a list")

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
        raise OpenAIClientError("OpenAI returned no usable selections")

    _log_token_usage("OpenAI selection", token_usage)
    return {"clips": results, "token_usage": token_usage}


def generate_from_full_transcript(
    full_text: str,
    sermon_metadata: dict,
    *,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    timeout: float = 120.0,
    prompt_version: str = "v1",
) -> dict:
    if not api_key or not api_key.strip():
        raise OpenAIClientError("OpenAI API key not configured")
    if not base_url or not base_url.strip():
        raise OpenAIClientError("OpenAI base URL not configured")
    if not model or not model.strip():
        raise OpenAIClientError("OpenAI model not configured")

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
    if prompt_version == "v3":
        system_prompt = full_context_system_prompt_v3()
    elif prompt_version == "v2":
        system_prompt = full_context_system_prompt_v2()
    else:
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
    }

    # Calcular timeout dinámico basado en el tamaño del payload
    # Base: 120s, +60s por cada 10,000 caracteres adicionales, máximo 600s (10 min)
    payload_size_chars = len(trimmed_text) + len(system_prompt)
    dynamic_timeout = 120.0 + (payload_size_chars / 10000.0) * 60.0
    dynamic_timeout = min(max(dynamic_timeout, timeout), 600.0)  # Clamp entre timeout y 600s
    
    logger.info(
        "OpenAI full-context timeout calculation: payload_size_chars=%d, base_timeout=%.1f, dynamic_timeout=%.1f",
        payload_size_chars, timeout, dynamic_timeout
    )

    endpoint = _resolve_endpoint(base_url)
    try:
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=dynamic_timeout,
        )
    except requests.RequestException as exc:
        # Log detallado del error para debugging
        error_type = type(exc).__name__
        error_msg = str(exc)
        is_timeout = isinstance(exc, requests.Timeout)
        is_connection = isinstance(exc, requests.ConnectionError)
        logger.error(
            "OpenAI request failed (generate_from_full_transcript): type=%s, message=%s, is_timeout=%s, is_connection=%s, endpoint=%s, timeout_used=%.1f, payload_size_chars=%d",
            error_type, error_msg, is_timeout, is_connection, endpoint, dynamic_timeout, payload_size_chars
        )
        raise OpenAIClientError(f"OpenAI request failed: {error_type}: {error_msg}") from exc

    if response.status_code >= 300:
        logger.error(
            "OpenAI HTTP error (generate_from_full_transcript): status=%s, response=%s", 
            response.status_code, response.text[:1000]
        )
        raise OpenAIClientError(f"OpenAI HTTP error {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("OpenAI response not JSON: %s", response.text[:500])
        raise OpenAIClientError("OpenAI response invalid JSON") from exc

    token_usage = _extract_token_usage(data)
    content = _extract_message_content(data)
    try:
        parsed = _coerce_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("OpenAI content not JSON: %s", content[:500])
        raise OpenAIClientError("OpenAI content invalid JSON") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("clips") or parsed.get("results") or []
    if not isinstance(parsed, list):
        raise OpenAIClientError("OpenAI JSON must be a list")

    results: list[dict] = []
    skipped_count = 0
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            skipped_count += 1
            logger.debug("OpenAI item %d skipped: not a dict, type=%s", index, type(item).__name__)
            continue
        
        # v3 usa start_u/end_u (utterance IDs)
        if prompt_version == "v3":
            start_u = item.get("start_u")
            end_u = item.get("end_u")
            try:
                start_u_val = int(start_u) if start_u is not None else None
                end_u_val = int(end_u) if end_u is not None else None
                if start_u_val is not None and end_u_val is not None:
                    if end_u_val <= start_u_val:
                        skipped_count += 1
                        logger.debug("OpenAI item %d skipped: end_u (%d) <= start_u (%d)", index, end_u_val, start_u_val)
                        continue
            except (TypeError, ValueError) as exc:
                start_u_val = None
                end_u_val = None
                skipped_count += 1
                logger.debug("OpenAI item %d skipped: invalid start_u/end_u: %s", index, exc)
            
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
            
            result_item = {
                "score": max(0.0, min(100.0, score_val)),
                "reason": reason,
                "theme": theme,
            }
            if start_u_val is not None and end_u_val is not None:
                result_item["start_u"] = start_u_val
                result_item["end_u"] = end_u_val
                logger.debug("OpenAI item %d (v3): start_u=%d, end_u=%d, score=%.1f", index, start_u_val, end_u_val, result_item["score"])
            else:
                logger.warning("OpenAI item %d skipped (v3): missing start_u or end_u (start_u=%s, end_u=%s, item_keys=%s)", 
                             index, start_u, end_u, list(item.keys()))
                continue
            results.append(result_item)
            continue
        
        # v1/v2: start_sec/end_sec o quote_start/quote_end
        start_sec = item.get("start_sec")
        end_sec = item.get("end_sec")
        quote_start = item.get("quote_start")
        quote_end = item.get("quote_end")
        try:
            start_sec_val = None
            end_sec_val = None
            if start_sec is not None and end_sec is not None:
                start_sec_val = float(start_sec)
                end_sec_val = float(end_sec)
                if end_sec_val <= start_sec_val:
                    continue
        except (TypeError, ValueError):
            pass
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
        quote_start_str = str(quote_start).strip() if quote_start is not None else None
        quote_end_str = str(quote_end).strip() if quote_end is not None else None
        result_item = {
            "score": max(0.0, min(100.0, score_val)),
            "reason": reason,
            "theme": theme,
        }
        if start_sec_val is not None and end_sec_val is not None:
            result_item["start_sec"] = start_sec_val
            result_item["end_sec"] = end_sec_val
        if quote_start_str:
            result_item["quote_start"] = quote_start_str
        if quote_end_str:
            result_item["quote_end"] = quote_end_str
        results.append(result_item)

    if not results:
        logger.error("OpenAI returned no usable clips (generate_from_full_transcript): parsed_len=%d, skipped=%d, results_len=0, prompt_version=%s", len(parsed), skipped_count, prompt_version)
        raise OpenAIClientError("OpenAI returned no usable clips")

    logger.info("OpenAI full-context (generate_from_full_transcript): parsed %d items, returned %d usable clips", len(parsed), len(results))
    _log_token_usage("OpenAI full-context", token_usage)
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
        raise OpenAIClientError("OpenAI API key not configured")
    if not base_url or not base_url.strip():
        raise OpenAIClientError("OpenAI base URL not configured")
    if not model or not model.strip():
        raise OpenAIClientError("OpenAI model not configured")

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
        raise OpenAIClientError("OpenAI request failed") from exc

    if response.status_code >= 300:
        logger.warning(
            "OpenAI HTTP error %s: %s", response.status_code, response.text[:500]
        )
        raise OpenAIClientError(f"OpenAI HTTP error {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("OpenAI response not JSON: %s", response.text[:500])
        raise OpenAIClientError("OpenAI response invalid JSON") from exc

    token_usage = _extract_token_usage(data)
    content = _extract_message_content(data)
    try:
        parsed = _coerce_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("OpenAI content not JSON: %s", content[:500])
        raise OpenAIClientError("OpenAI content invalid JSON") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("clips") or parsed.get("results") or []
    if not isinstance(parsed, list):
        raise OpenAIClientError("OpenAI JSON must be a list")

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
        raise OpenAIClientError("OpenAI returned no usable selections")

    _log_token_usage("OpenAI generation", token_usage)
    return {"clips": results, "token_usage": token_usage}
