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
                    "motion_metadata": {
                        "available": True,
                        "velocities_available_in_batch_any": True,
                        "actor_identity_available_in_batch_any": False,
                        "boxes3d_available_in_batch_any": True,
                        "per_frame_actor_boxes3d_observed_any": False,
                        "claim": "metadata_observed_only_not_runtime_control",
                    },
                },
                "override_audit": {
                    "changed_counts": {
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
                        "image_hdmap": {"source": "runtime_dataset_baseline"},
                        "image_box": {"source": "derived_from_runtime_boxes3d_canvas"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    report = build_motion_control_gap_report(summary)

    assert report["schema_version"] == "driveloop_motion_control_gap_audit.v0"
    assert report["observed_signals"]["runtime_hashes"]["prompt_embed"] == "prompt_hash"
    assert report["observed_signals"]["override_changed_counts"]["scene_description"] == 48
    assert "boxes3d" not in report["observed_signals"]["override_changed_counts"]
    assert report["control_path_status"]["text_prompt"] == "connected"
    assert report["control_path_status"]["scene_description"] == "connected"
    assert report["control_path_status"]["image_box_condition"] == "connected"
    assert report["control_path_status"]["boxes3d_target_override"] == "not_applied"
    assert report["control_path_status"]["boxes3d_static_actor"] == "not_applied"
    assert report["control_path_status"]["image_box"] == "derived_from_runtime_boxes3d_canvas"
    assert report["control_path_status"]["image_hdmap"] == "runtime_dataset_baseline"
    assert report["control_path_status"]["velocity_motion_control"] == "observed_only_not_condition_tensor"
    assert report["control_path_status"]["actor_identity"] == "not_observed"
    assert report["control_path_status"]["trajectory_tensor"] == "not_implemented"
    assert report["control_path_status"]["temporal_actor_motion"] == "not_implemented"
    assert report["control_path_status"]["semantic_lane_change_claim"] == "not_allowed"
    assert report["claim"]["lane_change_motion_tensor_control"] == "not_verified"
    assert report["claim"]["semantic_success_claim_allowed"] is False


def test_motion_control_gap_audit_accepts_direct_dd2_runtime_audit(tmp_path: Path):
    runtime = tmp_path / "dd2_runtime_input_audit_00.json"
    override = tmp_path / "dd2_override_audit_00.jsonl"
    paper = tmp_path / "paper_alignment_report_00.json"

    runtime.write_text(
        json.dumps(
            {
                "schema_version": "dd2_runtime_input_audit.v0",
                "prompt_override": "motorcycle lane change request",
                "prompt_embed": {"sha256": "prompt_hash"},
                "box_downsampler_input": {"available": True, "sha256": "box_hash"},
                "motion_metadata": {
                    "available": True,
                    "velocities_available_in_batch_any": True,
                    "actor_identity_available_in_batch_any": False,
                    "per_frame_actor_boxes3d_observed_any": False,
                    "claim": "metadata_observed_only_not_runtime_control",
                },
            }
        ),
        encoding="utf-8",
    )
    override.write_text(
        json.dumps(
            {
                "changed": {
                    "scene_description": True,
                    "boxes3d": False,
                    "image_hdmap": False,
                },
                "image_box_expected_changed": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    paper.write_text(
        json.dumps(
            {
                "stage_3_scene_consistent_generation": {
                    "structural_input_plan": {
                        "image_hdmap": {"source": "runtime_dataset_baseline"},
                        "image_box": {"source": "derived_from_runtime_boxes3d_canvas"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    report = build_motion_control_gap_report(runtime, paper)

    assert report["prompt"] == "motorcycle lane change request"
    assert report["observed_signals"]["override_changed_counts"]["scene_description"] == 1
    assert "boxes3d" not in report["observed_signals"]["override_changed_counts"]
    assert report["control_path_status"]["image_box_condition"] == "connected"
    assert report["control_path_status"]["boxes3d_target_override"] == "not_applied"
    assert report["control_path_status"]["velocity_motion_control"] == "observed_only_not_condition_tensor"
    assert report["claim"]["semantic_success_claim_allowed"] is False
