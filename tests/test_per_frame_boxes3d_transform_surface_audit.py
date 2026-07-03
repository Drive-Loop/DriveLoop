from scripts.run_per_frame_boxes3d_transform_surface_audit import (
    _build_checks,
    _compare_rows,
    _parse_frame_indices,
)


def test_parse_frame_indices():
    assert _parse_frame_indices("0, 2,3") == [0, 2, 3]


def test_build_checks_accepts_targeted_changes_and_non_target_skips():
    baseline = [
        {"index": 0, "frame_idx": 0, "box_sha256": "a"},
        {"index": 1, "frame_idx": 1, "box_sha256": "b"},
        {"index": 2, "frame_idx": 2, "box_sha256": "c"},
        {"index": 3, "frame_idx": 3, "box_sha256": "d"},
    ]
    override = [
        {"index": 0, "frame_idx": 0, "box_sha256": "aa"},
        {"index": 1, "frame_idx": 1, "box_sha256": "b"},
        {"index": 2, "frame_idx": 2, "box_sha256": "cc"},
        {"index": 3, "frame_idx": 3, "box_sha256": "d"},
    ]
    audit_entries = [
        {"sample_identity": {"frame_idx": 0}, "changed": {"image_box": True}, "skipped": []},
        {
            "sample_identity": {"frame_idx": 1},
            "changed": {"image_box": False},
            "skipped": [{"mode": "per_frame_append", "reason": "no_matching_frame_idx"}],
        },
        {"sample_identity": {"frame_idx": 2}, "changed": {"image_box": True}, "skipped": []},
        {
            "sample_identity": {"frame_idx": 3},
            "changed": {"image_box": False},
            "skipped": [{"mode": "per_frame_append", "reason": "no_matching_frame_idx"}],
        },
    ]

    comparisons = _compare_rows(baseline, override, [0, 2])
    checks = _build_checks(comparisons, audit_entries, [0, 1, 2, 3], [0, 2])

    assert checks["targeted_frames_changed"] is True
    assert checks["non_targeted_frames_unchanged"] is True
    assert checks["override_audit_entry_count_matches"] is True
    assert checks["target_audit_image_box_changed"] is True
    assert checks["non_target_audit_skipped"] is True
    assert checks["structural_condition_surface_verified"] is True


def test_build_checks_rejects_unchanged_target_frame():
    baseline = [
        {"index": 0, "frame_idx": 0, "box_sha256": "a"},
        {"index": 1, "frame_idx": 1, "box_sha256": "b"},
    ]
    override = [
        {"index": 0, "frame_idx": 0, "box_sha256": "a"},
        {"index": 1, "frame_idx": 1, "box_sha256": "b"},
    ]
    audit_entries = [
        {"sample_identity": {"frame_idx": 0}, "changed": {"image_box": False}, "skipped": []},
        {
            "sample_identity": {"frame_idx": 1},
            "changed": {"image_box": False},
            "skipped": [{"mode": "per_frame_append", "reason": "no_matching_frame_idx"}],
        },
    ]

    comparisons = _compare_rows(baseline, override, [0])
    checks = _build_checks(comparisons, audit_entries, [0, 1], [0])

    assert checks["targeted_frames_changed"] is False
    assert checks["structural_condition_surface_verified"] is False
