from scripts.run_candidate70_hdmap_dry_run_replacement_surface_audit import (
    build_report,
    select_dry_run_candidate_record,
)


def sig(value):
    return {
        "shape": [1, 2, 3],
        "dtype": "float32",
        "sum": 1.0,
        "mean": 1.0,
        "std": 0.0,
        "nonzero": 1,
        "sha256": value,
    }


def test_select_dry_run_candidate_record_requires_existing_changed_candidate(tmp_path):
    candidate_path = tmp_path / "candidate.png"
    candidate_path.write_bytes(b"placeholder")
    dry_run = {
        "records": [
            {
                "data_index": 9935,
                "frame_idx": 144,
                "candidate_raster_path": str(candidate_path),
                "candidate_signature": {"sha256": "abc123"},
                "baseline_matches_converter_signature": True,
                "candidate_differs_from_baseline": True,
                "diff_nonzero": 12,
                "operation": {"modified_visible_count": 6},
            }
        ]
    }

    selected = select_dry_run_candidate_record(dry_run, frame_index=0)

    assert selected["available"] is True
    assert selected["path"] == str(candidate_path)
    assert selected["expected_sha256"] == "abc123"
    assert selected["source"] == "candidate70_lane_divider_dry_run.candidate_raster_path"
    assert selected["provenance"] == "synthetic_projected_lane_divider_pixel_translation_dry_run"
    assert selected["claim_boundary"]["dry_run_candidate_is_synthetic_not_verified_map_geometry"] is True
    assert selected["claim_boundary"]["gpu_requires_separate_readiness_gate"] is True


def test_select_dry_run_candidate_record_rejects_unchanged_candidate(tmp_path):
    candidate_path = tmp_path / "candidate.png"
    candidate_path.write_bytes(b"placeholder")
    dry_run = {
        "records": [
            {
                "candidate_raster_path": str(candidate_path),
                "candidate_signature": {"sha256": "abc123"},
                "baseline_matches_converter_signature": True,
                "candidate_differs_from_baseline": False,
                "diff_nonzero": 0,
            }
        ]
    }

    selected = select_dry_run_candidate_record(dry_run, frame_index=0)

    assert selected["available"] is False
    assert selected["reason"] == "dry_run_candidate_not_eligible"


def test_dry_run_replacement_report_marks_grounding_surface_reached():
    report = build_report(
        baseline_signatures={
            "grounding_downsampler_input": sig("grounding_before"),
            "box_downsampler_input": sig("box_same"),
            "input_image": sig("image_same"),
        },
        replacement_signatures={
            "grounding_downsampler_input": sig("grounding_after"),
            "box_downsampler_input": sig("box_same"),
            "input_image": sig("image_same"),
        },
        override_audit={
            "available": True,
            "changed_counts": {"image_hdmap": 1},
            "entries_preview": [
                {
                    "applied": [
                        {
                            "target": "image_hdmap",
                            "mode": "replace_from_path",
                            "applied": True,
                            "path": "candidate.png",
                            "expected_sha256": "abc123",
                            "actual_sha256": "abc123",
                        }
                    ]
                }
            ],
        },
        dry_run_candidate={
            "available": True,
            "path": "candidate.png",
            "source": "candidate70_lane_divider_dry_run.candidate_raster_path",
            "provenance": "synthetic_projected_lane_divider_pixel_translation_dry_run",
            "expected_sha256": "abc123",
        },
    )

    assert report["schema_version"] == "candidate70_hdmap_dry_run_replacement_surface_audit.v0"
    assert report["status"] == "dry_run_raster_reaches_grounding_surface"
    assert report["does_not_run_gpu"] is True
    assert report["surfaces"]["image_hdmap_override"]["changed"] is True
    assert report["surfaces"]["grounding_downsampler_input"]["changed"] is True
    assert report["surfaces"]["box_downsampler_input"]["changed"] is False
    assert report["surfaces"]["input_image"]["changed"] is False
    assert report["claim"]["candidate70_dry_run_raster_reaches_grounding_downsampler_input"] is True
    assert report["claim"]["candidate70_true_lane_geometry_replacement_available"] is False
    assert report["claim"]["hdmap_lane_geometry_override_verified"] is False
    assert report["claim"]["lane_change_control_verified"] is False
    assert report["claim"]["runtime_motion_control_connected"] is False
    assert report["claim"]["semantic_success_claim_allowed"] is False
    assert report["claim_boundary"]["dry_run_candidate_is_synthetic_not_verified_map_geometry"] is True
    assert report["claim_boundary"]["gpu_requires_separate_readiness_gate"] is True
