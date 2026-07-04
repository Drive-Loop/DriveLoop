from __future__ import annotations

from driveloop.perception_metric_manifest import build_perception_metric_manifest
from driveloop.perception_video import PerceptionVideoEvaluator
from driveloop.schema import Generation


def detection(frame_index: int, confidence: float = 0.9) -> dict:
    return {
        "frame_index": frame_index,
        "label": "motorcycle",
        "confidence": confidence,
        "box": [10 + frame_index, 10, 30 + frame_index, 30],
    }


def detection_payload(frame_count: int = 4) -> dict:
    return {
        "frame_count": frame_count,
        "frames": [
            {"frame_index": frame_index, "detections": [detection(frame_index)]}
            for frame_index in range(frame_count)
        ],
    }


def test_manifest_normalizes_perception_video_eval_report():
    generation = Generation(
        iteration=0,
        prompt="night urban road with a visible motorcycle cut-in",
        artifacts={"video": "candidate.mp4"},
        metadata={
            "target_labels": ["motorcycle"],
            "perception_detections": detection_payload(),
        },
    )
    report = PerceptionVideoEvaluator(target_labels=["motorcycle"], pass_threshold=0.8).build_report(generation)

    manifest = build_perception_metric_manifest(report, source="artifact")

    assert manifest["schema_version"] == "driveloop_perception_metric_manifest.v0"
    assert manifest["available"] is True
    assert manifest["source"] == "artifact"
    assert manifest["perception_claim"] == "measured_passed"
    assert manifest["semantic_success_claim"] == "not_proven_by_perception_metrics_alone"
    assert manifest["measured"] is True
    assert manifest["passed"] is True
    assert manifest["metrics_complete"] is True
    assert manifest["metrics"]["Q_cov"] == 1.0
    assert manifest["metrics"]["Q_track"] == 1.0
    assert manifest["claim_boundary"]["perception_metric_manifest_is_not_video_semantic_success"] is True


def test_manifest_reads_prefixed_composite_runner_metrics():
    payload = {
        "score": 0.91,
        "metrics": {
            "1_PerceptionVideoEvaluator_perception_measured": 1.0,
            "1_PerceptionVideoEvaluator_Q_cov": 1.0,
            "1_PerceptionVideoEvaluator_Q_conf": 0.92,
            "1_PerceptionVideoEvaluator_Q_track": 1.0,
            "1_PerceptionVideoEvaluator_Q_id": 1.0,
            "1_PerceptionVideoEvaluator_Q_box": 0.84,
        },
        "diagnosis": {"passed": True, "reasons": []},
    }

    manifest = build_perception_metric_manifest(payload, source="attempt_history")

    assert manifest["perception_claim"] == "measured_passed"
    assert manifest["score"] == 0.91
    assert manifest["metrics"]["Q_conf"] == 0.92
    assert manifest["metric_source_keys"]["Q_cov"] == "1_PerceptionVideoEvaluator_Q_cov"
    assert manifest["source_metric_prefixes"] == ["1_PerceptionVideoEvaluator"]


def test_manifest_keeps_not_measured_as_negative_evidence():
    generation = Generation(
        iteration=0,
        prompt="night urban road with a visible motorcycle cut-in",
        artifacts={"video": "candidate.mp4"},
    )
    report = PerceptionVideoEvaluator(target_labels=["motorcycle"]).build_report(generation)

    manifest = build_perception_metric_manifest(report, source="artifact")

    assert manifest["available"] is True
    assert manifest["perception_claim"] == "not_measured"
    assert manifest["measured"] is False
    assert manifest["passed"] is False
    assert manifest["metrics_complete"] is False
    assert manifest["missing_metrics"] == ["Q_cov", "Q_conf", "Q_track", "Q_id", "Q_box"]
    assert manifest["claim_boundary"]["not_measured_is_valid_negative_evidence"] is True
