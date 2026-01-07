from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp


@dataclass
class VideoMetadata:
    width: int
    height: int
    fps: float


def get_video_metadata(video_path: str) -> VideoMetadata | None:
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return None
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    capture.release()
    if width <= 0 or height <= 0:
        return None
    return VideoMetadata(width=width, height=height, fps=fps)


def detect_face_track(
    video_path: str,
    target_fps: float = 2.0,
    smooth_window: int = 5,
) -> list[tuple[int, float]]:
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return []

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    if fps <= 0:
        fps = 30.0
    frame_interval = max(1, int(round(fps / target_fps)))

    face_detection = mp.solutions.face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5
    )

    track: list[tuple[int, float]] = []
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % frame_interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb)
            if results.detections:
                best = max(
                    results.detections,
                    key=lambda detection: detection.score[0]
                    if detection.score
                    else 0.0,
                )
                bbox = best.location_data.relative_bounding_box
                x_center = float(bbox.xmin + bbox.width / 2.0)
                x_center = min(1.0, max(0.0, x_center))
                t_ms = int((frame_index / fps) * 1000)
                track.append((t_ms, x_center))
        frame_index += 1

    capture.release()
    face_detection.close()
    return smooth_track(track, smooth_window)


def smooth_track(
    track: list[tuple[int, float]], window_size: int = 5
) -> list[tuple[int, float]]:
    if window_size <= 1 or len(track) < 2:
        return track
    smoothed: list[tuple[int, float]] = []
    for index, (t_ms, _) in enumerate(track):
        start = max(0, index - window_size + 1)
        window = track[start : index + 1]
        avg = sum(value for _, value in window) / len(window)
        smoothed.append((t_ms, avg))
    return smoothed


def get_center_at(
    track: list[tuple[int, float]], t_ms: int, default_center: float = 0.5
) -> float:
    if not track:
        return default_center
    if t_ms <= track[0][0]:
        return track[0][1]
    if t_ms >= track[-1][0]:
        return track[-1][1]
    for index in range(1, len(track)):
        if track[index][0] >= t_ms:
            t0, x0 = track[index - 1]
            t1, x1 = track[index]
            if t1 == t0:
                return x1
            ratio = (t_ms - t0) / (t1 - t0)
            return x0 + (x1 - x0) * ratio
    return track[-1][1]


def build_segment_centers(
    track: list[tuple[int, float]],
    duration_ms: int,
    segment_ms: int = 500,
    default_center: float = 0.5,
) -> list[tuple[int, float]]:
    if duration_ms <= 0:
        return []
    centers: list[tuple[int, float]] = []
    for t_ms in range(0, duration_ms, segment_ms):
        centers.append((t_ms, get_center_at(track, t_ms, default_center)))
    return centers


def compute_scaled_dims(
    width: int,
    height: int,
    target_width: int = 1080,
    target_height: int = 1920,
) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        return target_width, target_height
    input_ratio = width / height
    target_ratio = target_width / target_height
    if input_ratio >= target_ratio:
        scale_h = target_height
        scale_w = int(round(width * (target_height / height)))
    else:
        scale_w = target_width
        scale_h = int(round(height * (target_width / width)))
    return max(target_width, scale_w), max(target_height, scale_h)


def compute_crop_x(center_norm: float, scale_width: int, crop_width: int = 1080) -> int:
    center_px = center_norm * scale_width
    raw = int(round(center_px - crop_width / 2))
    return max(0, min(scale_width - crop_width, raw))
