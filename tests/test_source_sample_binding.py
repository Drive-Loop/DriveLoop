from __future__ import annotations

import json
import pickle
from pathlib import Path
from types import SimpleNamespace

from driveloop.backends.drivedreamer2 import DriveDreamer2Backend
from driveloop.schema import DriveLoopRequest
from driveloop.source_sample_binding import build_source_sample_binding


def write_dataset(root: Path) -> Path:
    labels = root / "labels"
    labels.mkdir(parents=True)
    records = [
        {
            "cam_type": "CAM_FRONT",
            "frame_idx": 0,
            "video_length": 4,
            "sample_token": "sample_a",
            "scene_token": "scene_0",
            "scene_description": "target start",
            "labels3d": [["vehicle", "motorcycle"]],
            "ori_labels3d": ["vehicle.motorcycle"],
        },
        {
            "cam_type": "CAM_FRONT",
            "frame_idx": 1,
            "video_length": 4,
            "sample_token": "sample_b",
            "scene_token": "scene_0",
            "scene_description": "target second",
            "labels3d": [["vehicle", "motorcycle"]],
            "ori_labels3d": ["vehicle.motorcycle"],
        },
        {
            "cam_type": "CAM_FRONT",
            "frame_idx": 2,
            "video_length": 4,
            "sample_token": "sample_c",
            "scene_token": "scene_1",
            "scene_description": "other start",
            "labels3d": [["vehicle", "car"]],
            "ori_labels3d": ["vehicle.car"],
        },
        {
            "cam_type": "CAM_FRONT",
            "frame_idx": 3,
            "video_length": 4,
            "sample_token": "sample_d",
            "scene_token": "scene_1",
            "scene_description": "other second",
            "labels3d": [["vehicle", "car"]],
            "ori_labels3d": ["vehicle.car"],
        },
    ]
    with (labels / "data.pkl").open("wb") as handle:
        pickle.dump(records, handle)
    return root


def write_identity(path: Path) -> Path:
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


def test_source_sample_binding_maps_identity_tokens_to_dd2_batch_skip(tmp_path: Path):
    dataset = write_dataset(tmp_path / "dataset")
    identity = write_identity(tmp_path / "identity" / "summary.json")

    binding = build_source_sample_binding(
        dataset,
        source_candidate_id="candidate70",
        identity_summary_path=identity,
        frame_num=2,
        hz_factor=1,
        video_split_rate=1,
        multiview=False,
    )

    assert binding["ready"] is True
    assert binding["dd2_batch_skip"] == 0
    assert binding["front_record_index"] == 0
    assert binding["matched_sample_tokens"] == ["sample_a", "sample_b"]
    assert binding["claim_boundary"]["source_sample_binding_is_not_gpu_approval"] is True


def test_source_sample_binding_blocks_when_tokens_are_not_in_dd2_dataset(tmp_path: Path):
    dataset = write_dataset(tmp_path / "dataset")

    binding = build_source_sample_binding(
        dataset,
        sample_token="missing_sample",
        frame_num=2,
        hz_factor=1,
        video_split_rate=1,
        multiview=False,
    )

    assert binding["ready"] is False
    assert binding["reason"] == "no_dd2_candidate_contains_requested_source_tokens"


def test_drivedreamer2_backend_sets_runtime_batch_skip_from_source_binding(monkeypatch, tmp_path: Path):
    dataset = write_dataset(tmp_path / "dataset")
    identity = write_identity(tmp_path / "identity" / "summary.json")
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    baseline_video = baseline_output_dir / "000000.mp4"
    captured = {}

    def fake_run(cmd, cwd, env, check, text, timeout):
        captured["env"] = env
        baseline_video.write_bytes(b"fake video")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)

    backend = DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=baseline_output_dir,
        baseline_dataset_dir=dataset,
        artifact_dir=tmp_path / "artifacts",
        source_candidate_id="candidate70",
        source_identity_summary_path=identity,
        source_selector_frame_num=2,
        source_selector_hz_factor=1,
        source_selector_video_split_rate=1,
        source_selector_multiview=False,
    )

    generation = backend.generate(DriveLoopRequest(prompt="target prompt"), iteration=0)

    assert captured["env"]["DRIVELOOP_DD2_BATCH_SKIP"] == "0"
    assert generation.metadata["dd2_source_sample_binding"]["ready"] is True
    assert generation.metadata["dd2_source_sample_binding"]["dd2_batch_skip"] == 0
    assert generation.metadata["dd2_baseline_structural_snapshot"]["sample"]["sample_token"] == "sample_a"


def test_source_sample_binding_blocks_partial_identity_token_match(tmp_path: Path):
    dataset = write_dataset(tmp_path / "dataset")
    identity = write_identity(tmp_path / "identity" / "summary.json")
    data = json.loads(identity.read_text(encoding="utf-8"))
    data["frame_summaries"].append({"sample_token": "missing_sample"})
    identity.write_text(json.dumps(data), encoding="utf-8")

    binding = build_source_sample_binding(
        dataset,
        source_candidate_id="candidate70",
        identity_summary_path=identity,
        frame_num=2,
        hz_factor=1,
        video_split_rate=1,
        multiview=False,
    )

    assert binding["ready"] is False
    assert binding["reason"] == "no_dd2_candidate_contains_requested_source_tokens"
