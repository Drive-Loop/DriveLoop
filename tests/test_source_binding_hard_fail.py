from __future__ import annotations

import pickle
from pathlib import Path
from types import SimpleNamespace

import pytest

from driveloop.backends.drivedreamer2 import DriveDreamer2Backend
from driveloop.schema import DriveLoopRequest


def _write_dataset(root: Path) -> Path:
    labels = root / "labels"
    labels.mkdir(parents=True)
    records = [
        {
            "cam_type": "CAM_FRONT",
            "frame_idx": 0,
            "video_length": 2,
            "sample_token": "sample_a",
            "scene_token": "scene_a",
            "scene_description": "target start",
            "labels3d": [["vehicle", "motorcycle"]],
            "ori_labels3d": ["vehicle.motorcycle"],
        },
        {
            "cam_type": "CAM_FRONT",
            "frame_idx": 1,
            "video_length": 2,
            "sample_token": "sample_b",
            "scene_token": "scene_a",
            "scene_description": "target second",
            "labels3d": [["vehicle", "motorcycle"]],
            "ori_labels3d": ["vehicle.motorcycle"],
        },
    ]
    with (labels / "data.pkl").open("wb") as handle:
        pickle.dump(records, handle)
    return root


def _backend(tmp_path: Path, **kwargs) -> DriveDreamer2Backend:
    dataset = _write_dataset(tmp_path / "dataset")
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    return DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=baseline_output_dir,
        baseline_dataset_dir=dataset,
        artifact_dir=tmp_path / "artifacts",
        source_selector_frame_num=2,
        source_selector_hz_factor=1,
        source_selector_video_split_rate=1,
        source_selector_multiview=False,
        **kwargs,
    )


def test_unready_binding_hard_fails_before_generation(monkeypatch, tmp_path: Path):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)
    backend = _backend(tmp_path, audit_only=False, sample_token="missing_token")

    with pytest.raises(RuntimeError, match="binding is not ready"):
        backend.generate(DriveLoopRequest(prompt="target prompt"), iteration=0)
    assert calls == []


def test_unready_binding_does_not_delete_existing_baseline_video(monkeypatch, tmp_path: Path):
    def fake_run(*args, **kwargs):
        raise AssertionError("generation must not start")

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)
    backend = _backend(tmp_path, audit_only=False, sample_token="missing_token")
    baseline_video = backend.baseline_output_dir / "000000.mp4"
    baseline_video.write_bytes(b"keep existing baseline video")

    with pytest.raises(RuntimeError, match="binding is not ready"):
        backend.generate(DriveLoopRequest(prompt="target prompt"), iteration=0)
    assert baseline_video.read_bytes() == b"keep existing baseline video"


def test_unready_binding_still_allows_audit_only_diagnosis(monkeypatch, tmp_path: Path):
    def fake_run(*args, **kwargs):
        env = kwargs["env"]
        audit_path = Path(env["DRIVELOOP_DD2_AUDIT_PATH"])
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text('{"audit_only": true}', encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)
    backend = _backend(tmp_path, audit_only=True, sample_token="missing_token")

    generation = backend.generate(DriveLoopRequest(prompt="target prompt"), iteration=0)

    binding = generation.metadata["dd2_source_sample_binding"]
    assert binding["requested"] is True
    assert binding["ready"] is False


def test_no_selector_keeps_synthetic_fallback_path(monkeypatch, tmp_path: Path):
    def fake_run(*args, **kwargs):
        env = kwargs["env"]
        audit_path = Path(env["DRIVELOOP_DD2_AUDIT_PATH"])
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text('{"audit_only": true}', encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)
    backend = _backend(tmp_path, audit_only=True)

    generation = backend.generate(DriveLoopRequest(prompt="target prompt"), iteration=0)

    binding = generation.metadata["dd2_source_sample_binding"]
    assert binding["requested"] is False
