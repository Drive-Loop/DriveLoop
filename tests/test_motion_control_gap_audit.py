import json
from pathlib import Path

from scripts.run_motion_control_gap_audit import build_motion_control_gap_report


def test_motion_control_gap_audit_records_static_box_not_temporal_motion(tmp_path: Path):
    summary = tmp_path / "backend_audit_only_summary.json"
    paper = tmp_path / "paper_alignment_report_00.json"

    summary.write_text(
        json.dumps(
            {
                "scenario_id": "motorcycle_manual_feedback_dd2_audit_only",
                "prompt": "daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.",
                "runtime_input_audit": {
                    "prompt_override": "daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.",
                    "prompt_embed": {"sha256": "prompt_hash"},
                    "box_downsampler_input": {"sha256": "box_hash"},
                    "grounding_downsampler_input": {"sha256": "grounding_hash"},
                    "img_cond": {"sha256": "image_hash"},
                },
                "override_audit": {
                    "changed_counts": {
                        "boxes3d": 48,
                        "image_box": 48,
                        "scene_description": 48,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    paper.write_text(
        json.dumps(
            {
                "stage_3_scene_consistent_generation": {
                    "structural_input_plan": {
                        "image_hdmap": {"source": "mini_dataset_baseline"},
                        "image_box": {"source": "derived_from_boxes3d_override"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    report = build_motion_control_gap_report(summary)

    assert report["schema_version"] == "driveloop_motion_control_gap_audit.v0"
    assert report["observed_signals"]["runtime_hashes"]["prompt_embed"] == "prompt_hash"
    assert report["observed_signals"]["override_changed_counts"]["boxes3d"] == 48
    assert report["control_path_status"]["text_prompt"] == "connected"
    assert report["control_path_status"]["scene_description"] == "connected"
    assert report["control_path_status"]["boxes3d_static_actor"] == "connected_as_static_draft_box"
    assert report["control_path_status"]["image_box"] == "derived_from_boxes3d_override"
    assert report["control_path_status"]["image_hdmap"] == "mini_dataset_baseline"
    assert report["control_path_status"]["trajectory_tensor"] == "not_implemented"
    assert report["control_path_status"]["temporal_actor_motion"] == "not_implemented"
    assert report["claim"]["lane_change_motion_tensor_control"] == "not_verified"
