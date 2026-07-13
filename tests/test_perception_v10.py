from __future__ import annotations

from pathlib import Path

import pytest

from driveloop.perception_v10 import (
    SuperclassCompositePerceptionEvaluator,
    expand_labels,
)
from driveloop.schema import Generation

import scripts.rescore_driveloop_videos as harness


def test_expand_labels_maps_motorcycle_superclass_normalized():
    assert expand_labels({"motorcycle"}) == {"motorcycle", "bicycle", "pedestrian"}


def test_expand_labels_leaves_unmapped_labels_alone():
    assert expand_labels({"car"}) == {"car"}


def test_resolve_target_labels_expands_in_normalized_vocabulary():
    evaluator = SuperclassCompositePerceptionEvaluator()
    generation = Generation(
        iteration=0,
        prompt="night urban street, a motorcycle cuts in from the left",
        artifacts={},
        metadata={},
    )
    labels = evaluator._resolve_target_labels(generation)
    assert {"motorcycle", "bicycle", "pedestrian"} <= labels
    assert "person" not in labels
    assert evaluator._v10_original_labels == {"motorcycle"}


def test_class_fidelity_normalizes_raw_detector_labels():
    evaluator = SuperclassCompositePerceptionEvaluator()
    centers = [
        [("motorcycle", 10.0), ("person", 20.0)],
        None,
        [("car", 30.0), ("person", 40.0)],
    ]
    share, original, total = evaluator.class_fidelity(
        centers, {"motorcycle"}, {"motorcycle", "bicycle", "pedestrian"}
    )
    assert total == 3
    assert original == 1
    assert share == round(1 / 3, 6)


def test_harness_build_generation_roundtrip():
    record = {
        "generation": {
            "iteration": 2,
            "prompt": "target prompt",
            "artifacts": {"video": "x.mp4"},
            "metadata": {"backend": "drivedreamer2"},
        }
    }
    generation = harness.build_generation(record)
    assert generation.iteration == 2
    assert generation.prompt == "target prompt"
    assert generation.artifacts["video"] == "x.mp4"
    assert generation.metadata["backend"] == "drivedreamer2"


def test_harness_missing_baseline_fails_fast(tmp_path: Path):
    with pytest.raises(SystemExit) as excinfo:
        harness.main(
            [
                "--arm", "t=%s=%s" % (tmp_path, tmp_path / "missing.mp4"),
                "--cases", "m1_night_cut_in_left",
            ]
        )
    assert excinfo.value.code == 2
