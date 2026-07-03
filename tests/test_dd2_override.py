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


def test_apply_dd2_override_appends_only_matching_per_frame_boxes():
    sample = {
        "frame_idx": 2,
        "scene_description": "night road",
        "boxes3d": np.zeros((0, 9), dtype=np.float32),
        "ori_labels3d": [],
        "labels3d": [],
        "image_hdmap": np.ones((2, 2, 3), dtype=np.uint8),
    }

    updated, audit = apply_dd2_override_to_sample(
        sample,
        {
            "schema_version": "driveloop_dd2_override.v0",
            "boxes3d": {
                "per_frame_append": [
                    {
                        "frame_idx": 1,
                        "category": "car",
                        "box3d": [1.0, 0.0, 8.0, 1.8, 1.6, 4.0, 0.0, 0.0, 0.0],
                    },
                    {
                        "frame_idx": 2,
                        "category": "motorcycle",
                        "box3d": [6.0, -1.0, 18.0, 0.7, 1.5, 2.0, 0.0, 0.0, -0.2],
                        "source": "unit_test_per_frame_trajectory",
                        "provenance": "synthetic_temporal_box_condition",
                    },
                ],
            },
        },
    )

    assert updated["boxes3d"].shape == (1, 9)
    assert updated["ori_labels3d"] == ["vehicle.motorcycle"]
    assert updated["labels3d"] == [["vehicle", "motorcycle"]]
    assert audit["changed"]["boxes3d"] is True
    assert audit["image_box_expected_changed"] is True
    per_frame_audit = next(item for item in audit["applied"] if item["mode"] == "per_frame_append")
    assert per_frame_audit["frame_idx"] == 2
    assert per_frame_audit["accepted_count"] == 1
    assert per_frame_audit["accepted_entries"][0]["frame_idx"] == 2


def test_apply_dd2_override_does_not_match_missing_frame_idx():
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
            "boxes3d": {
                "per_frame_append": [
                    {
                        "category": "motorcycle",
                        "box3d": [6.0, -1.0, 18.0, 0.7, 1.5, 2.0, 0.0, 0.0, -0.2],
                    },
                ],
            },
        },
    )

    assert updated["boxes3d"].shape == (0, 9)
    assert audit["changed"]["boxes3d"] is False
    skip = next(item for item in audit["skipped"] if item.get("mode") == "per_frame_append")
    assert skip["reason"] == "no_matching_frame_idx"
    assert skip["frame_idx"] is None


def test_apply_dd2_override_skips_per_frame_boxes_without_matching_frame():
    sample = {
        "frame_idx": 3,
        "boxes3d": np.zeros((0, 9), dtype=np.float32),
        "ori_labels3d": [],
        "labels3d": [],
        "image_hdmap": np.ones((2, 2, 3), dtype=np.uint8),
    }

    updated, audit = apply_dd2_override_to_sample(
        sample,
        {
            "schema_version": "driveloop_dd2_override.v0",
            "boxes3d": {
                "per_frame_append": [
                    {
                        "frame_idx": 2,
                        "category": "motorcycle",
                        "box3d": [6.0, -1.0, 18.0, 0.7, 1.5, 2.0, 0.0, 0.0, -0.2],
                    },
                ],
            },
        },
    )

    assert updated["boxes3d"].shape == (0, 9)
    assert audit["changed"]["boxes3d"] is False
    assert audit["image_box_expected_changed"] is False
    skip = next(item for item in audit["skipped"] if item.get("mode") == "per_frame_append")
    assert skip["reason"] == "no_matching_frame_idx"
    assert skip["frame_idx"] == 3

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


def test_apply_dd2_override_replaces_hdmap_from_verified_path(tmp_path):
    from PIL import Image

    raster_path = tmp_path / "replacement_hdmap.png"
    replacement = np.zeros((3, 4, 3), dtype=np.uint8)
    replacement[:, :, 1] = 7
    Image.fromarray(replacement).save(raster_path)
    expected_sha256 = tensor_signature(Image.open(raster_path).convert("RGB"))["sha256"]

    sample = {
        "boxes3d": np.zeros((0, 9), dtype=np.float32),
        "ori_labels3d": [],
        "labels3d": [],
        "image_hdmap": np.ones((3, 4, 3), dtype=np.uint8),
    }

    updated, audit = apply_dd2_override_to_sample(
        sample,
        {
            "schema_version": "driveloop_dd2_override.v0",
            "image_hdmap": {
                "mode": "replace_from_path",
                "path": str(raster_path),
                "source": "unit_test_verified_raster",
                "provenance": "tmp_path_png",
                "expected_sha256": expected_sha256,
            },
        },
    )

    assert audit["changed"]["image_hdmap"] is True
    applied = audit["applied"][0]
    assert applied["target"] == "image_hdmap"
    assert applied["mode"] == "replace_from_path"
    assert applied["applied"] is True
    assert applied["path"] == str(raster_path)
    assert applied["source"] == "unit_test_verified_raster"
    assert applied["provenance"] == "tmp_path_png"
    assert applied["expected_sha256"] == expected_sha256
    assert applied["actual_sha256"] == expected_sha256
    assert applied["claim_boundary"]["replacement_raster_reaches_grounding_surface_only"] is True
    assert applied["claim_boundary"]["hdmap_lane_geometry_override_verified"] is False
    assert applied["claim_boundary"]["lane_change_control_verified"] is False
    assert applied["claim_boundary"]["runtime_motion_control_connected"] is False
    assert applied["claim_boundary"]["semantic_success_claim_allowed"] is False
    assert tensor_signature(updated["image_hdmap"])["sha256"] == expected_sha256


def test_apply_dd2_override_rejects_missing_hdmap_replacement_path():
    sample = {
        "boxes3d": np.zeros((0, 9), dtype=np.float32),
        "ori_labels3d": [],
        "labels3d": [],
        "image_hdmap": np.ones((2, 2, 3), dtype=np.uint8),
    }
    before = tensor_signature(sample["image_hdmap"])

    updated, audit = apply_dd2_override_to_sample(
        sample,
        {
            "schema_version": "driveloop_dd2_override.v0",
            "image_hdmap": {
                "mode": "replace_from_path",
                "path": "does/not/exist.png",
                "source": "unit_test_missing_raster",
                "expected_sha256": "not_used",
            },
        },
    )

    assert tensor_signature(updated["image_hdmap"]) == before
    assert audit["changed"]["image_hdmap"] is False
    hdmap_skip = next(item for item in audit["skipped"] if item["target"] == "image_hdmap")
    assert hdmap_skip["mode"] == "replace_from_path"
    assert hdmap_skip["reason"] == "missing_path"


def test_apply_dd2_override_rejects_hdmap_replacement_hash_mismatch(tmp_path):
    from PIL import Image

    raster_path = tmp_path / "replacement_hdmap.png"
    replacement = np.zeros((2, 2, 3), dtype=np.uint8)
    replacement[:, :, 2] = 9
    Image.fromarray(replacement).save(raster_path)

    sample = {
        "boxes3d": np.zeros((0, 9), dtype=np.float32),
        "ori_labels3d": [],
        "labels3d": [],
        "image_hdmap": np.ones((2, 2, 3), dtype=np.uint8),
    }
    before = tensor_signature(sample["image_hdmap"])

    updated, audit = apply_dd2_override_to_sample(
        sample,
        {
            "schema_version": "driveloop_dd2_override.v0",
            "image_hdmap": {
                "mode": "replace_from_path",
                "path": str(raster_path),
                "source": "unit_test_bad_hash",
                "expected_sha256": "0" * 64,
            },
        },
    )

    assert tensor_signature(updated["image_hdmap"]) == before
    assert audit["changed"]["image_hdmap"] is False
    hdmap_skip = next(item for item in audit["skipped"] if item["target"] == "image_hdmap")
    assert hdmap_skip["mode"] == "replace_from_path"
    assert hdmap_skip["reason"] == "sha256_mismatch"
    assert hdmap_skip["actual_sha256"] != "0" * 64
