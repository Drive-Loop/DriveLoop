import json

from scripts.run_experiment_status_dashboard import build_dashboard


def write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_dashboard_reports_pre_gpu_ready_without_semantic_claim(tmp_path):
    readiness = write_json(
        tmp_path / "readiness.json",
        {
            "scenario_id": "case",
            "prompt": "prompt",
            "gpu_smoke_allowed": True,
            "semantic_claim_allowed": False,
        },
    )
    manifest = write_json(
        tmp_path / "manifest.json",
        {"candidate_status": "candidate_not_generated", "video_semantic_claim": "not_measured"},
    )
    bundle = write_json(tmp_path / "bundle.json", {"bundle_status": "blocked"})

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        candidate_audit_path=write_json(tmp_path / "candidate_audit.json", {"allowed": True, "status": "allowed"}),
        failure_taxonomy_path=write_json(tmp_path / "taxonomy.json", {"taxonomy_labels": ["lane_change_motion_failed"], "intervention_hints": ["audit trajectory"]}),
        prompt_object_transfer_audit_path=write_json(tmp_path / "object_transfer.json", {"status": "partially_verified"}),
        trajectory_runtime_surface_audit_path=write_json(tmp_path / "trajectory_surface.json", {"status": "not_runtime_connected"}),
        runtime_surface_code_audit_path=write_json(tmp_path / "runtime_surface_code.json", {"status": "not_runtime_connected"}),
    )

    assert dashboard["dashboard_status"] == "pre_gpu_ready"
    assert dashboard["summary"]["semantic_success_claim_allowed"] is False
    assert dashboard["claim_boundary"]["readiness_allows_gpu_candidate_only"] is True
    assert dashboard["claim_boundary"]["source_candidate_support_is_not_generation_success"] is True
    assert dashboard["summary"]["source_candidate_support_status"] == "allowed"
    assert dashboard["summary"]["source_candidate_support_allowed"] is True
    assert dashboard["summary"]["failure_taxonomy_labels"] == ["lane_change_motion_failed"]
    assert dashboard["summary"]["object_transfer_status"] == "partially_verified"
    assert dashboard["summary"]["trajectory_runtime_surface_status"] == "not_runtime_connected"
    assert dashboard["summary"]["runtime_surface_code_audit_status"] == "not_runtime_connected"
    assert dashboard["claim_boundary"]["failure_taxonomy_is_diagnostic_not_success_claim"] is True
    assert "gated GPU smoke candidate" in dashboard["next_recommended_action"]


def test_dashboard_promotes_candidate_and_review_states(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": True})
    manifest = write_json(
        tmp_path / "manifest.json",
        {"candidate_status": "candidate_video_only", "video_semantic_claim": "not_measured"},
    )
    bundle = write_json(tmp_path / "bundle.json", {"bundle_status": "review_ready"})

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        candidate_audit_path=write_json(tmp_path / "candidate_audit_review.json", {"allowed": True, "status": "allowed"}),
        failure_taxonomy_path=write_json(tmp_path / "taxonomy_review.json", {"taxonomy_labels": ["object_identity_failed"], "intervention_hints": ["audit object transfer"]}),
    )

    assert dashboard["dashboard_status"] == "review_ready"
    assert dashboard["summary"]["candidate_status"] == "candidate_video_only"
    assert dashboard["summary"]["bundle_status"] == "review_ready"
    assert dashboard["summary"]["semantic_success_claim_allowed"] is False


def test_dashboard_surfaces_audit_signals(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": True})
    manifest = write_json(tmp_path / "manifest.json", {})
    bundle = write_json(tmp_path / "bundle.json", {})
    runtime = write_json(tmp_path / "runtime.json", {"runtime_tensor_hash_changed": {"prompt_embed": True}})
    motion = write_json(tmp_path / "motion.json", {"claim": {"lane_change_motion_tensor_control": "not_verified"}})
    velocity = write_json(tmp_path / "velocity.json", {"claim": {"velocity_consumed_by_dd2_runtime": False}})

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=runtime,
        motion_gap_path=motion,
        velocity_audit_path=velocity,
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        candidate_audit_path=write_json(
            tmp_path / "candidate_audit_signals.json",
            {
                "allowed": False,
                "status": "blocked",
                "missing_requested_support": ["motorcycle"],
                "unrequested_selection_bias": ["rainy"],
            },
        ),
        failure_taxonomy_path=write_json(
            tmp_path / "taxonomy_signals.json",
            {
                "taxonomy_labels": ["motorcycle_identity_failed", "lane_change_motion_failed"],
                "intervention_hints": ["audit object transfer", "audit trajectory"],
            },
        ),
    )

    assert dashboard["audit_signals"]["runtime_tensor_hash_changed"] == {"prompt_embed": True}
    assert dashboard["audit_signals"]["lane_change_motion_tensor_control"] == "not_verified"
    assert dashboard["audit_signals"]["velocity_consumed_by_dd2_runtime"] is False
    assert dashboard["audit_signals"]["trajectory_or_temporal_motion_verified"] is False
    assert dashboard["audit_signals"]["prompt_conditional_candidate_allowed"] is False
    assert dashboard["audit_signals"]["prompt_conditional_candidate_status"] == "blocked"
    assert dashboard["audit_signals"]["prompt_conditional_candidate_missing_support"] == ["motorcycle"]
    assert dashboard["audit_signals"]["prompt_conditional_candidate_unrequested_bias"] == ["rainy"]
    assert dashboard["audit_signals"]["failure_taxonomy_labels"] == ["motorcycle_identity_failed", "lane_change_motion_failed"]
    assert dashboard["audit_signals"]["failure_taxonomy_intervention_hints"] == ["audit object transfer", "audit trajectory"]


def test_dashboard_surfaces_measured_failed_alignment_eval(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": True})
    manifest = write_json(
        tmp_path / "manifest.json",
        {"candidate_status": "candidate_video_only", "video_semantic_claim": "not_measured"},
    )
    bundle = write_json(tmp_path / "bundle.json", {"bundle_status": "measured_ready"})
    alignment = write_json(
        tmp_path / "alignment.json",
        {"interpretation": {"video_semantic_claim": "measured_failed"}},
    )

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        alignment_eval_path=alignment,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
    )

    assert dashboard["dashboard_status"] == "measured_ready"
    assert dashboard["summary"]["video_semantic_claim"] == "measured_failed"
    assert dashboard["summary"]["semantic_success_claim_allowed"] is False
    assert dashboard["sources"]["alignment_eval"]["exists"] is True


def test_dashboard_surfaces_object_transfer_and_trajectory_runtime_audits(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": True})
    manifest = write_json(tmp_path / "manifest.json", {})
    bundle = write_json(tmp_path / "bundle.json", {})
    object_transfer = write_json(
        tmp_path / "object_transfer.json",
        {
            "status": "partially_verified",
            "blockers": ["runtime_tensor_class_label_not_directly_observable"],
            "checks": {
                "runtime_tensor_class_labels": {
                    "class_label_observable": False,
                }
            },
        },
    )
    trajectory_surface = write_json(
        tmp_path / "trajectory_surface.json",
        {
            "status": "not_runtime_connected",
            "blockers": ["trajectory_tensor_not_observed_in_runtime_audit"],
            "surfaces": {
                "trajectory_tensor": {"available": False},
                "per_frame_actor_boxes3d": {"verified": False},
                "hdmap_lane_geometry": {"override_verified": False},
            },
        },
    )
    runtime_surface_code = write_json(
        tmp_path / "runtime_surface_code.json",
        {
            "status": "not_runtime_connected",
            "surfaces": {
                "dataset_velocity": {"status": "available_in_converter"},
                "dataset_lane_hdmap": {"status": "rasterized_image_hdmap_from_lane_geometry"},
                "direct_motion_runtime_surface": {"status": "not_observed"},
            },
        },
    )

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        prompt_object_transfer_audit_path=object_transfer,
        trajectory_runtime_surface_audit_path=trajectory_surface,
        runtime_surface_code_audit_path=runtime_surface_code,
    )

    assert dashboard["summary"]["object_transfer_status"] == "partially_verified"
    assert dashboard["summary"]["trajectory_runtime_surface_status"] == "not_runtime_connected"
    assert dashboard["audit_signals"]["object_transfer_blockers"] == [
        "runtime_tensor_class_label_not_directly_observable"
    ]
    assert dashboard["audit_signals"]["runtime_tensor_class_label_observable"] is False
    assert dashboard["audit_signals"]["trajectory_runtime_surface_blockers"] == [
        "trajectory_tensor_not_observed_in_runtime_audit"
    ]
    assert dashboard["audit_signals"]["trajectory_tensor_available"] is False
    assert dashboard["audit_signals"]["per_frame_actor_boxes3d_verified"] is False
    assert dashboard["audit_signals"]["hdmap_lane_geometry_override_verified"] is False
    assert dashboard["claim_boundary"]["object_transfer_audit_is_not_video_semantic_success"] is True
    assert dashboard["claim_boundary"]["trajectory_surface_audit_is_not_video_semantic_success"] is True
    assert dashboard["claim_boundary"]["runtime_surface_code_audit_is_not_video_semantic_success"] is True
    assert dashboard["audit_signals"]["dataset_velocity_status"] == "available_in_converter"
    assert dashboard["audit_signals"]["dataset_lane_hdmap_status"] == "rasterized_image_hdmap_from_lane_geometry"
    assert dashboard["audit_signals"]["direct_motion_runtime_surface_status"] == "not_observed"
    motion_metadata_audit = write_json(
        tmp_path / "motion_metadata_runtime_audit.json",
        {
            "motion_metadata": {
                "available": True,
                "velocities_available_in_batch_any": True,
                "velocities_available_in_batch_all": True,
                "actor_identity_available_in_batch_any": False,
                "boxes3d_available_in_batch_any": True,
                "per_frame_actor_boxes3d_observed_any": False,
                "claim": "metadata_observed_only_not_runtime_control",
            }
        },
    )
    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        prompt_object_transfer_audit_path=object_transfer,
        trajectory_runtime_surface_audit_path=trajectory_surface,
        runtime_surface_code_audit_path=runtime_surface_code,
        motion_metadata_runtime_audit_path=motion_metadata_audit,
    )
    assert dashboard["summary"]["motion_metadata_runtime_status"] == "metadata_observed_not_runtime_control"
    assert dashboard["summary"]["motion_metadata_claim"] == "metadata_observed_only_not_runtime_control"
    assert dashboard["audit_signals"]["motion_metadata_available"] is True
    assert dashboard["audit_signals"]["velocities_available_in_batch_any"] is True
    assert dashboard["audit_signals"]["actor_identity_available_in_batch_any"] is False
    assert dashboard["audit_signals"]["boxes3d_available_in_batch_any"] is True
    assert dashboard["audit_signals"]["per_frame_actor_boxes3d_observed_any"] is False
    assert dashboard["claim_boundary"]["motion_metadata_audit_is_not_runtime_motion_control"] is True
    assert dashboard["claim_boundary"]["motion_metadata_audit_is_not_video_semantic_success"] is True
    assert dashboard["sources"]["motion_metadata_runtime_audit"]["exists"] is True
    actor_identity_audit = write_json(
        tmp_path / "actor_identity_surface_audit.json",
        {
            "status": "identity_available_upstream_but_missing_from_processed_labels",
            "claim": {
                "actor_identity_available_in_processed_labels": False,
                "actor_identity_available_upstream": True,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            },
            "blockers": ["processed_labels_do_not_include_persistent_actor_identity"],
        },
    )
    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        prompt_object_transfer_audit_path=object_transfer,
        trajectory_runtime_surface_audit_path=trajectory_surface,
        runtime_surface_code_audit_path=runtime_surface_code,
        motion_metadata_runtime_audit_path=motion_metadata_audit,
        actor_identity_surface_audit_path=actor_identity_audit,
    )
    assert dashboard["summary"]["actor_identity_surface_status"] == "identity_available_upstream_but_missing_from_processed_labels"
    assert dashboard["summary"]["actor_identity_available_in_processed_labels"] is False
    assert dashboard["summary"]["actor_identity_available_upstream"] is True
    assert dashboard["audit_signals"]["actor_identity_surface_blockers"] == ["processed_labels_do_not_include_persistent_actor_identity"]
    assert dashboard["claim_boundary"]["actor_identity_surface_audit_is_not_runtime_motion_control"] is True
    assert dashboard["claim_boundary"]["actor_identity_surface_audit_is_not_video_semantic_success"] is True
    assert dashboard["sources"]["actor_identity_surface_audit"]["exists"] is True
    assert dashboard["sources"]["prompt_object_transfer_audit"]["exists"] is True
    assert dashboard["sources"]["trajectory_runtime_surface_audit"]["exists"] is True
    assert dashboard["sources"]["runtime_surface_code_audit"]["exists"] is True


def test_dashboard_surfaces_candidate70_converter_identity_subset(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": True})
    manifest = write_json(tmp_path / "manifest.json", {})
    bundle = write_json(tmp_path / "bundle.json", {})
    identity_summary = write_json(
        tmp_path / "candidate70_identity_summary.json",
        {
            "target_raw_instance_token": "target",
            "frame_count": 8,
            "all_frames_have_target": True,
            "claim": {"candidate70_converter_derived_identity_subset_created": True},
        },
    )
    actor_track = write_json(
        tmp_path / "candidate70_actor_track.json",
        {
            "status": "per_frame_actor_tracks_observed",
            "track_surface": {
                "tracks_preview": [
                    {"instance_token": "target", "observation_count": 8}
                ]
            },
        },
    )

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        candidate70_converter_identity_summary_path=identity_summary,
        candidate70_converter_actor_track_audit_path=actor_track,
    )

    assert dashboard["summary"]["candidate70_converter_identity_subset_created"] is True
    assert dashboard["summary"]["candidate70_converter_identity_all_frames_have_target"] is True
    assert dashboard["summary"]["candidate70_converter_identity_track_observed"] is True
    assert dashboard["summary"]["candidate70_target_motorcycle_track_covers_all_8_frames"] is True
    assert dashboard["summary"]["candidate70_full_processed_labels_rebuilt_with_identity"] is False
    assert dashboard["audit_signals"]["candidate70_identity_subset_is_not_runtime_motion_control"] is True
    assert dashboard["claim_boundary"]["actor_identity_surface_audit_is_not_runtime_motion_control"] is True

def test_dashboard_surfaces_candidate70_hdmap_raster_source_probe(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": True})
    manifest = write_json(tmp_path / "manifest.json", {})
    bundle = write_json(tmp_path / "bundle.json", {})
    hdmap_probe = write_json(
        tmp_path / "candidate70_hdmap_probe.json",
        {
            "frame_count": 2,
            "records": [
                {
                    "converter_signature": {"nonzero": 10},
                    "processed_matches": [{"matches_converter": True}, {"matches_converter": True}],
                },
                {
                    "converter_signature": {"nonzero": 12},
                    "processed_matches": [{"matches_converter": True}, {"matches_converter": True}],
                },
            ],
        },
    )

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        candidate70_hdmap_raster_probe_path=hdmap_probe,
    )

    assert dashboard["summary"]["candidate70_baseline_hdmap_raster_reproducible"] is True
    assert dashboard["summary"]["candidate70_processed_hdmap_matches_converter"] is True
    assert dashboard["summary"]["candidate70_verified_replacement_hdmap_raster_available"] is False
    assert dashboard["audit_signals"]["candidate70_hdmap_raster_probe_frame_count"] == 2
    assert dashboard["audit_signals"]["candidate70_hdmap_raster_probe_all_generated_nonzero"] is True
    assert dashboard["audit_signals"]["candidate70_hdmap_raster_probe_processed_match_true"] == 4
    assert dashboard["audit_signals"]["candidate70_hdmap_raster_probe_processed_match_false"] == 0
    assert dashboard["audit_signals"]["candidate70_hdmap_raster_source_probe_is_not_lane_geometry_override"] is True
    assert dashboard["claim_boundary"]["candidate70_hdmap_raster_source_probe_is_not_video_semantic_success"] is True
    assert dashboard["sources"]["candidate70_hdmap_raster_probe"]["exists"] is True


def test_dashboard_surfaces_candidate70_hdmap_replacement_surface_audit(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": False})
    manifest = write_json(tmp_path / "manifest.json", {})
    bundle = write_json(tmp_path / "bundle.json", {})
    hdmap_probe = write_json(
        tmp_path / "candidate70_hdmap_probe.json",
        {
            "frame_count": 1,
            "records": [
                {
                    "converter_signature": {"nonzero": 10},
                    "processed_matches": [{"matches_converter": True}],
                },
            ],
        },
    )
    replacement_audit = write_json(
        tmp_path / "candidate70_hdmap_replacement_surface_audit.json",
        {
            "status": "replacement_raster_reaches_grounding_surface",
            "does_not_run_gpu": True,
            "does_not_generate_video": True,
            "surfaces": {
                "image_hdmap_override": {"changed": True},
                "grounding_downsampler_input": {"changed": True},
            },
            "claim": {
                "candidate70_dry_run_raster_reaches_grounding_downsampler_input": True,
                "candidate70_verified_replacement_hdmap_raster_available": False,
                "hdmap_lane_geometry_override_verified": False,
                "lane_change_control_verified": False,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            },
        },
    )

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        candidate70_hdmap_raster_probe_path=hdmap_probe,
        candidate70_hdmap_replacement_surface_audit_path=replacement_audit,
    )

    assert dashboard["summary"]["candidate70_replacement_raster_reaches_grounding_downsampler_input"] is True
    assert dashboard["summary"]["candidate70_verified_replacement_hdmap_raster_available"] is False
    assert dashboard["audit_signals"]["candidate70_hdmap_replacement_surface_audit_status"] == "replacement_raster_reaches_grounding_surface"
    assert dashboard["audit_signals"]["candidate70_hdmap_replacement_audit_available"] is True
    assert dashboard["audit_signals"]["candidate70_hdmap_replacement_does_not_run_gpu"] is True
    assert dashboard["audit_signals"]["candidate70_hdmap_replacement_does_not_generate_video"] is True
    assert dashboard["audit_signals"]["candidate70_image_hdmap_override_changed"] is True
    assert dashboard["audit_signals"]["candidate70_replacement_grounding_downsampler_input_changed"] is True
    assert dashboard["audit_signals"]["candidate70_replacement_raster_reaches_grounding_downsampler_input"] is True
    assert dashboard["audit_signals"]["candidate70_hdmap_lane_geometry_override_verified"] is False
    assert dashboard["audit_signals"]["candidate70_lane_change_control_verified"] is False
    assert dashboard["audit_signals"]["candidate70_runtime_motion_control_connected"] is False
    assert dashboard["audit_signals"]["candidate70_semantic_success_claim_allowed"] is False
    assert dashboard["claim_boundary"]["candidate70_hdmap_replacement_surface_audit_is_not_lane_geometry_override"] is True
    assert dashboard["claim_boundary"]["candidate70_hdmap_replacement_surface_audit_is_not_video_semantic_success"] is True
    assert dashboard["sources"]["candidate70_hdmap_replacement_surface_audit"]["exists"] is True


def test_dashboard_surfaces_candidate70_dry_run_replacement_surface_audit(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": False})
    manifest = write_json(tmp_path / "manifest.json", {})
    bundle = write_json(tmp_path / "bundle.json", {})
    dry_run_audit = write_json(
        tmp_path / "candidate70_dry_run_replacement_surface_audit.json",
        {
            "status": "dry_run_raster_reaches_grounding_surface",
            "does_not_run_gpu": True,
            "does_not_generate_video": True,
            "surfaces": {
                "image_hdmap_override": {"changed": True},
                "grounding_downsampler_input": {"changed": True},
            },
            "claim": {
                "replacement_raster_reaches_grounding_downsampler_input": True,
                "hdmap_lane_geometry_override_verified": False,
                "lane_change_control_verified": False,
                "runtime_motion_control_connected": False,
                "semantic_success_claim_allowed": False,
            },
        },
    )

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        candidate70_dry_run_replacement_surface_audit_path=dry_run_audit,
    )

    assert dashboard["summary"]["candidate70_dry_run_raster_reaches_grounding_downsampler_input"] is True
    assert dashboard["summary"]["candidate70_true_lane_geometry_replacement_available"] is False
    assert dashboard["audit_signals"]["candidate70_dry_run_replacement_surface_audit_status"] == "dry_run_raster_reaches_grounding_surface"
    assert dashboard["audit_signals"]["candidate70_dry_run_replacement_audit_available"] is True
    assert dashboard["audit_signals"]["candidate70_dry_run_replacement_does_not_run_gpu"] is True
    assert dashboard["audit_signals"]["candidate70_dry_run_replacement_does_not_generate_video"] is True
    assert dashboard["audit_signals"]["candidate70_dry_run_image_hdmap_override_changed"] is True
    assert dashboard["audit_signals"]["candidate70_dry_run_grounding_downsampler_input_changed"] is True
    assert dashboard["audit_signals"]["candidate70_dry_run_raster_reaches_grounding_downsampler_input"] is True
    assert dashboard["audit_signals"]["candidate70_true_lane_geometry_replacement_available"] is False
    assert dashboard["audit_signals"]["candidate70_dry_run_hdmap_lane_geometry_override_verified"] is False
    assert dashboard["audit_signals"]["candidate70_dry_run_lane_change_control_verified"] is False
    assert dashboard["audit_signals"]["candidate70_dry_run_runtime_motion_control_connected"] is False
    assert dashboard["audit_signals"]["candidate70_dry_run_semantic_success_claim_allowed"] is False
    assert dashboard["claim_boundary"]["candidate70_dry_run_replacement_surface_audit_is_not_lane_geometry_override"] is True
    assert dashboard["claim_boundary"]["candidate70_dry_run_replacement_surface_audit_is_not_video_semantic_success"] is True
    assert dashboard["claim_boundary"]["candidate70_dry_run_gpu_requires_separate_readiness_gate"] is True
    assert dashboard["sources"]["candidate70_dry_run_replacement_surface_audit"]["exists"] is True


def test_dashboard_surfaces_candidate70_gpu_readiness_gate(tmp_path):
    readiness = write_json(tmp_path / "readiness.json", {"gpu_smoke_allowed": False})
    manifest = write_json(tmp_path / "manifest.json", {})
    bundle = write_json(tmp_path / "bundle.json", {})
    gate = write_json(
        tmp_path / "candidate70_gpu_readiness_gate.json",
        {
            "readiness_status": "blocked",
            "gpu_smoke_allowed": False,
            "blockers": [
                "accepted_prompt_required_before_generate",
                "runtime_motion_control_not_connected",
                "true_lane_geometry_replacement_not_available",
            ],
            "checks": {
                "accepted_prompt_selected": False,
                "runtime_motion_control_connected": False,
                "true_lane_geometry_replacement_available": False,
                "semantic_success_claim_allowed": False,
            },
            "claim_boundary": {
                "candidate70_readiness_gate_is_not_gpu_approval": True,
                "candidate70_readiness_gate_is_not_video_semantic_success": True,
                "accepted_prompt_required_before_generate": True,
            },
        },
    )

    dashboard = build_dashboard(
        readiness_path=readiness,
        manifest_path=manifest,
        bundle_validation_path=bundle,
        runtime_compare_path=tmp_path / "runtime.json",
        motion_gap_path=tmp_path / "motion.json",
        velocity_audit_path=tmp_path / "velocity.json",
        evidence_index_path=tmp_path / "index.md",
        claim_table_path=tmp_path / "claim.md",
        candidate70_gpu_readiness_gate_path=gate,
    )

    assert dashboard["summary"]["candidate70_gpu_readiness_status"] == "blocked"
    assert dashboard["summary"]["candidate70_gpu_smoke_allowed"] is False
    assert dashboard["summary"]["candidate70_gpu_readiness_blockers"] == [
        "accepted_prompt_required_before_generate",
        "runtime_motion_control_not_connected",
        "true_lane_geometry_replacement_not_available",
    ]
    assert dashboard["audit_signals"]["candidate70_gpu_readiness_status"] == "blocked"
    assert dashboard["audit_signals"]["candidate70_gpu_smoke_allowed"] is False
    assert dashboard["audit_signals"]["candidate70_accepted_prompt_selected"] is False
    assert dashboard["audit_signals"]["candidate70_readiness_runtime_motion_control_connected"] is False
    assert dashboard["audit_signals"]["candidate70_readiness_true_lane_geometry_replacement_available"] is False
    assert dashboard["audit_signals"]["candidate70_readiness_semantic_success_claim_allowed"] is False
    assert dashboard["claim_boundary"]["candidate70_readiness_gate_is_not_gpu_approval"] is True
    assert dashboard["claim_boundary"]["candidate70_readiness_gate_is_not_video_semantic_success"] is True
    assert dashboard["claim_boundary"]["candidate70_accepted_prompt_required_before_generate"] is True
    assert dashboard["sources"]["candidate70_gpu_readiness_gate"]["exists"] is True
