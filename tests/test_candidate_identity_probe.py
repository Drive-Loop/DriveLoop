from __future__ import annotations

import json
import pickle
from pathlib import Path

import pytest

import scripts.run_candidate_identity_probe as probe


def _write_dataset(root: Path, second_frame_has_target: bool = True) -> Path:
    labels = root / "labels"
    labels.mkdir(parents=True)
    records = []
    for frame_idx, sample in ((0, "sample_a"), (1, "sample_b")):
        has_target = frame_idx == 0 or second_frame_has_target
        records.append({
            "cam_type": "CAM_FRONT",
            "frame_idx": frame_idx,
            "video_length": 2,
            "data_index": frame_idx,
            "cam_token": "cam_%d" % frame_idx,
            "sample_token": sample,
            "scene_token": "scene_a",
            "ori_labels3d": ["vehicle.motorcycle", "vehicle.car"],
            "instance_tokens": [
                "target_instance" if has_target else "other_instance",
                "car_instance",
            ],
            "sample_annotation_tokens": ["ann_%d_0" % frame_idx, "ann_%d_1" % frame_idx],
        })
    with (labels / "data.pkl").open("wb") as handle:
        pickle.dump(records, handle)
    return root


def _argv(dataset: Path, out: Path, **overrides):
    args = {
        "--dataset-dir": str(dataset),
        "--candidate-index": "0",
        "--expect-f0-sample-token": "sample_a",
        "--instance-token": "target_instance",
        "--candidate-id": "candidate_test",
        "--output-dir": str(out),
        "--frame-num": "2",
        "--hz-factor": "1",
    }
    args.update(overrides)
    argv = []
    for key, value in args.items():
        argv.extend([key, value])
    argv.append("--single-view")
    return argv


def test_probe_emits_summary_with_target_verification(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset")
    out = tmp_path / "probe"

    assert probe.main(_argv(dataset, out)) == 0

    summary = json.loads((out / "labels" / "summary.json").read_text(encoding="utf-8"))
    assert summary["candidate"] == "candidate_test"
    assert summary["all_frames_have_target"] is True
    assert [f["sample_token"] for f in summary["frame_summaries"]] == ["sample_a", "sample_b"]
    assert summary["frame_summaries"][0]["target_box_indices"] == [0]
    assert (out / "labels" / "data.pkl").exists()


def test_probe_fails_on_f0_sample_token_mismatch(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset")
    with pytest.raises(SystemExit) as excinfo:
        probe.main(_argv(dataset, tmp_path / "probe",
                         **{"--expect-f0-sample-token": "wrong_token"}))
    assert excinfo.value.code == 2


def test_probe_fails_when_target_missing_in_a_frame(tmp_path: Path):
    dataset = _write_dataset(tmp_path / "dataset", second_frame_has_target=False)
    with pytest.raises(SystemExit) as excinfo:
        probe.main(_argv(dataset, tmp_path / "probe"))
    assert excinfo.value.code == 2
