from __future__ import annotations

import json
from pathlib import Path

import pytest

from driveloop.backends.drivedreamer2 import DriveDreamer2Backend

STRUCTURAL_PLAN = {
    "scene_description": {"value": "night urban street", "source": "text_control.prompt"}
}
CANDIDATE_PLAN = {
    "actor_motion_surface_plan": {
        "per_frame_boxes3d": [
            {
                "frame_idx": 0,
                "actor_id": "actor_00",
                "synthetic_track_id": "actor_00_synthetic_motion_track",
                "category": "motorcycle",
                "box3d": [1.0, 2.0, 3.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
            }
        ]
    }
}


def _backend(tmp_path: Path) -> DriveDreamer2Backend:
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    return DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=baseline_output_dir,
        baseline_dataset_dir=tmp_path / "dataset",
        artifact_dir=tmp_path / "artifacts",
    )


def test_strict_mode_blocks_empty_real_track_fallback(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DRIVELOOP_EGO_INJECTION", "1")
    monkeypatch.setenv("DRIVELOOP_EGO_REQUIRE_REAL_TRACK", "1")
    backend = _backend(tmp_path)

    with pytest.raises(RuntimeError, match="silent synthetic fallback"):
        backend._build_override_json(
            "prompt",
            STRUCTURAL_PLAN,
            CANDIDATE_PLAN,
            source_sample_binding={"ready": False},
        )


def test_default_keeps_synthetic_fallback(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DRIVELOOP_EGO_INJECTION", "1")
    monkeypatch.delenv("DRIVELOOP_EGO_REQUIRE_REAL_TRACK", raising=False)
    backend = _backend(tmp_path)

    override = backend._build_override_json(
        "prompt",
        STRUCTURAL_PLAN,
        CANDIDATE_PLAN,
        source_sample_binding={"ready": False},
    )

    assert "real_track_fallback_reason" in json.dumps(override)


def test_strict_mode_ignored_without_injection(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("DRIVELOOP_EGO_INJECTION", raising=False)
    monkeypatch.setenv("DRIVELOOP_EGO_REQUIRE_REAL_TRACK", "1")
    backend = _backend(tmp_path)

    override = backend._build_override_json(
        "prompt",
        STRUCTURAL_PLAN,
        CANDIDATE_PLAN,
        source_sample_binding={"ready": False},
    )

    assert isinstance(override, dict)
