import pickle
from pathlib import Path

from scripts.run_actor_identity_surface_audit import build_report


def write_pickle(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pickle.dumps(payload))
    return path


def test_actor_identity_audit_detects_upstream_missing_processed_identity(tmp_path):
    converter = tmp_path / "nuscenes_converter.py"
    converter.write_text(
        "global_velo2d = self.nusc.box_velocity(cam_box.token)[:2]\n"
        "ann_token = self.nusc.get('sample_annotation', cam_box.token)['attribute_tokens']\n",
        encoding="utf-8",
    )
    labels = write_pickle(
        tmp_path / "labels.pkl",
        [
            {
                "scene_token": "scene",
                "sample_token": "sample",
                "cam_token": "cam",
                "boxes3d": [[1] * 9],
                "velocities": [[0, 0]],
                "labels3d": ["car"],
            }
        ],
    )

    report = build_report(converter, [labels])

    assert report["status"] == "identity_available_upstream_but_missing_from_processed_labels"
    assert report["converter_surface"]["cam_box_token_observed"] is True
    assert report["converter_surface"]["converter_has_actor_identity_token_source"] is True
    assert report["converter_surface"]["processed_label_identity_write_observed"] is False
    assert report["processed_label_surfaces"][0]["actor_identity_available"] is False
    assert report["claim"]["runtime_motion_control_connected"] is False
    assert report["claim"]["semantic_success_claim_allowed"] is False
    assert "processed_labels_do_not_include_persistent_actor_identity" in report["blockers"]


def test_actor_identity_audit_detects_processed_identity(tmp_path):
    converter = tmp_path / "nuscenes_converter.py"
    converter.write_text("cam_box.token\n", encoding="utf-8")
    labels = write_pickle(
        tmp_path / "labels.pkl",
        [
            {
                "sample_annotation_tokens": ["ann"],
                "instance_tokens": ["inst"],
                "boxes3d": [[1] * 9],
                "velocities": [[0, 0]],
            }
        ],
    )

    report = build_report(converter, [labels])

    assert report["status"] == "identity_available_in_processed_labels"
    assert report["processed_label_surfaces"][0]["actor_identity_available"] is True
    assert report["claim"]["runtime_motion_control_connected"] is False
    assert report["claim"]["actor_identity_available_in_processed_labels"] is True
