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
        "1. HOOK FUERTE (0-35 pts):\n"
        "   EXCELENTES (35 pts):\n"
        "   - Pregunta provocadora\n"
        "   - Declaración contraintuitiva\n"
        "   - Verdad universal\n"
        "   - Analogía poderosa\n"
        "   \n"
        "   ACEPTABLES (20 pts):\n"
        "   - Declaración directa con promesa: 'La alegría que ofrece Jesús es diferente'\n"
        "   - Definición + implicación: 'Creer significa seguir, no es pasar al altar'\n"
        "   \n"
        "   MALOS (0 pts):\n"
        "   - 'Y entonces...'\n"
        "   - 'Como dije antes...'\n"
        "   - 'También es importante...'\n"
        "   - 'Ahora bien...'\n"
        "   - Cualquier cosa que requiera contexto previo\n\n"
        "2. UNA SOLA IDEA (0-25 pts):\n"
        "   - El clip debe desarrollar UNA idea completa\n"
        "   - NO intentar cubrir múltiples puntos\n"
        "   - Mensaje debe ser cristalino al terminar\n"
        "   - Test: ¿Puedo resumir este clip en 1 oración?\n\n"
        "3. CONCLUSION FUERTE (0-20 pts):\n"
        "   - Termina con frase memorable\n"
        "   - O con pregunta que invita reflexión\n"
        "   - O con llamado a la acción\n"
        "   - NO terminar en medio de pensamiento\n\n"
        "4. AUTONOMIA (0-15 pts):\n"
        "   - Se entiende SIN contexto previo\n"
        "   - No requiere haber visto el sermón\n"
        "   - No hace referencia a 'lo que dije antes'\n\n"
        "5. EMOCION (0-5 pts):\n"
        "   - Inspira, desafía o conmueve\n"
        "   - Conecta emocionalmente\n\n"
        "REQUISITOS TECNICOS:\n"
        "- Duracion ideal: 40-70 segundos (minimo 30s, maximo 120s)\n"
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


def full_context_system_prompt_v2() -> str:
    return (
        "Eres un experto en crear clips virales de sermones para redes sociales.\n\n"
        "TAREA: Lee este sermon COMPLETO y genera 10-20 clips optimos.\n\n"
        "CRITERIOS DE SELECCION:\n"
        "1. HOOK FUERTE (0-35 pts):\n"
        "   EXCELENTES (35 pts):\n"
        "   - Pregunta provocadora\n"
        "   - Declaración contraintuitiva\n"
        "   - Verdad universal\n"
        "   - Analogía poderosa\n"
        "   \n"
        "   ACEPTABLES (20 pts):\n"
        "   - Declaración directa con promesa: 'La alegría que ofrece Jesús es diferente'\n"
        "   - Definición + implicación: 'Creer significa seguir, no es pasar al altar'\n"
        "   \n"
        "   MALOS (0 pts):\n"
        "   - 'Y entonces...'\n"
        "   - 'Como dije antes...'\n"
        "   - 'También es importante...'\n"
        "   - 'Ahora bien...'\n"
        "   - Cualquier cosa que requiera contexto previo\n\n"
        "2. UNA SOLA IDEA (0-25 pts):\n"
        "   - El clip debe desarrollar UNA idea completa\n"
        "   - NO intentar cubrir múltiples puntos\n"
        "   - Mensaje debe ser cristalino al terminar\n"
        "   - Test: ¿Puedo resumir este clip en 1 oración?\n\n"
        "3. CONCLUSION FUERTE (0-20 pts):\n"
        "   - Termina con frase memorable\n"
        "   - O con pregunta que invita reflexión\n"
        "   - O con llamado a la acción\n"
        "   - NO terminar en medio de pensamiento\n\n"
        "4. AUTONOMIA (0-15 pts):\n"
        "   - Se entiende SIN contexto previo\n"
        "   - No requiere haber visto el sermón\n"
        "   - No hace referencia a 'lo que dije antes'\n\n"
        "5. EMOCION (0-5 pts):\n"
        "   - Inspira, desafía o conmueve\n"
        "   - Conecta emocionalmente\n\n"
        "REQUISITOS TECNICOS:\n"
        "- Duracion ideal: 40-70 segundos (minimo 30s, maximo 120s)\n"
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
        '  {"quote_start": "Las primeras 5-7 palabras exactas con las que empieza el clip", "quote_end": "Las últimas 5-7 palabras exactas con las que termina el clip", "score": 0-100, "reason": "explicacion", "theme": "tema"}\n'
        "]\n\n"
        "Genera 10-20 clips que cumplan estos criterios."
    )


def full_context_system_prompt_v3() -> str:
    return (
        "Eres un experto en crear clips virales de sermones para redes sociales.\n\n"
        "TAREA: Lee este sermon COMPLETO y genera 10-20 clips optimos.\n\n"
        "IMPORTANTE - FORMATO DEL TRANSCRIPT:\n"
        "El transcript viene con lineas en formato: [u{idx} {start_ms}-{end_ms}] {text}\n"
        "Donde 'u{idx}' es el ID de la utterance (oracion completa).\n"
        "Ejemplo: [u42 123400-127800] Esta es una oracion completa.\n\n"
        "REGLAS CRITICAS DE HOOK (start_u):\n"
        "- start_u DEBE ser una linea que funcione como HOOK por si sola.\n"
        "- HOOKS EXCELENTES: pregunta provocadora, verdad universal, declaracion contraintuitiva, analogia poderosa.\n"
        "- PROHIBIDO empezar con conectores: 'y', 'pero', 'entonces', 'ahora', 'como dije', 'como te dije', 'como te decia', 'tambien', 'ademas'.\n"
        "- PROHIBIDO empezar con frases que requieren contexto: 'y entonces...', 'ahora bien...', 'como dije antes...'.\n"
        "- Si una linea empieza con conector, NO la uses como start_u. Busca una linea anterior que sea hook fuerte.\n\n"
        "REGLAS CRITICAS DE CIERRE (end_u):\n"
        "- end_u DEBE ser una linea que funcione como CIERRE completo.\n"
        "- CIERRES EXCELENTES: mic-drop (frase memorable), punchline (conclusion impactante), tesis cerrada, pregunta final que invita reflexion.\n"
        "- PROHIBIDO terminar con conectores: 'y', 'pero', 'porque', 'entonces', 'asi que', 'así que', 'o sea', 'para que', 'cuando', 'si'.\n"
        "- PROHIBIDO terminar con frases abiertas: 'y...', 'pero...', 'porque...', 'entonces...', 'asi que...'.\n"
        "- Si una linea termina con conector o sin puntuacion de cierre (. ! ?), NO la uses como end_u. Busca una linea posterior que sea cierre limpio.\n\n"
        "CRITERIOS DE SELECCION:\n"
        "1. HOOK FUERTE (0-35 pts) - MAXIMA PRIORIDAD:\n"
        "   EXCELENTES (35 pts):\n"
        "   - Pregunta provocadora: '¿Cuándo fue la última vez que seguir a Jesús nos costó una relación?'\n"
        "   - Declaración contraintuitiva: 'Las armas que Dios nos proveyó, aunque parecen arcaicas, siguen funcionando'\n"
        "   - Verdad universal: 'Todos nacemos con un anhelo intenso de significación'\n"
        "   - Analogía poderosa: '¿Podría alguien construir un palacio y olvidarse del rey?'\n"
        "   \n"
        "   ACEPTABLES (20 pts):\n"
        "   - Declaración directa con promesa: 'La alegría que ofrece Jesús es diferente'\n"
        "   - Definición + implicación: 'Creer significa seguir, no es pasar al altar'\n"
        "   \n"
        "   MALOS (0 pts) - NO USAR:\n"
        "   - 'Y entonces...'\n"
        "   - 'Como dije antes...'\n"
        "   - 'También es importante...'\n"
        "   - 'Ahora bien...'\n"
        "   - Cualquier cosa que requiera contexto previo\n\n"
        "2. UNA SOLA IDEA (0-25 pts):\n"
        "   - El clip debe desarrollar UNA idea completa\n"
        "   - NO intentar cubrir múltiples puntos\n"
        "   - Mensaje debe ser cristalino al terminar\n"
        "   - Test: ¿Puedo resumir este clip en 1 oración?\n\n"
        "3. CONCLUSION FUERTE (0-20 pts) - MAXIMA PRIORIDAD:\n"
        "   - Termina con frase memorable (mic-drop)\n"
        "   - O con pregunta que invita reflexión\n"
        "   - O con llamado a la acción\n"
        "   - O con tesis cerrada y completa\n"
        "   - NO terminar en medio de pensamiento\n"
        "   - NO terminar con conectores o frases abiertas\n\n"
        "4. AUTONOMIA (0-15 pts):\n"
        "   - Se entiende SIN contexto previo\n"
        "   - No requiere haber visto el sermón\n"
        "   - No hace referencia a 'lo que dije antes'\n\n"
        "5. EMOCION (0-5 pts):\n"
        "   - Inspira, desafía o conmueve\n"
        "   - Conecta emocionalmente\n\n"
        "REQUISITOS TECNICOS:\n"
        "- Duracion ideal: 40-70 segundos (minimo 30s, maximo 120s)\n"
        "- Inicio y fin en puntos naturales (no cortar palabras/frases)\n"
        "- Variedad: Cubre diferentes temas del sermon\n"
        "- Prioriza momentos con narrativa completa (inicio-desarrollo-conclusion)\n\n"
        "EVITA:\n"
        "- Clips que requieren contexto previo\n"
        "- Momentos que terminan abruptamente\n"
        "- Contenido exclusivamente doctrinal sin aplicacion\n"
        "- Clips muy cortos (<30s) o muy largos (>120s)\n"
        "- Empezar con conectores o frases de relleno\n"
        "- Terminar con conectores o frases abiertas\n\n"
        "FORMATO DE RESPUESTA (solo JSON, sin markdown):\n"
        "[\n"
        '  {"start_u": 42, "end_u": 55, "score": 0-100, "reason": "explicacion", "theme": "tema"}\n'
        "]\n\n"
        "REGLAS CRITICAS:\n"
        "- start_u y end_u DEBEN ser enteros existentes en el transcript (IDs de utterances).\n"
        "- start_u < end_u (siempre).\n"
        "- La duracion aproximada (end_ms - start_ms) debe estar entre 30s y 120s (ideal 40-70s).\n"
        "- NO inventes IDs que no existan en el transcript.\n"
        "- Usa SOLO los IDs que ves en las lineas [u{idx} ...].\n"
        "- start_u DEBE ser un hook fuerte (no conectores).\n"
        "- end_u DEBE ser un cierre completo (no conectores, con puntuacion de cierre).\n\n"
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
