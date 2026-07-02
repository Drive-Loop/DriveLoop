from __future__ import annotations

import json
import pickle
from pathlib import Path
from types import SimpleNamespace

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


def _write_identity(path: Path) -> Path:
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "candidate": "candidate70",
                "frame_summaries": [
                    {"sample_token": "sample_a"},
                    {"sample_token": "sample_b"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_audit_only_allows_missing_baseline_video(monkeypatch, tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset")
    identity = _write_identity(tmp_path / "identity" / "summary.json")
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    captured = {}

    def fake_run(*args, **kwargs):
        env = kwargs["env"]
        captured["env"] = env
        audit_path = Path(env["DRIVELOOP_DD2_AUDIT_PATH"])
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text('{"audit_only": true}', encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)

    backend = DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=baseline_output_dir,
        baseline_dataset_dir=dataset,
        artifact_dir=tmp_path / "artifacts",
        audit_only=True,
        source_candidate_id="candidate70",
        source_identity_summary_path=identity,
        source_selector_frame_num=2,
        source_selector_hz_factor=1,
        source_selector_video_split_rate=1,
        source_selector_multiview=False,
    )

    generation = backend.generate(DriveLoopRequest(prompt="target prompt"), iteration=0)

    assert not (baseline_output_dir / "000000.mp4").exists()
    assert captured["env"]["DRIVELOOP_DD2_AUDIT_ONLY"] == "1"
    assert generation.metadata["dd2_audit_only"] is True
    assert generation.metadata["dd2_runtime_input_audit"]["audit_only"] is True


def test_external_audit_only_env_allows_missing_baseline_video(monkeypatch, tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset")
    identity = _write_identity(tmp_path / "identity" / "summary.json")
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    captured = {}

    def fake_run(*args, **kwargs):
        env = kwargs["env"]
        captured["env"] = env
        audit_path = Path(env["DRIVELOOP_DD2_AUDIT_PATH"])
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text('{"audit_only": true}', encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setenv("DRIVELOOP_DD2_AUDIT_ONLY", "1")
    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)

    backend = DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=baseline_output_dir,
        baseline_dataset_dir=dataset,
        artifact_dir=tmp_path / "artifacts",
        audit_only=False,
        source_candidate_id="candidate70",
        source_identity_summary_path=identity,
        source_selector_frame_num=2,
        source_selector_hz_factor=1,
        source_selector_video_split_rate=1,
        source_selector_multiview=False,
    )

    generation = backend.generate(DriveLoopRequest(prompt="target prompt"), iteration=0)

    assert not (baseline_output_dir / "000000.mp4").exists()
    assert captured["env"]["DRIVELOOP_DD2_AUDIT_ONLY"] == "1"
    assert generation.metadata["dd2_audit_only"] is True
    assert generation.metadata["dd2_runtime_input_audit"]["audit_only"] is True
