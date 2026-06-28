import numpy as np

from driveloop.dd2_override import (
    apply_dd2_override_to_sample,
    read_override_audit,
    tensor_signature,
    write_override_audit,
)


def test_apply_dd2_override_appends_boxes_and_records_changed_signature():
    sample = {
        "scene_description": "clear road with a car",
        "boxes3d": np.zeros((1, 9), dtype=np.float32),
        "ori_labels3d": ["vehicle.car"],
        "labels3d": [["vehicle", "car"]],
        "image_hdmap": np.ones((2, 2, 3), dtype=np.uint8),
    }
    before = tensor_signature(sample["boxes3d"])

    updated, audit = apply_dd2_override_to_sample(
        sample,
        {
            "schema_version": "driveloop_dd2_override.v0",
            "scene_description": {
                "value": "rainy night intersection with a bicycle cut in",
                "source": "text_control.prompt",
            },
            "boxes3d": {
                "append": [
                    {
                        "category": "bicycle",
                        "box3d": [8.0, 1.8, 18.0, 0.6, 1.6, 1.8, 0.0, 0.0, -0.25],
                        "source": "class_default_dimensions",
                        "provenance": "driveloop_executable_condition",
                    }
                ]
            },
            "image_hdmap": {
                "mode": "keep_baseline",
                "reason": "no_verified_hdmap_override_source",
            },
        },
    )

    assert updated["scene_description"] == "rainy night intersection with a bicycle cut in"
    assert updated["boxes3d"].shape == (2, 9)
    assert updated["ori_labels3d"] == ["vehicle.car", "vehicle.bicycle"]
    assert updated["labels3d"] == [["vehicle", "car"], ["vehicle", "bicycle"]]
    assert tensor_signature(updated["boxes3d"]) != before
    assert audit["changed"]["boxes3d"] is True
    assert audit["changed"]["scene_description"] is True
    assert audit["changed"]["image_hdmap"] is False
    assert audit["image_box_expected_changed"] is True


def test_apply_dd2_override_can_zero_hdmap_when_explicitly_requested():
    sample = {
        "boxes3d": np.zeros((0, 9), dtype=np.float32),
        "ori_labels3d": [],
        "labels3d": [],
        "image_hdmap": np.ones((2, 2, 3), dtype=np.uint8),
    }

    updated, audit = apply_dd2_override_to_sample(
        sample,
        {
            "schema_version": "driveloop_dd2_override.v0",
            "image_hdmap": {
                "mode": "zero",
                "source": "unit_test_explicit_override",
            },
        },
    )

    assert np.count_nonzero(updated["image_hdmap"]) == 0
    assert audit["changed"]["image_hdmap"] is True


def test_override_audit_summary_counts_changed_targets(tmp_path):
    audit_path = tmp_path / "override_audit.jsonl"
    write_override_audit(
        audit_path,
        {
            "changed": {
                "boxes3d": True,
                "scene_description": True,
                "image_hdmap": False,
            },
            "image_box_expected_changed": True,
        },
    )

    summary = read_override_audit(audit_path)

    assert summary["available"] is True
    assert summary["entry_count"] == 1
    assert summary["changed_counts"] == {
        "boxes3d": 1,
        "scene_description": 1,
        "image_box": 1,
    }

def test_override_audit_summary_does_not_double_count_image_box(tmp_path):
    audit_path = tmp_path / "override_audit.jsonl"
    write_override_audit(
        audit_path,
        {
            "changed": {
                "boxes3d": True,
                "image_box": True,
                "scene_description": True,
            },
            "image_box_expected_changed": True,
        },
    )

    summary = read_override_audit(audit_path)

    assert summary["changed_counts"] == {
        "boxes3d": 1,
        "image_box": 1,
        "scene_description": 1,
    }

