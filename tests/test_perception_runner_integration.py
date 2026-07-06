from __future__ import annotations

import json
import tempfile
from pathlib import Path

from driveloop import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.backends import MockGenerationBackend
from driveloop.evaluators import CompositeEvaluator, RuleBasedEvaluator
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


def test_runner_records_perception_metrics_in_attempt_history_jsonl():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        evaluator = CompositeEvaluator([
            RuleBasedEvaluator(),
            PerceptionVideoEvaluator(target_labels=["motorcycle"], pass_threshold=0.8, static_motion_threshold=0.0),
        ])
        result = DriveLoopRunner(
            backend=MockGenerationBackend(output_dir=root / "artifacts"),
            evaluator=evaluator,
            config=DriveLoopConfig(
                max_iterations=1,
                target_score=0.8,
                output_dir=root / "history",
            ),
        ).run(
            DriveLoopRequest(
                prompt="night realistic autonomous driving scene with a visible motorcycle cut in",
                metadata={
                    "perception_evaluation": {
                        "enabled": True,
                        "target_labels": ["motorcycle"],
                        "perception_detections": detection_payload(),
                    },
                },
            )
        )

        records = [
            json.loads(line)
            for line in (root / "history" / "history.jsonl").read_text().splitlines()
        ]

    assert len(result.attempt_history) == 1
    metrics = result.attempt_history[0].evaluation.metrics
    assert metrics["1_PerceptionVideoEvaluator_perception_measured"] == 1.0
    assert metrics["1_PerceptionVideoEvaluator_Q_cov"] == 1.0
    assert metrics["1_PerceptionVideoEvaluator_Q_track"] == 1.0
    assert result.attempt_history[0].evaluation.diagnosis.passed is True

    logged_attempt = records[0]["attempt"]
    assert logged_attempt["generation"]["metadata"]["perception_detections"]["frame_count"] == 4
    assert logged_attempt["evaluation"]["metrics"]["1_PerceptionVideoEvaluator_Q_cov"] == 1.0


def test_api_build_evaluator_enables_perception_video_composite():
    from driveloop.api.server import _build_evaluator

    evaluator = _build_evaluator(
        {
            "perception_evaluation": {
                "enabled": True,
                "target_labels": ["motorcycle"],
                "pass_threshold": 0.8,
            }
        }
    )
    evaluation = evaluator.evaluate(
        Generation(
            iteration=0,
            prompt="night realistic autonomous driving scene with a visible motorcycle cut in",
            artifacts={"video": "candidate.mp4"},
            metadata={
                "target_labels": ["motorcycle"],
                "perception_detections": detection_payload(),
            },
        )
    )

    assert evaluation.diagnosis.passed is True
    assert evaluation.metrics["1_PerceptionVideoEvaluator_perception_measured"] == 1.0
    assert evaluation.metrics["1_PerceptionVideoEvaluator_Q_cov"] == 1.0
