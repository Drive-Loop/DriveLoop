import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from driveloop.composite_perception import CompositePerceptionVideoEvaluator
from driveloop.perception_video import Detection, PerceptionVideoEvaluator
from driveloop.schema import Generation


def _gen(frames_payload, frame_count=8):
    return Generation(
        iteration=0,
        prompt="a motorcycle cut-in at night",
        artifacts={},
        metadata={"perception_detections": {"frames": frames_payload, "frame_count": frame_count}},
    )


def _det_payload(frame_index, label="motorcycle", confidence=0.6, box=(10, 10, 40, 40)):
    return {"frame_index": frame_index, "label": label, "confidence": confidence, "box": list(box)}


def test_single_frame_support_zeroes_degenerate_components():
    evaluator = PerceptionVideoEvaluator(target_labels=["motorcycle"])
    frames = [{"frame_index": i, "detections": []} for i in range(8)]
    frames[3]["detections"] = [_det_payload(3)]
    ev = evaluator.evaluate(_gen(frames))
    assert ev.metrics["perception_target_support_frames"] == 1.0
    assert ev.metrics["Q_id"] == 0.0
    assert ev.metrics["Q_box"] == 0.0
    assert "insufficient_target_support_frames" in ev.diagnosis.reasons


def test_multi_frame_support_keeps_components():
    evaluator = PerceptionVideoEvaluator(target_labels=["motorcycle"])
    frames = [{"frame_index": i, "detections": []} for i in range(8)]
    frames[3]["detections"] = [_det_payload(3)]
    frames[4]["detections"] = [_det_payload(4, box=(12, 12, 42, 42))]
    ev = evaluator.evaluate(_gen(frames))
    assert ev.metrics["perception_target_support_frames"] == 2.0
    assert "insufficient_target_support_frames" not in ev.diagnosis.reasons
    assert ev.metrics["Q_id"] > 0.0


def test_zero_detections_do_not_trigger_guard():
    evaluator = PerceptionVideoEvaluator(target_labels=["motorcycle"])
    frames = [{"frame_index": i, "detections": []} for i in range(8)]
    ev = evaluator.evaluate(_gen(frames))
    assert ev.metrics["perception_target_support_frames"] == 0.0
    assert "insufficient_target_support_frames" not in ev.diagnosis.reasons


def _det(box, label="person", conf=0.6, frame=7):
    return Detection(frame_index=frame, label=label, confidence=conf, box=tuple(float(v) for v in box))


def test_baseline_subtraction_on_measured_m5_coordinates():
    # Real coordinates from the 2026-07-08 baseline-differential record:
    # baseline source object vs re-detection (subtract) vs new motorcycle (keep).
    evaluator = CompositePerceptionVideoEvaluator()
    baseline = [_det((160, 71, 228, 204), label="person", conf=0.65)]
    same_source = _det((165, 83, 222, 193), label="person", conf=0.43)
    new_motorcycle = _det((175, 159, 226, 207), label="motorcycle", conf=0.64)
    kept, removed = evaluator._subtract_baseline([same_source, new_motorcycle], baseline)
    assert removed == 1
    assert kept == [new_motorcycle]
    assert evaluator._iou_xyxy(same_source.box, baseline[0].box) >= 0.5
    assert evaluator._iou_xyxy(new_motorcycle.box, baseline[0].box) < 0.5


def test_subtraction_noop_without_baseline():
    evaluator = CompositePerceptionVideoEvaluator()
    d = _det((0, 0, 10, 10))
    kept, removed = evaluator._subtract_baseline([d], [])
    assert kept == [d] and removed == 0


def test_baseline_constructor_and_plumbing():
    evaluator = CompositePerceptionVideoEvaluator(baseline_video="/tmp/x.mp4", baseline_iou_threshold=0.6)
    assert evaluator.baseline_video == "/tmp/x.mp4"
    assert evaluator.baseline_iou_threshold == 0.6
    pipeline_src = (REPO_ROOT / "driveloop" / "experiment_pipeline.py").read_text(encoding="utf-8")
    assert "perception_baseline_video" in pipeline_src
    cli_src = (REPO_ROOT / "scripts" / "run_driveloop_experiment.py").read_text(encoding="utf-8")
    assert "--perception-baseline-video" in cli_src
