import json

from scripts.run_refresh_all_audit_status import refresh_all


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_refresh_all_regenerates_audit_status_without_gpu(tmp_path):
    runtime_compare = write_json(
        tmp_path / "inputs" / "runtime_compare.json",
        {
            "runtime_tensor_hash_changed": {
                "prompt_embed": True,
                "box_downsampler_input": False,
                "grounding_downsampler_input": False,
                "img_cond": False,
            }
        },
    )
    motion_gap = write_json(
        tmp_path / "inputs" / "motion_gap.json",
        {"claim": {"lane_change_motion_tensor_control": "not_verified"}},
    )
    velocity_surface = write_json(
        tmp_path / "inputs" / "velocity.json",
        {"claim": {"velocity_consumed_by_dd2_runtime": False}},
    )
    trajectory_contract = tmp_path / "inputs" / "trajectory.md"
    trajectory_contract.write_text("trajectory control contract", encoding="utf-8")
    config_path = tmp_path / "inputs" / "config.py"
    config_path.write_text("config", encoding="utf-8")
    labels_path = tmp_path / "inputs" / "labels.pkl"
    labels_path.write_text("labels", encoding="utf-8")
    weights_path = tmp_path / "inputs" / "weights.bin"
    weights_path.write_text("weights", encoding="utf-8")
    evidence_index = tmp_path / "inputs" / "evidence.md"
    evidence_index.write_text("evidence", encoding="utf-8")
    claim_table = tmp_path / "inputs" / "claims.md"
    claim_table.write_text("claims", encoding="utf-8")
    artifact_dir = tmp_path / "candidate_output" / "artifacts" / "case"
    video_path = artifact_dir / "iteration_00.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_text("fake video artifact", encoding="utf-8")
    write_json(artifact_dir / "dd2_runtime_input_audit_00.json", {"status": "runtime_audit_available"})
    write_json(tmp_path / "post_gate" / "post_gpu_review_gate.json", {"status": "review_pack_ready"})
    write_json(
        tmp_path / "post_gate" / "manual_review_pack" / "manual_alignment_report.json",
        {"status": "reviewed"},
    )
    alignment_eval_file = tmp_path / "alignment_eval" / "case_manual_review" / "prompt_video_alignment_evaluation.json"
    write_json(
        alignment_eval_file,
        {"interpretation": {"video_semantic_claim": "measured_failed"}},
    )
    object_transfer = write_json(
        tmp_path / "inputs" / "object_transfer.json",
        {"status": "partially_verified"},
    )
    trajectory_surface = write_json(
        tmp_path / "inputs" / "trajectory_surface.json",
        {"status": "not_runtime_connected"},
    )
    runtime_surface_code = write_json(
        tmp_path / "inputs" / "runtime_surface_code.json",
        {"status": "not_runtime_connected"},
    )
    motion_metadata_runtime_audit = write_json(
        tmp_path / "inputs" / "motion_metadata_runtime_audit.json",
        {
            "motion_metadata": {
                "available": True,
                "velocities_available_in_batch_any": True,
                "actor_identity_available_in_batch_any": False,
                "boxes3d_available_in_batch_any": True,
                "per_frame_actor_boxes3d_observed_any": False,
                "claim": "metadata_observed_only_not_runtime_control",
            }
        },
    )
    actor_identity_surface_audit = write_json(
        tmp_path / "inputs" / "actor_identity_surface_audit.json",
        {
            "status": "identity_available_upstream_but_missing_from_processed_labels",
            "claim": {
                "actor_identity_available_in_processed_labels": False,
                "actor_identity_available_upstream": True,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            },
        },
    )
    candidate70_runtime_surface_audit = write_json(
        tmp_path / "inputs" / "candidate70_runtime_surface.json",
        {"status": "not_runtime_connected"},
    )
    candidate70_trajectory_surface_audit = write_json(
        tmp_path / "inputs" / "candidate70_trajectory_surface.json",
        {"status": "not_runtime_connected"},
    )
    candidate70_dry_run_replacement_audit = write_json(
        tmp_path / "inputs" / "candidate70_dry_run_replacement.json",
        {
            "claim": {
                "candidate70_dry_run_raster_reaches_grounding_downsampler_input": True,
                "candidate70_true_lane_geometry_replacement_available": False,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            }
        },
    )

    summary = refresh_all(
        prompt="daytime urban road with a motorcycle",
        scenario_id="case",
        output_dir=tmp_path / "candidate_output",
        readiness_output=tmp_path / "out" / "readiness.json",
        command_plan_output=tmp_path / "out" / "plan.json",
        runbook_output=tmp_path / "out" / "runbook.md",
        manifest_output=tmp_path / "out" / "manifest.json",
        validation_output=tmp_path / "out" / "validation.json",
        dashboard_output=tmp_path / "out" / "dashboard.json",
        summary_output=tmp_path / "out" / "summary.json",
        post_gate_dir=tmp_path / "post_gate",
        alignment_eval_dir=tmp_path / "alignment_eval",
        runtime_compare=runtime_compare,
        motion_gap=motion_gap,
        velocity_surface=velocity_surface,
        trajectory_contract_doc=trajectory_contract,
        config_path=config_path,
        labels_path=labels_path,
        weights_path=weights_path,
        evidence_index=evidence_index,
        claim_table=claim_table,
        prompt_object_transfer_audit=object_transfer,
        trajectory_runtime_surface_audit=trajectory_surface,
        runtime_surface_code_audit=runtime_surface_code,
        motion_metadata_runtime_audit=motion_metadata_runtime_audit,
        actor_identity_surface_audit=actor_identity_surface_audit,
        candidate70_prompt_bank_output=tmp_path / "out" / "candidate70_prompt_bank.json",
        candidate70_prompt_bank_support_audit_output=tmp_path / "out" / "candidate70_prompt_bank_support_audit.json",
        candidate70_accepted_prompt_selection=tmp_path / "out" / "missing_candidate70_accepted_prompt.json",
        candidate70_gpu_readiness_output=tmp_path / "out" / "candidate70_gpu_readiness.json",
        candidate70_runtime_surface_audit=candidate70_runtime_surface_audit,
        candidate70_trajectory_surface_audit=candidate70_trajectory_surface_audit,
        candidate70_dry_run_replacement_audit=candidate70_dry_run_replacement_audit,
    )

    assert summary["does_not_run_gpu"] is True
    assert summary["does_not_generate_video"] is True
    assert summary["semantic_success_claim_allowed"] is False
    assert summary["status_summary"]["gpu_smoke_allowed"] is True
    assert summary["status_summary"]["candidate_status"] == "candidate_video_only"
    assert summary["status_summary"]["bundle_status"] == "measured_ready"
    assert summary["status_summary"]["dashboard_status"] == "measured_ready"
    assert summary["status_summary"]["video_semantic_claim"] == "measured_failed"
    assert summary["status_summary"]["dashboard_semantic_success_claim_allowed"] is False
    assert summary["status_summary"]["object_transfer_status"] == "partially_verified"
    assert summary["status_summary"]["trajectory_runtime_surface_status"] == "not_runtime_connected"
    assert summary["status_summary"]["runtime_surface_code_audit_status"] == "not_runtime_connected"
    assert summary["status_summary"]["motion_metadata_runtime_status"] == "metadata_observed_not_runtime_control"
    assert summary["status_summary"]["actor_identity_surface_status"] == "identity_available_upstream_but_missing_from_processed_labels"
    assert summary["status_summary"]["candidate70_gpu_readiness_status"] == "blocked"
    assert summary["status_summary"]["candidate70_gpu_smoke_allowed"] is False
    assert "accepted_prompt_required_before_generate" in summary["status_summary"]["candidate70_gpu_readiness_blockers"]

    for artifact in summary["refreshed_artifacts"].values():
        assert artifact["exists_after_refresh"] is True

    dashboard = json.loads((tmp_path / "out" / "dashboard.json").read_text(encoding="utf-8"))
    assert dashboard["claim_boundary"]["video_generation_is_not_semantic_success"] is True
    assert dashboard["audit_signals"]["trajectory_or_temporal_motion_verified"] is False
    assert dashboard["summary"]["object_transfer_status"] == "partially_verified"
    assert dashboard["summary"]["trajectory_runtime_surface_status"] == "not_runtime_connected"
    assert dashboard["summary"]["runtime_surface_code_audit_status"] == "not_runtime_connected"
    assert dashboard["summary"]["motion_metadata_runtime_status"] == "metadata_observed_not_runtime_control"
    assert dashboard["audit_signals"]["actor_identity_available_in_batch_any"] is False
    assert dashboard["audit_signals"]["per_frame_actor_boxes3d_observed_any"] is False
    assert dashboard["summary"]["actor_identity_surface_status"] == "identity_available_upstream_but_missing_from_processed_labels"
