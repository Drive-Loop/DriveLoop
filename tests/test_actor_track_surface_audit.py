import pickle
from pathlib import Path

import numpy as np

from scripts.run_actor_track_surface_audit import build_actor_track_surface_audit


def write_labels(path: Path, rows):
    with path.open("wb") as f:
        pickle.dump(rows, f)


def test_actor_track_surface_groups_boxes_by_instance_token(tmp_path: Path):
    labels = tmp_path / "data.pkl"
    rows = [
        {
            "scene_token": "scene",
            "cam_type": "cam_front",
            "frame_idx": 0,
            "data_index": 0,
            "sample_token": "sample_0",
            "cam_token": "cam_0",
            "boxes3d": np.asarray([[0, 1, 2, 3, 4, 5, 0, 0, 0]], dtype=np.float32),
            "velocities": np.asarray([[1.0, 0.5]], dtype=np.float32),
            "instance_tokens": ["inst_0"],
            "sample_annotation_tokens": ["ann_0"],
            "actor_identity_categories": ["vehicle.car"],
        },
        {
            "scene_token": "scene",
            "cam_type": "cam_front",
            "frame_idx": 1,
            "data_index": 1,
            "sample_token": "sample_1",
            "cam_token": "cam_1",
            "boxes3d": np.asarray([[0.5, 1, 2, 3, 4, 5, 0, 0, 0]], dtype=np.float32),
            "velocities": np.asarray([[1.2, 0.4]], dtype=np.float32),
            "instance_tokens": ["inst_0"],
            "sample_annotation_tokens": ["ann_1"],
            "actor_identity_categories": ["vehicle.car"],
        },
    ]
    write_labels(labels, rows)

    report = build_actor_track_surface_audit(labels)

    assert report["schema_version"] == "driveloop_actor_track_surface_audit.v0"
    assert report["status"] == "per_frame_actor_tracks_observed"
    assert report["track_surface"]["actor_identity_available"] is True
    assert report["track_surface"]["boxes_grouped_by_instance_token"] is True
    assert report["track_surface"]["persistent_track_count"] == 1
    assert report["track_surface"]["tracks_preview"][0]["instance_token"] == "inst_0"
    assert report["track_surface"]["tracks_preview"][0]["frame_indices"] == [0, 1]
    assert report["claim"]["per_frame_actor_boxes3d_grouped_by_identity"] is True
    assert report["claim"]["runtime_motion_control_connected"] is False
    assert report["claim_boundary"]["grouped_boxes_do_not_prove_lane_change_control"] is True



def test_actor_track_surface_ignores_null_identity_tokens(tmp_path: Path):
    labels = tmp_path / "data.pkl"
    rows = [
        {
            "scene_token": "scene",
            "cam_type": "cam_front",
            "frame_idx": 0,
            "data_index": 0,
            "sample_token": "sample_0",
            "cam_token": "cam_0",
            "boxes3d": np.asarray(
                [
                    [0, 1, 2, 3, 4, 5, 0, 0, 0],
                    [10, 1, 2, 3, 4, 5, 0, 0, 0],
                ],
                dtype=np.float32,
            ),
            "velocities": np.asarray([[1.0, 0.5], [0.0, 0.0]], dtype=np.float32),
            "instance_tokens": ["inst_0", None],
            "sample_annotation_tokens": ["ann_0", None],
            "actor_identity_categories": ["vehicle.motorcycle", "vehicle.car"],
        },
        {
            "scene_token": "scene",
            "cam_type": "cam_front",
            "frame_idx": 1,
            "data_index": 1,
            "sample_token": "sample_1",
            "cam_token": "cam_1",
            "boxes3d": np.asarray(
                [
                    [0.5, 1, 2, 3, 4, 5, 0, 0, 0],
                    [11, 1, 2, 3, 4, 5, 0, 0, 0],
                ],
                dtype=np.float32,
            ),
            "velocities": np.asarray([[1.2, 0.4], [0.0, 0.0]], dtype=np.float32),
            "instance_tokens": ["inst_0", "None"],
            "sample_annotation_tokens": ["ann_1", None],
            "actor_identity_categories": ["vehicle.motorcycle", "vehicle.car"],
        },
    ]
    write_labels(labels, rows)

    report = build_actor_track_surface_audit(labels)

    assert report["status"] == "per_frame_actor_tracks_observed"
    assert report["track_surface"]["persistent_track_count"] == 1
    assert len(report["track_surface"]["tracks_preview"]) == 1
    assert report["track_surface"]["tracks_preview"][0]["instance_token"] == "inst_0"
    assert report["claim"]["per_frame_actor_identity_observed"] is True

def test_actor_track_surface_reports_missing_identity(tmp_path: Path):
    labels = tmp_path / "data.pkl"
    rows = [
        {
            "scene_token": "scene",
            "cam_type": "cam_front",
            "frame_idx": 0,
            "data_index": 0,
            "sample_token": "sample_0",
            "cam_token": "cam_0",
            "boxes3d": np.zeros((1, 9), dtype=np.float32),
            "velocities": np.zeros((1, 2), dtype=np.float32),
        }
    ]
    write_labels(labels, rows)

    report = build_actor_track_surface_audit(labels)

    assert report["status"] == "not_observed"
    assert report["track_surface"]["actor_identity_available"] is False
    assert "actor_identity_not_available" in report["blockers"]
    assert report["claim"]["per_frame_actor_identity_observed"] is False
