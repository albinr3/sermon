"""Shared LLM prompts.

Single source of truth so Deepseek/OpenAI use identical system/user prompts.
"""

from __future__ import annotations

import json


def scoring_system_prompt() -> str:
    return (
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


def scoring_user_prompt(prompt_candidates: list[dict]) -> str:
    return (
        "Candidates JSON:\n"
        f"{json.dumps(prompt_candidates, ensure_ascii=True)}\n\n"
        "Return a JSON array with one entry per candidate id."
    )


def selection_system_prompt(*, target_count: int) -> str:
    return (
        "Eres un experto en identificar MEJORES momentos de sermones para redes sociales. "
        "Selecciona los 10 MEJORES de estos candidatos basandote en: "
        "1. IMPACTO EMOCIONAL, 2. MENSAJE COMPLETO, 3. AUTONOMIA, "
        "4. VIRALIDAD, 5. VARIEDAD. "
        "Devuelve SOLO JSON (sin markdown) como una lista de objetos con: "
        "id, score (0-100), reason. "
        "Devuelve exactamente {target_count} resultados si es posible."
    ).format(target_count=target_count)


def selection_user_prompt(*, sermon_context: str, prompt_candidates: list[dict]) -> str:
    sermon_context = sermon_context or ""
    return (
        "Contexto del sermon (primeros 2000 chars):\n"
        f"{sermon_context}\n\n"
        "Candidates JSON:\n"
        f"{json.dumps(prompt_candidates, ensure_ascii=True)}\n\n"
        "Return a JSON array with one entry per selected candidate id."
    )


def full_context_system_prompt() -> str:
    return (
        "Eres un experto en crear clips virales de sermones para redes sociales.\n\n"
        "TAREA: Lee este sermon COMPLETO y genera 10-20 clips optimos.\n\n"
        "CRITERIOS DE SELECCION:\n"
        "1. HOOK FUERTE (0-25 pts): Inicia con pregunta, declaracion impactante o estadistica\n"
        "2. MENSAJE AUTONOMO (0-25 pts): Se entiende sin contexto previo, tiene conclusion clara\n"
        "3. APLICABILIDAD (0-20 pts): Relevante para vida diaria, accionable\n"
        "4. IMPACTO EMOCIONAL (0-20 pts): Inspira, conmueve, desafia o motiva\n"
        "5. VIRALIDAD (0-10 pts): Potencial de ser compartido en redes sociales\n\n"
        "REQUISITOS TECNICOS:\n"
        "- Duracion ideal: 45-90 segundos (minimo 30s, maximo 120s)\n"
        "- Inicio y fin en puntos naturales (no cortar palabras/frases)\n"
        "- Variedad: Cubre diferentes temas del sermon\n"
        "- Prioriza momentos con narrativa completa (inicio-desarrollo-conclusion)\n\n"
        "EVITA:\n"
        "- Clips que requieren contexto previo\n"
        "- Momentos que terminan abruptamente\n"
        "- Contenido exclusivamente doctrinal sin aplicacion\n"
        "- Clips muy cortos (<30s) o muy largos (>120s)\n\n"
        "FORMATO DE RESPUESTA (solo JSON, sin markdown):\n"
        "[\n"
        '  {"start_sec": numero, "end_sec": numero, "score": 0-100, "reason": "explicacion", "theme": "tema"}\n'
        "]\n\n"
        "Genera 10-20 clips que cumplan estos criterios."
    )


def full_context_user_prompt(*, title: str, preacher: str, duration_label: str, transcript: str) -> str:
    return (
        f"SERMON COMPLETO:\n"
        f"Titulo: {title}\n"
        f"Predicador: {preacher}\n"
        f"Duracion: {duration_label}\n\n"
        f"TRANSCRIPCION CON TIMESTAMPS:\n"
        f"{transcript}\n\n"
        "Analiza todo el sermon y devuelve 10-20 clips en formato JSON."
    )


def windows_system_prompt(*, count: int) -> str:
    return (
        "Eres experto en clips virales. Analiza {count} ventanas y selecciona las "
        "10-12 MEJORES basandote en: HOOK, MENSAJE AUTONOMO, IMPACTO EMOCIONAL, "
        "APLICABILIDAD, VIRALIDAD. Devuelve SOLO JSON (sin markdown) como una lista "
        "de objetos con: window_id, score (0-100), reason, theme, timing_adjustment "
        "(start_offset_sec, end_offset_sec, confidence). Usa confidence 0-1."
    ).format(count=count)


def windows_user_prompt(*, sermon_title: str, sermon_intro: str, prompt_windows: list[dict]) -> str:
    return (
        "Sermon context:\n"
        f"Title: {sermon_title}\n"
        f"Intro: {sermon_intro}\n\n"
        "Windows JSON:\n"
        f"{json.dumps(prompt_windows, ensure_ascii=True)}\n\n"
        "Selecciona las mejores."
    )
