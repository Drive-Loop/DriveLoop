from scripts.run_candidate70_hdmap_lane_geometry_replacement_surface_audit import (
    build_report,
    select_candidate_record,
)


def test_select_candidate_record_requires_local_map_vector_operation():
    summary = {
        "claim": {"candidate70_geometry_grounded_replacement_candidate_available": True},
        "records": [
            {
                "data_index": 1,
                "frame_idx": 144,
                "candidate_raster_path": "/tmp/missing.png",
                "candidate_signature": {"sha256": "abc"},
                "baseline_matches_converter_signature": True,
                "candidate_differs_from_baseline": True,
                "diff_nonzero": 10,
                "operation": {
                    "operation": "offset_lane_divider_camera_space_before_projection",
                    "coordinate_frame": "camera",
                    "modified_visible_count": 1,
                },
            }
        ],
    }

    record = select_candidate_record(summary, 0)

    assert record["available"] is False
    assert record["reason"] == "unverified_candidate_record"


def test_build_report_promotes_only_hdmap_surface_claim_not_semantic_success():
    report = build_report(
        baseline_signatures={
            "grounding_downsampler_input": {"sha256": "a"},
            "box_downsampler_input": {"sha256": "b"},
            "input_image": {"sha256": "c"},
        },
        replacement_signatures={
            "grounding_downsampler_input": {"sha256": "changed"},
            "box_downsampler_input": {"sha256": "b"},
            "input_image": {"sha256": "c"},
        },
        override_audit={
            "available": True,
            "changed_counts": {"image_hdmap": 1},
            "entries_preview": [{"applied": [{"target": "image_hdmap", "mode": "replace_from_path"}]}],
        },
        candidate_summary={
            "claim": {"candidate70_geometry_grounded_replacement_candidate_available": True}
        },
        candidate_record={"available": True, "path": "candidate.png"},
    )

    assert report["status"] == "local_map_vector_lane_geometry_replacement_reaches_grounding_surface"
    assert report["claim"]["candidate70_true_lane_geometry_replacement_available"] is True
    assert report["claim"]["hdmap_lane_geometry_override_verified"] is True
    assert report["claim"]["lane_change_control_verified"] is False
    assert report["claim"]["semantic_success_claim_allowed"] is False
    assert report["claim_boundary"]["runtime_tensor_audit_is_not_video_semantic_success"] is True
