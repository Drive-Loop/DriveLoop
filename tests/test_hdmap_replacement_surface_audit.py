from scripts.run_hdmap_replacement_surface_audit import (
    build_report,
    select_verified_raster_record,
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


def test_select_verified_raster_record_requires_existing_matched_source(tmp_path):
    raster_path = tmp_path / "candidate70_hdmap.png"
    raster_path.write_bytes(b"placeholder")
    probe = {
        "records": [
            {
                "data_index": 9935,
                "frame_idx": 144,
                "converter_hdmap_path": str(raster_path),
                "converter_signature": {
                    "nonzero": 10,
                    "sha256": "abc123",
                },
                "processed_matches": [
                    {"matches_converter": True},
                    {"matches_converter": True},
                ],
            }
        ]
    }

    selected = select_verified_raster_record(probe, frame_index=0)

    assert selected["verified"] is True
    assert selected["path"] == str(raster_path)
    assert selected["expected_sha256"] == "abc123"
    assert selected["processed_match_true"] == 2
    assert selected["processed_match_false"] == 0
    assert selected["provenance"] == "converter_generated_raster_matches_processed_hdmap_lmdb_by_sha256"


def test_select_verified_raster_record_rejects_processed_mismatch(tmp_path):
    raster_path = tmp_path / "candidate70_hdmap.png"
    raster_path.write_bytes(b"placeholder")
    probe = {
        "records": [
            {
                "converter_hdmap_path": str(raster_path),
                "converter_signature": {
                    "nonzero": 10,
                    "sha256": "abc123",
                },
                "processed_matches": [
                    {"matches_converter": True},
                    {"matches_converter": False},
                ],
            }
        ]
    }

    selected = select_verified_raster_record(probe, frame_index=0)

    assert selected["verified"] is False
    assert selected["reason"] == "unverified_raster_source"
    assert selected["processed_match_false"] == 1


def test_replacement_report_marks_grounding_surface_reached():
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
                            "path": "verified.png",
                            "expected_sha256": "abc123",
                            "actual_sha256": "abc123",
                        }
                    ]
                }
            ],
        },
        verified_raster={
            "verified": True,
            "path": "verified.png",
            "source": "candidate70_hdmap_raster_probe.converter_hdmap_path",
            "provenance": "converter_generated_raster_matches_processed_hdmap_lmdb_by_sha256",
            "expected_sha256": "abc123",
        },
    )

    assert report["schema_version"] == "driveloop_hdmap_replacement_surface_audit.v0"
    assert report["status"] == "replacement_raster_reaches_grounding_surface"
    assert report["does_not_run_gpu"] is True
    assert report["does_not_generate_video"] is True
    assert report["surfaces"]["image_hdmap_override"]["changed"] is True
    assert report["surfaces"]["grounding_downsampler_input"]["changed"] is True
    assert report["surfaces"]["box_downsampler_input"]["changed"] is False
    assert report["surfaces"]["input_image"]["changed"] is False
    assert report["claim"]["replacement_raster_reaches_grounding_downsampler_input"] is True
    assert report["claim"]["candidate70_verified_replacement_hdmap_raster_available"] is False
    assert report["claim"]["hdmap_lane_geometry_override_verified"] is False
    assert report["claim"]["lane_change_control_verified"] is False
    assert report["claim"]["runtime_motion_control_connected"] is False
    assert report["claim"]["semantic_success_claim_allowed"] is False
    assert report["claim_boundary"]["verified_raster_replacement_is_not_lane_geometry_override"] is True
    assert report["claim_boundary"]["grounding_surface_hash_change_is_not_lane_change_control"] is True


def test_replacement_report_stays_not_observed_without_grounding_change():
    report = build_report(
        baseline_signatures={
            "grounding_downsampler_input": sig("grounding_same"),
            "box_downsampler_input": sig("box_same"),
            "input_image": sig("image_same"),
        },
        replacement_signatures={
            "grounding_downsampler_input": sig("grounding_same"),
            "box_downsampler_input": sig("box_same"),
            "input_image": sig("image_same"),
        },
        override_audit={
            "available": True,
            "changed_counts": {"image_hdmap": 1},
        },
        verified_raster={
            "verified": True,
            "path": "verified.png",
            "source": "candidate70_hdmap_raster_probe.converter_hdmap_path",
            "provenance": "converter_generated_raster_matches_processed_hdmap_lmdb_by_sha256",
            "expected_sha256": "abc123",
        },
    )

    assert report["status"] == "not_observed"
    assert report["claim"]["replacement_raster_reaches_grounding_downsampler_input"] is False
    assert report["claim"]["hdmap_lane_geometry_override_verified"] is False
    assert report["claim"]["semantic_success_claim_allowed"] is False
