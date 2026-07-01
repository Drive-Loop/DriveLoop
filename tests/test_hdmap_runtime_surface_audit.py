from scripts.run_hdmap_runtime_surface_audit import build_report


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


def test_hdmap_zero_ablation_marks_grounding_surface_mutable():
    report = build_report(
        baseline_signatures={
            "grounding_downsampler_input": sig("grounding_before"),
            "box_downsampler_input": sig("box_same"),
            "input_image": sig("image_same"),
        },
        zero_signatures={
            "grounding_downsampler_input": sig("grounding_after"),
            "box_downsampler_input": sig("box_same"),
            "input_image": sig("image_same"),
        },
        override_audit={
            "available": True,
            "changed_counts": {"image_hdmap": 1},
        },
    )

    assert report["schema_version"] == "driveloop_hdmap_runtime_surface_audit.v0"
    assert report["status"] == "hdmap_raster_runtime_surface_mutable"
    assert report["does_not_run_gpu"] is True
    assert report["does_not_generate_video"] is True
    assert report["surfaces"]["image_hdmap_override"]["changed"] is True
    assert report["surfaces"]["grounding_downsampler_input"]["changed"] is True
    assert report["surfaces"]["box_downsampler_input"]["changed"] is False
    assert report["surfaces"]["input_image"]["changed"] is False
    assert report["claim"]["hdmap_raster_runtime_surface_mutable"] is True
    assert report["claim"]["hdmap_lane_geometry_override_verified"] is False
    assert report["claim"]["lane_change_control_verified"] is False
    assert report["claim"]["runtime_motion_control_connected"] is False
    assert report["claim"]["semantic_success_claim_allowed"] is False
    assert report["claim_boundary"]["zero_hdmap_ablation_is_not_lane_geometry_override"] is True
    assert report["claim_boundary"]["hdmap_raster_hash_change_is_not_lane_change_control"] is True


def test_hdmap_audit_stays_not_observed_without_grounding_change():
    report = build_report(
        baseline_signatures={
            "grounding_downsampler_input": sig("grounding_same"),
            "box_downsampler_input": sig("box_same"),
            "input_image": sig("image_same"),
        },
        zero_signatures={
            "grounding_downsampler_input": sig("grounding_same"),
            "box_downsampler_input": sig("box_same"),
            "input_image": sig("image_same"),
        },
        override_audit={
            "available": True,
            "changed_counts": {"image_hdmap": 1},
        },
    )

    assert report["status"] == "not_observed"
    assert report["claim"]["hdmap_raster_runtime_surface_mutable"] is False
    assert report["claim"]["hdmap_lane_geometry_override_verified"] is False
