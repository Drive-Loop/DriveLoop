from __future__ import annotations

import json
import pickle
from pathlib import Path

from driveloop.schema import DriveLoopRequest, LongTailConditionPlan, SceneSpecification
from driveloop.source_selector import DD2SourceSelector, NoOpSourceSelector


def write_dataset(root: Path) -> Path:
    labels = root / "labels"
    labels.mkdir(parents=True)
    records = [
        {"cam_type": "CAM_FRONT", "frame_idx": 0, "video_length": 2, "sample_token": "sample_a", "scene_token": "scene_0"},
        {"cam_type": "CAM_FRONT", "frame_idx": 1, "video_length": 2, "sample_token": "sample_b", "scene_token": "scene_0"},
        {"cam_type": "CAM_FRONT", "frame_idx": 2, "video_length": 2, "sample_token": "other_a", "scene_token": "scene_1"},
        {"cam_type": "CAM_FRONT", "frame_idx": 3, "video_length": 2, "sample_token": "other_b", "scene_token": "scene_1"},
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


def test_noop_source_selector_records_not_requested():
    selection = NoOpSourceSelector().select(
        DriveLoopRequest(prompt="test"),
        SceneSpecification(prompt="test"),
        LongTailConditionPlan(),
    )

    assert selection.requested is False
    assert selection.ready is False
    assert selection.selector_type == "none"
    assert selection.diagnosis["status"] == "not_requested"
    assert selection.claim_boundary["source_selection_is_not_gpu_approval"] is True


def test_dd2_source_selector_wraps_source_sample_binding(tmp_path: Path):
    dataset = write_dataset(tmp_path / "dataset")
    identity = write_identity(tmp_path / "identity" / "summary.json")

    selection = DD2SourceSelector(
        dataset,
        source_candidate_id="candidate70",
        identity_summary_path=identity,
        frame_num=2,
        hz_factor=1,
        video_split_rate=1,
        multiview=False,
    ).select(
        DriveLoopRequest(prompt="night motorcycle cut in"),
        SceneSpecification(prompt="night motorcycle cut in"),
        LongTailConditionPlan(),
    )

    assert selection.requested is True
    assert selection.ready is True
    assert selection.selector_type == "dd2_source_sample_binding"
    assert selection.binding["dd2_batch_skip"] == 0
    assert selection.backend_hints["source_candidate_id"] == "candidate70"
    assert selection.backend_hints["source_identity_summary_path"] == str(identity)
    assert selection.claim_boundary["source_selection_is_not_gpu_approval"] is True
    assert selection.diagnosis["status"] == "ready"


def test_dd2_source_selector_records_failure_diagnosis(tmp_path: Path):
    dataset = write_dataset(tmp_path / "dataset")

    selection = DD2SourceSelector(
        dataset,
        sample_token="missing_sample",
        frame_num=2,
        hz_factor=1,
        video_split_rate=1,
        multiview=False,
    ).select(
        DriveLoopRequest(prompt="night motorcycle cut in"),
        SceneSpecification(prompt="night motorcycle cut in"),
        LongTailConditionPlan(),
    )

    assert selection.requested is True
    assert selection.ready is False
    assert selection.binding["reason"] == "no_dd2_candidate_contains_requested_source_tokens"
    assert selection.diagnosis["status"] == "failed"
    assert "select another source candidate" in selection.diagnosis["suggested_actions"][0]
