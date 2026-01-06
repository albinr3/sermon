def ms_to_srt_time(ms: int) -> str:
    total_ms = max(ms, 0)
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    seconds = (total_ms % 60_000) // 1000
    milliseconds = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def build_srt(segments: list[tuple[int, int, str]]) -> str:
    lines = []
    for index, (start_ms, end_ms, text) in enumerate(segments, start=1):
        safe_end = max(end_ms, start_ms + 1)
        lines.append(str(index))
        lines.append(f"{ms_to_srt_time(start_ms)} --> {ms_to_srt_time(safe_end)}")
        lines.append(text.strip())
        lines.append("")
    return "\n".join(lines)
