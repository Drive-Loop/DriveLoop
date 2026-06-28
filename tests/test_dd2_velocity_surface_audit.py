import json
import pickle
from pathlib import Path

import numpy as np

from scripts.run_dd2_velocity_surface_audit import build_velocity_surface_audit


def test_velocity_surface_audit_records_dataset_velocity_but_no_runtime_use(tmp_path: Path):
    labels = tmp_path / "data.pkl"
    transform = tmp_path / "transform.py"
    tester = tmp_path / "tester.py"

    rows = [
        {
            "scene_token": "scene_0",
            "cam_type": "cam_front",
            "frame_idx": 0,
            "data_index": 0,
            "sample_token": "sample_0",
            "cam_token": "cam_0",
            "ori_labels3d": ["vehicle.motorcycle"],
            "boxes3d": np.zeros((1, 9), dtype=np.float32),
            "velocities": np.asarray([[1.0, -0.5]], dtype=np.float32),
        },
        {
            "scene_token": "scene_0",
            "cam_type": "cam_front",
            "frame_idx": 1,
            "data_index": 1,
            "sample_token": "sample_1",
            "cam_token": "cam_1",
            "ori_labels3d": ["vehicle.motorcycle"],
            "boxes3d": np.ones((1, 9), dtype=np.float32),
            "velocities": np.asarray([[1.2, -0.4]], dtype=np.float32),
        },
    ]
    with labels.open("wb") as f:
        pickle.dump(rows, f)

    transform.write_text("new_data_dict['box_downsampler_input'] = box_downsampler_input\n", encoding="utf-8")
    tester.write_text(
        json.dumps(
            {
                "runtime_inputs": [
                    "prompt_embed",
                    "img_cond",
                    "grounding_downsampler_input",
                    "box_downsampler_input",
                ]
            }
        ),
        encoding="utf-8",
    )

    report = build_velocity_surface_audit(labels, transform, tester)

    assert report["schema_version"] == "driveloop_dd2_velocity_surface_audit.v0"
    assert report["dataset_surface"]["velocities_present"] is True
    assert report["dataset_surface"]["velocities_shape"] == [1, 2]
    assert report["dataset_surface"]["track_identity_fields_present"] == []
    assert report["dataset_surface"]["sequence_frames_inspected"] == 2
    assert report["runtime_surface"]["velocity_runtime_input_observed"] is False
    assert report["claim"]["velocity_exists_in_dataset"] is True
    assert report["claim"]["velocity_consumed_by_dd2_runtime"] is False
    assert report["claim"]["track_identity_available"] is False
    assert report["claim"]["lane_change_trajectory_control"] == "not_verified"
