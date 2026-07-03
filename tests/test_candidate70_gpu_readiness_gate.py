import json
from pathlib import Path

from scripts.run_candidate70_gpu_readiness_gate import build_candidate70_readiness_gate, write_gate


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_candidate70_gate_blocks_without_accepted_prompt_and_runtime_motion(tmp_path):
    prompt_bank = tmp_path / "prompt_bank.json"
    accepted_prompt = tmp_path / "accepted_prompt.json"
    runtime_surface = tmp_path / "runtime_surface.json"
    trajectory_surface = tmp_path / "trajectory_surface.json"
    dry_run = tmp_path / "dry_run.json"

    write_json(prompt_bank, {"accepted_for_generate_count": 0, "candidate70_allowed_count": 4})
    write_json(runtime_surface, {"status": "not_runtime_connected"})
    write_json(trajectory_surface, {"status": "not_runtime_connected"})
    write_json(
        dry_run,
        {
            "claim": {
                "candidate70_dry_run_raster_reaches_grounding_downsampler_input": True,
                "candidate70_true_lane_geometry_replacement_available": False,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            }
        },
    )

    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=prompt_bank,
        accepted_prompt_selection_path=accepted_prompt,
        runtime_surface_audit_path=runtime_surface,
        trajectory_surface_audit_path=trajectory_surface,
        dry_run_replacement_audit_path=dry_run,
    )

    assert gate["schema_version"] == "driveloop_candidate70_gpu_readiness_gate.v0"
    assert gate["gpu_smoke_allowed"] is False
    assert gate["readiness_status"] == "blocked"
    assert "accepted_prompt_required_before_generate" in gate["blockers"]
    assert "runtime_motion_control_not_connected" in gate["blockers"]
    assert "true_lane_geometry_replacement_not_available" in gate["blockers"]
    assert gate["checks"]["dry_run_raster_reaches_grounding_downsampler_input"] is True
    assert gate["claim_boundary"]["candidate70_readiness_gate_is_not_gpu_approval"] is True


def test_candidate70_gate_still_blocks_after_accepted_prompt_if_motion_missing(tmp_path):
    prompt_bank = tmp_path / "prompt_bank.json"
    accepted_prompt = tmp_path / "accepted_prompt.json"
    runtime_surface = tmp_path / "runtime_surface.json"
    trajectory_surface = tmp_path / "trajectory_surface.json"
    dry_run = tmp_path / "dry_run.json"

    write_json(prompt_bank, {"accepted_for_generate_count": 0, "candidate70_allowed_count": 4})
    write_json(accepted_prompt, {"accepted_prompt_selected": True, "accepted_for_generate": False})
    write_json(runtime_surface, {"status": "not_runtime_connected"})
    write_json(trajectory_surface, {"status": "not_runtime_connected"})
    write_json(
        dry_run,
        {
            "claim": {
                "candidate70_dry_run_raster_reaches_grounding_downsampler_input": True,
                "candidate70_true_lane_geometry_replacement_available": False,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            }
        },
    )

    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=prompt_bank,
        accepted_prompt_selection_path=accepted_prompt,
        runtime_surface_audit_path=runtime_surface,
        trajectory_surface_audit_path=trajectory_surface,
        dry_run_replacement_audit_path=dry_run,
    )

    assert gate["gpu_smoke_allowed"] is False
    assert "accepted_prompt_required_before_generate" not in gate["blockers"]
    assert "runtime_motion_control_not_connected" in gate["blockers"]
    assert "semantic_success_claim_not_allowed" in gate["blockers"]
    assert gate["checks"]["accepted_prompt_selected"] is True
    assert gate["checks"]["accepted_prompt_for_generate"] is False
    assert gate["sources"]["accepted_prompt_selection"]["exists"] is True


def test_candidate70_gate_writes_output(tmp_path):
    output = tmp_path / "gate.json"
    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=tmp_path / "missing_prompt_bank.json",
        accepted_prompt_selection_path=tmp_path / "missing_accepted_prompt.json",
        runtime_surface_audit_path=tmp_path / "missing_runtime.json",
        trajectory_surface_audit_path=tmp_path / "missing_trajectory.json",
        dry_run_replacement_audit_path=tmp_path / "missing_dry_run.json",
    )

    write_gate(output, gate)
    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert loaded["gpu_smoke_allowed"] is False
    assert loaded["sources"]["prompt_bank_audit"]["exists"] is False
    assert loaded["sources"]["accepted_prompt_selection"]["exists"] is False
    assert "candidate70_prompt_bank_audit_missing" in loaded["blockers"]


def test_candidate70_gate_records_boxes3d_structural_override_without_allowing_gpu(tmp_path):
    prompt_bank = tmp_path / "prompt_bank.json"
    accepted_prompt = tmp_path / "accepted_prompt.json"
    runtime_surface = tmp_path / "runtime_surface.json"
    trajectory_surface = tmp_path / "trajectory_surface.json"
    dry_run = tmp_path / "dry_run.json"

    write_json(prompt_bank, {"accepted_for_generate_count": 0, "candidate70_allowed_count": 4})
    write_json(accepted_prompt, {"accepted_prompt_selected": True, "accepted_for_generate": False})
    write_json(runtime_surface, {"status": "not_runtime_connected"})
    write_json(
        trajectory_surface,
        {
            "status": "not_runtime_connected",
            "surfaces": {
                "box_condition": {
                    "available": True,
                    "interpretation": "static/spatial conditioning only; does not prove temporal motion",
                },
                "trajectory_tensor": {"available": False},
            },
            "source_signals": {
                "motion_gap_boxes3d_target_override": "applied",
                "motion_gap_semantic_success_claim_allowed": False,
            },
            "blockers": [
                "trajectory_tensor_not_observed_in_runtime_audit",
                "static_box_condition_available_but_not_temporal_motion_control",
                "semantic_success_claim_not_allowed_by_motion_gap",
            ],
        },
    )
    write_json(
        dry_run,
        {
            "claim": {
                "candidate70_dry_run_raster_reaches_grounding_downsampler_input": True,
                "candidate70_true_lane_geometry_replacement_available": False,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            }
        },
    )

    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=prompt_bank,
        accepted_prompt_selection_path=accepted_prompt,
        runtime_surface_audit_path=runtime_surface,
        trajectory_surface_audit_path=trajectory_surface,
        dry_run_replacement_audit_path=dry_run,
    )

    assert gate["checks"]["boxes3d_target_override_applied"] is True
    assert gate["checks"]["image_box_condition_connected"] is True
    assert gate["checks"]["boxes3d_image_box_structural_override_ready"] is True
    assert gate["checks"]["static_box_condition_is_not_temporal_motion_control"] is True
    assert gate["gpu_smoke_allowed"] is False
    assert "trajectory_runtime_surface_not_connected" in gate["blockers"]
    assert gate["claim_boundary"]["boxes3d_image_box_structural_override_is_not_temporal_motion_control"] is True


def write_source_bound_actor_motion_evidence(root: Path):
    write_json(
        root / "case_summary.json",
        {
            "status": "accepted",
            "claim_boundary": {
                "dd2_audit_only_is_not_video_semantic_success": True,
                "semantic_success_claim_allowed": False,
            },
        },
    )
    write_json(
        root / "result.json",
        {
            "attempt_history": [
                {
                    "generation": {
                        "metadata": {
                            "dd2_source_sample_binding": {
                                "ready": True,
                                "selector": {"source_candidate_id": "candidate70"},
                            },
                            "actor_motion_frame_mapping": {
                                "available": True,
                                "mode": "source_bound_relative_step_to_sample_identity",
                                "source_identity_count": 48,
                                "input_per_frame_count": 4,
                                "mapped_entry_count": 24,
                                "unmapped_relative_frame_idx": [],
                            },
                            "trace_metadata": {
                                "tensor_control_ready": True,
                                "actor_motion_surface_ready": True,
                                "limitations": ["velocity_or_displacement_tensor_not_connected"],
                            },
                        }
                    }
                }
            ]
        },
    )
    audit_path = root / "artifacts" / "dd2_override_audit_00.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps(
            {
                "changed": {
                    "boxes3d": True,
                    "image_box": True,
                    "image_hdmap": False,
                    "scene_description": True,
                },
                "applied": [
                    {"target": "scene_description", "mode": "replace", "source": "text_control.prompt"},
                    {
                        "target": "boxes3d",
                        "mode": "per_frame_append",
                        "accepted_count": 1,
                        "accepted_entries": [
                            {
                                "relative_frame_idx": 0,
                                "source_record_index": 24,
                                "sample_identity": {
                                    "cam_type": "cam_front",
                                    "frame_idx": 144,
                                    "sample_token": "sample",
                                    "scene_token": "scene",
                                },
                            }
                        ],
                    },
                ],
                "skipped": [{"target": "image_hdmap", "reason": "no_verified_hdmap_override_source"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_candidate70_gate_clears_motion_surface_blockers_with_source_bound_actor_motion_evidence(tmp_path):
    prompt_bank = tmp_path / "prompt_bank.json"
    accepted_prompt = tmp_path / "accepted_prompt.json"
    runtime_surface = tmp_path / "runtime_surface.json"
    trajectory_surface = tmp_path / "trajectory_surface.json"
    dry_run = tmp_path / "dry_run.json"
    actor_motion_root = tmp_path / "actor_motion_audit"

    write_json(prompt_bank, {"accepted_for_generate_count": 0, "candidate70_allowed_count": 4})
    write_json(accepted_prompt, {"accepted_prompt_selected": True, "accepted_for_generate": False})
    write_json(runtime_surface, {"status": "not_runtime_connected"})
    write_json(trajectory_surface, {"status": "not_runtime_connected"})
    write_json(
        dry_run,
        {
            "claim": {
                "candidate70_dry_run_raster_reaches_grounding_downsampler_input": True,
                "candidate70_true_lane_geometry_replacement_available": False,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            }
        },
    )
    write_source_bound_actor_motion_evidence(actor_motion_root)

    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=prompt_bank,
        accepted_prompt_selection_path=accepted_prompt,
        runtime_surface_audit_path=runtime_surface,
        trajectory_surface_audit_path=trajectory_surface,
        dry_run_replacement_audit_path=dry_run,
        source_bound_actor_motion_audit_path=actor_motion_root,
    )

    assert gate["gpu_smoke_allowed"] is False
    assert "runtime_motion_control_not_connected" not in gate["blockers"]
    assert "trajectory_runtime_surface_not_connected" not in gate["blockers"]
    assert "runtime_motion_control_claim_not_allowed" not in gate["blockers"]
    assert "true_lane_geometry_replacement_not_available" in gate["blockers"]
    assert "semantic_success_claim_not_allowed" in gate["blockers"]
    assert gate["checks"]["source_bound_actor_motion_runtime_connected"] is True
    assert gate["checks"]["source_bound_actor_motion_sample_identity_verified"] is True
    assert gate["evidence"]["source_bound_actor_motion"]["connected"] is True
    assert gate["claim_boundary"]["source_bound_actor_motion_audit_is_not_video_semantic_success"] is True



def write_local_map_vector_hdmap_surface_audit(path: Path):
    write_json(
        path,
        {
            "schema_version": "candidate70_hdmap_lane_geometry_replacement_surface_audit.v1",
            "status": "local_map_vector_lane_geometry_replacement_reaches_grounding_surface",
            "candidate_source": {
                "available": True,
                "frame_index": 0,
                "data_index": 9935,
                "frame_idx": 144,
                "path_exists": True,
                "expected_sha256": "sha",
                "operation": {
                    "operation": "offset_lane_divider_local_map_vector_before_camera_projection",
                    "coordinate_frame": "ego_aligned_local_map_patch",
                    "modified_visible_count": 6,
                },
                "provenance": "ego_aligned_local_map_vector_offset_before_camera_projection",
            },
            "surfaces": {
                "image_hdmap_override": {"changed": True},
                "grounding_downsampler_input": {"changed": True},
                "box_downsampler_input": {"changed": False},
                "input_image": {"changed": False},
            },
            "claim": {
                "candidate70_local_map_vector_lane_geometry_replacement_reaches_grounding_downsampler_input": True,
                "candidate70_true_lane_geometry_replacement_available": True,
                "hdmap_lane_geometry_override_verified": True,
                "semantic_success_claim_allowed": False,
            },
            "claim_boundary": {
                "runtime_tensor_audit_is_not_video_semantic_success": True,
            },
        },
    )


def test_candidate70_gate_clears_hdmap_blocker_with_local_map_vector_replacement_surface_evidence(tmp_path):
    prompt_bank = tmp_path / "prompt_bank.json"
    accepted_prompt = tmp_path / "accepted_prompt.json"
    runtime_surface = tmp_path / "runtime_surface.json"
    trajectory_surface = tmp_path / "trajectory_surface.json"
    dry_run = tmp_path / "dry_run.json"
    actor_motion_root = tmp_path / "actor_motion_audit"
    hdmap_audit = tmp_path / "local_map_vector_hdmap.json"

    write_json(prompt_bank, {"accepted_for_generate_count": 0, "candidate70_allowed_count": 4})
    write_json(accepted_prompt, {"accepted_prompt_selected": True, "accepted_for_generate": False})
    write_json(runtime_surface, {"status": "not_runtime_connected"})
    write_json(trajectory_surface, {"status": "not_runtime_connected"})
    write_json(
        dry_run,
        {
            "claim": {
                "candidate70_dry_run_raster_reaches_grounding_downsampler_input": True,
                "candidate70_true_lane_geometry_replacement_available": False,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            }
        },
    )
    write_source_bound_actor_motion_evidence(actor_motion_root)
    write_local_map_vector_hdmap_surface_audit(hdmap_audit)

    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=prompt_bank,
        accepted_prompt_selection_path=accepted_prompt,
        runtime_surface_audit_path=runtime_surface,
        trajectory_surface_audit_path=trajectory_surface,
        dry_run_replacement_audit_path=dry_run,
        source_bound_actor_motion_audit_path=actor_motion_root,
        local_map_vector_hdmap_audit_path=hdmap_audit,
    )

    assert gate["gpu_smoke_allowed"] is False
    assert "runtime_motion_control_not_connected" not in gate["blockers"]
    assert "trajectory_runtime_surface_not_connected" not in gate["blockers"]
    assert "runtime_motion_control_claim_not_allowed" not in gate["blockers"]
    assert "true_lane_geometry_replacement_not_available" not in gate["blockers"]
    assert gate["blockers"] == ["semantic_success_claim_not_allowed"]
    assert gate["checks"]["true_lane_geometry_replacement_available"] is True
    assert gate["checks"]["local_map_vector_hdmap_reaches_grounding_surface"] is True
    assert gate["checks"]["local_map_vector_hdmap_lane_geometry_override_verified"] is True
    assert gate["evidence"]["local_map_vector_hdmap"]["true_lane_geometry_replacement_available"] is True
    assert gate["claim_boundary"]["local_map_vector_hdmap_replacement_is_not_video_semantic_success"] is True



def write_candidate70_semantic_alignment_protocol(path: Path):
    write_json(
        path,
        {
            "schema_version": "driveloop_candidate70_semantic_alignment_protocol.v0",
            "status": "protocol_defined",
            "does_not_run_gpu": True,
            "does_not_generate_video": True,
            "semantic_success_claim_allowed": False,
            "required_semantic_checks": [
                {"name": "artifact.video_available_and_decodable", "required": True},
                {"name": "object_presence.motorcycle_or_scooter_visible", "required": True},
                {"name": "object_consistency.target_actor_trackable_across_frames", "required": True},
                {"name": "maneuver.cut_in_from_left_toward_ego_visible", "required": True},
                {"name": "temporal_motion.lateral_displacement_visible", "required": True},
            ],
            "measurement_acceptance_rule": {
                "report_status_must_be_measured": True,
                "all_required_checks_must_pass": True,
            },
            "claim_boundary": {
                "protocol_definition_is_not_video_semantic_success": True,
            },
        },
    )


def test_candidate70_gate_records_semantic_alignment_protocol_evidence(tmp_path):
    prompt_bank = tmp_path / "prompt_bank.json"
    accepted_prompt = tmp_path / "accepted_prompt.json"
    runtime_surface = tmp_path / "runtime_surface.json"
    trajectory_surface = tmp_path / "trajectory_surface.json"
    dry_run = tmp_path / "dry_run.json"
    actor_motion_root = tmp_path / "actor_motion_audit"
    hdmap_audit = tmp_path / "local_map_vector_hdmap.json"
    semantic_protocol = tmp_path / "semantic_protocol.json"

    write_json(prompt_bank, {"accepted_for_generate_count": 0, "candidate70_allowed_count": 4})
    write_json(accepted_prompt, {"accepted_prompt_selected": True, "accepted_for_generate": False})
    write_json(runtime_surface, {"status": "not_runtime_connected"})
    write_json(trajectory_surface, {"status": "not_runtime_connected"})
    write_json(dry_run, {"claim": {"semantic_success_claim_allowed": False}})
    write_source_bound_actor_motion_evidence(actor_motion_root)
    write_local_map_vector_hdmap_surface_audit(hdmap_audit)
    write_candidate70_semantic_alignment_protocol(semantic_protocol)

    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=prompt_bank,
        accepted_prompt_selection_path=accepted_prompt,
        runtime_surface_audit_path=runtime_surface,
        trajectory_surface_audit_path=trajectory_surface,
        dry_run_replacement_audit_path=dry_run,
        source_bound_actor_motion_audit_path=actor_motion_root,
        local_map_vector_hdmap_audit_path=hdmap_audit,
        semantic_alignment_protocol_path=semantic_protocol,
    )

    assert gate["checks"]["semantic_alignment_protocol_exists"] is True
    assert gate["checks"]["semantic_alignment_protocol_defined"] is True
    assert gate["evidence"]["semantic_alignment_protocol"]["required_check_count"] == 5
    assert gate["sources"]["semantic_alignment_protocol"]["exists"] is True
    assert gate["gpu_smoke_allowed"] is False
    assert "semantic_success_claim_not_allowed" in gate["blockers"]
    assert gate["claim_boundary"]["semantic_alignment_protocol_is_not_video_semantic_success"] is True
