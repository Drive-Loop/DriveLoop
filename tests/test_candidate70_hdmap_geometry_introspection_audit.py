import numpy as np

from scripts.run_candidate70_hdmap_geometry_introspection_audit import (
    array_signature,
    build_summary,
    vector_stats,
)


def test_vector_stats_counts_visible_vectors_by_type():
    vectors = [
        {"type_name": "lane_divider", "pts": np.array([[0, 1], [2, 3], [4, 5]]), "pts_num": 3},
        {"type_name": "lane_divider", "pts": np.array([[1, 1]]), "pts_num": 1},
        {"type_name": "contours", "pts": np.array([[10, 20], [30, 40]]), "pts_num": 2},
    ]

    stats = vector_stats(vectors)

    assert stats["lane_divider"]["count"] == 2
    assert stats["lane_divider"]["visible_count"] == 1
    assert stats["lane_divider"]["total_pts_num"] == 4
    assert stats["lane_divider"]["total_visible_pts_num"] == 3
    assert stats["lane_divider"]["min_xy"] == [0.0, 1.0]
    assert stats["lane_divider"]["max_xy"] == [4.0, 5.0]
    assert stats["contours"]["count"] == 1
    assert stats["contours"]["visible_count"] == 1


def test_array_signature_is_hash_stable():
    arr = np.array([[0, 1], [2, 3]], dtype=np.uint8)

    first = array_signature(arr)
    second = array_signature(arr.copy())

    assert first == second
    assert first["shape"] == [2, 2]
    assert first["dtype"] == "uint8"
    assert first["nonzero"] == 3


def test_build_summary_preserves_claim_boundaries():
    records = [
        {
            "rebuilt_matches_converter_signature": True,
            "vector_stats": {
                "lane_divider": {"visible_count": 2},
                "contours": {"visible_count": 1},
            },
        },
        {
            "rebuilt_matches_converter_signature": True,
            "vector_stats": {
                "lane_divider": {"visible_count": 3},
                "ped_crossing": {"visible_count": 1},
            },
        },
    ]

    summary = build_summary(records, probe_path="probe.json", raw_root="/raw")

    assert summary["schema_version"] == "candidate70_hdmap_geometry_introspection_audit.v0"
    assert summary["audit_only"] is True
    assert summary["does_not_run_gpu"] is True
    assert summary["does_not_generate_video"] is True
    assert summary["does_not_modify_model_inputs"] is True
    assert summary["frame_count"] == 2
    assert summary["rebuilt_match_true"] == 2
    assert summary["rebuilt_match_false"] == 0
    assert summary["all_rebuilt_match_converter"] is True
    assert summary["layer_visible_counts"]["lane_divider"] == 5
    assert summary["layer_visible_counts"]["contours"] == 1
    assert summary["layer_visible_counts"]["ped_crossing"] == 1
    assert summary["claim"]["candidate70_hdmap_geometry_introspected"] is True
    assert summary["claim"]["candidate70_geometry_rebuild_matches_converter"] is True
    assert summary["claim"]["candidate70_true_lane_geometry_replacement_available"] is False
    assert summary["claim"]["hdmap_lane_geometry_override_verified"] is False
    assert summary["claim"]["lane_change_control_verified"] is False
    assert summary["claim"]["runtime_motion_control_connected"] is False
    assert summary["claim"]["semantic_success_claim_allowed"] is False
    assert summary["claim_boundary"]["geometry_introspection_is_not_lane_geometry_override"] is True
    assert summary["claim_boundary"]["geometry_rebuild_match_is_not_replacement"] is True
