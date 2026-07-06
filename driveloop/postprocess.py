"""Verified post-processing operators P_post (paper Eq. 14).

Only effects registered here are treated as executable; unknown effect tags
are reported as skipped so the loop never silently claims an unapplied
control.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List


def apply_fog_overlay(frame: Any, intensity: float = 0.35) -> Any:
    import cv2
    import numpy as np

    fog = np.full_like(frame, 255)
    blended = cv2.addWeighted(frame, 1.0 - intensity, fog, intensity, 0)
    return cv2.GaussianBlur(blended, (5, 5), 0)


EFFECTS = {
    "fog_overlay": apply_fog_overlay,
}


def apply_postprocess_effects(
    video_path: str | Path,
    effects: Iterable[str],
    output_path: str | Path | None = None,
) -> Dict[str, Any]:
    import cv2

    video_path = Path(video_path)
    requested = list(effects)
    applied = [e for e in requested if e in EFFECTS]
    skipped = [e for e in requested if e not in EFFECTS]

    if not applied:
        return {
            "schema_version": "driveloop_postprocess_report.v0",
            "applied": [],
            "skipped_unknown": skipped,
            "output": str(video_path),
            "claim_boundary": "no executable post-process effect was applied",
        }

    output_path = Path(output_path) if output_path else video_path.with_name(video_path.stem + "_post.mp4")
    capture = cv2.VideoCapture(str(video_path))
    fps = capture.get(cv2.CAP_PROP_FPS) or 4.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    frame_count = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            for effect in applied:
                frame = EFFECTS[effect](frame)
            writer.write(frame)
            frame_count += 1
    finally:
        capture.release()
        writer.release()

    return {
        "schema_version": "driveloop_postprocess_report.v0",
        "applied": applied,
        "skipped_unknown": skipped,
        "frame_count": frame_count,
        "output": str(output_path),
        "claim_boundary": "post-processing modifies pixels only; it is not semantic-success evidence",
    }
