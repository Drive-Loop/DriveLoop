import numpy as np
from PIL import Image

from scripts.run_candidate70_hdmap_lane_divider_dry_run_builder import (
    build_summary,
    diff_image,
    perturb_lane_dividers,
)


def test_perturb_lane_dividers_only_moves_visible_lane_divider_vectors():
    vectors = [
        {"type_name": "lane_divider", "pts": np.array([[10.0, 20.0], [30.0, 40.0]]), "pts_num": 2},
        {"type_name": "road_divider", "pts": np.array([[1.0, 2.0], [3.0, 4.0]]), "pts_num": 2},
        {"type_name": "lane_divider", "pts": np.array([[5.0, 6.0]]), "pts_num": 1},
    ]

    candidate, operation = perturb_lane_dividers(vectors, dx_pixels=-32.0, dy_pixels=4.0)

    assert operation["modified_count"] == 1
    assert operation["modified_visible_count"] == 1
    assert candidate[0]["pts"].tolist() == [[-22.0, 24.0], [-2.0, 44.0]]
    assert candidate[1]["pts"].tolist() == [[1.0, 2.0], [3.0, 4.0]]
    assert candidate[2]["pts"].tolist() == [[5.0, 6.0]]
    assert "dry_run_operation" in candidate[0]
    assert "dry_run_operation" not in candidate[1]


def test_diff_image_records_pixel_difference():
    baseline = Image.fromarray(np.zeros((2, 2, 3), dtype=np.uint8))
    candidate_arr = np.zeros((2, 2, 3), dtype=np.uint8)
    candidate_arr[0, 0, 1] = 9
    candidate = Image.fromarray(candidate_arr)

    diff = np.asarray(diff_image(baseline, candidate))

    assert diff[0, 0, 1] == 9
    assert int(np.count_nonzero(diff)) == 1


def test_build_summary_keeps_dry_run_claim_boundaries():
    records = [
        {
            "baseline_matches_converter_signature": True,
            "candidate_differs_from_baseline": True,
            "diff_nonzero": 12,
            "operation": {"modified_visible_count": 6},
        },
        {
            "baseline_matches_converter_signature": True,
            "candidate_differs_from_baseline": True,
            "diff_nonzero": 8,
            "operation": {"modified_visible_count": 6},
        },
    ]

    summary = build_summary(
        records=records,
        probe_path="probe.json",
        raw_root="/raw",
        dx_pixels=-32.0,
        dy_pixels=0.0,
    )

    assert summary["schema_version"] == "candidate70_hdmap_lane_divider_dry_run_builder.v0"
    assert summary["audit_only"] is True
    assert summary["does_not_run_gpu"] is True
    assert summary["does_not_generate_video"] is True
    assert summary["does_not_modify_model_inputs"] is True
    assert summary["frame_count"] == 2
    assert summary["baseline_match_true"] == 2
    assert summary["baseline_match_false"] == 0
    assert summary["candidate_changed_true"] == 2
    assert summary["candidate_changed_false"] == 0
    assert summary["total_diff_nonzero"] == 20
    assert summary["total_modified_visible_lane_dividers"] == 12
    assert summary["claim"]["candidate70_lane_divider_dry_run_candidate_built"] is True
    assert summary["claim"]["candidate70_dry_run_raster_diff_observed"] is True
    assert summary["claim"]["candidate70_true_lane_geometry_replacement_available"] is False
    assert summary["claim"]["hdmap_lane_geometry_override_verified"] is False
    assert summary["claim"]["lane_change_control_verified"] is False
    assert summary["claim"]["runtime_motion_control_connected"] is False
    assert summary["claim"]["semantic_success_claim_allowed"] is False
    assert summary["claim_boundary"]["dry_run_candidate_is_synthetic_not_verified_map_geometry"] is True
    assert summary["claim_boundary"]["gpu_requires_separate_readiness_gate"] is True
