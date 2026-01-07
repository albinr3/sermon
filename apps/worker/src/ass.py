from __future__ import annotations


def _ms_to_ass_time(ms: int) -> str:
    total_ms = max(ms, 0)
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    seconds = (total_ms % 60_000) // 1000
    centiseconds = (total_ms % 1000) // 10
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def _wrap_text(text: str, max_words_per_line: int) -> str:
    safe = " ".join(text.replace("\n", " ").split())
    if max_words_per_line <= 0:
        return safe
    words = safe.split(" ")
    lines = []
    for index in range(0, len(words), max_words_per_line):
        lines.append(" ".join(words[index : index + max_words_per_line]))
    return r"\N".join(lines)


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def build_ass_from_segments(
    segments: list[tuple[int, int, str]], template_config: dict
) -> str:
    font = template_config.get("font", "Arial")
    font_size = int(template_config.get("font_size", 64))
    max_words_per_line = int(template_config.get("max_words_per_line", 4))
    y_pos = int(template_config.get("y_pos", 1500))
    highlight_mode = template_config.get("highlight_mode", "none")
    safe_margins = template_config.get("safe_margins", {}) or {}
    safe_top = int(safe_margins.get("top", 120))
    safe_bottom = int(safe_margins.get("bottom", 120))
    safe_left = int(safe_margins.get("left", 120))
    safe_right = int(safe_margins.get("right", 120))

    play_res_x = 1080
    play_res_y = 1920
    x_pos = _clamp(play_res_x / 2, safe_left, play_res_x - safe_right)
    y_pos = _clamp(y_pos, safe_top, play_res_y - safe_bottom)

    if highlight_mode == "word":
        # TODO: implement word-level highlights using ASS override tags.
        pass

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {play_res_x}",
        f"PlayResY: {play_res_y}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font},{font_size},&H00FFFFFF,&H000000FF,"
        "&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,3,1,5,20,20,20,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text",
    ]

    for start_ms, end_ms, text in segments:
        safe_end = max(end_ms, start_ms + 1)
        wrapped = _wrap_text(text, max_words_per_line)
        lines.append(
            "Dialogue: 0,"
            f"{_ms_to_ass_time(start_ms)},"
            f"{_ms_to_ass_time(safe_end)},"
            f"Default,,0,0,0,,{{\\pos({int(x_pos)},{int(y_pos)})}}{wrapped}"
        )

    return "\n".join(lines)
