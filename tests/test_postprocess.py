import cv2
import numpy as np

from driveloop.postprocess import apply_postprocess_effects


def _write_video(path, n=4, value=40):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 4, (64, 64))
    for _ in range(n):
        writer.write(np.full((64, 64, 3), value, dtype=np.uint8))
    writer.release()


def test_fog_overlay_brightens_dark_video(tmp_path):
    src = tmp_path / "clip.mp4"
    _write_video(src)
    report = apply_postprocess_effects(src, ["fog_overlay"])
    assert report["applied"] == ["fog_overlay"]
    assert report["frame_count"] == 4
    cap = cv2.VideoCapture(report["output"])
    ok, frame = cap.read()
    cap.release()
    assert ok and float(frame.mean()) > 40.0


def test_unknown_effect_is_reported_not_applied(tmp_path):
    src = tmp_path / "clip.mp4"
    _write_video(src)
    report = apply_postprocess_effects(src, ["hologram_rain"])
    assert report["applied"] == []
    assert report["skipped_unknown"] == ["hologram_rain"]
    assert report["output"] == str(src)
