from pathlib import Path

from scripts.run_candidate70_hdmap_lane_geometry_replacement_builder import build_summary


def test_lane_geometry_candidate_summary_marks_candidate_without_runtime_claim():
    summary = build_summary(
        records=[
            {
                "baseline_matches_converter_signature": True,
                "candidate_differs_from_baseline": True,
                "diff_nonzero": 123,
                "operation": {"modified_visible_count": 6},
            }
        ],
        probe_path=Path("probe.json"),
        raw_root="/tmp/nuscenes",
        local_x_offset_m=0.0,
        local_y_offset_m=-1.5,
    )

    assert summary["claim"]["candidate70_geometry_grounded_replacement_candidate_available"] is True
    assert summary["claim"]["candidate70_true_lane_geometry_replacement_available"] is False
    assert summary["claim"]["hdmap_lane_geometry_override_verified"] is False
    assert summary["claim_boundary"]["candidate_raster_requires_runtime_surface_audit_before_gate_use"] is True
    assert summary["operation"]["coordinate_frame"] == "ego_aligned_local_map_patch"


def test_lane_geometry_candidate_summary_refuses_candidate_when_baseline_does_not_match_converter():
    summary = build_summary(
        records=[
            {
                "baseline_matches_converter_signature": False,
                "candidate_differs_from_baseline": True,
                "diff_nonzero": 123,
                "operation": {"modified_visible_count": 6},
            }
        ],
        probe_path=Path("probe.json"),
        raw_root="/tmp/nuscenes",
        local_x_offset_m=0.0,
        local_y_offset_m=-1.5,
    )

    assert summary["claim"]["candidate70_geometry_grounded_replacement_candidate_available"] is False
    assert summary["claim"]["candidate70_true_lane_geometry_replacement_available"] is False
