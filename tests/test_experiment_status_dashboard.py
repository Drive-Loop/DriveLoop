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
    )

    assert dashboard["dashboard_status"] == "pre_gpu_ready"
    assert dashboard["summary"]["semantic_success_claim_allowed"] is False
    assert dashboard["claim_boundary"]["readiness_allows_gpu_candidate_only"] is True
    assert dashboard["claim_boundary"]["source_candidate_support_is_not_generation_success"] is True
    assert dashboard["summary"]["source_candidate_support_status"] == "allowed"
    assert dashboard["summary"]["source_candidate_support_allowed"] is True
    assert dashboard["summary"]["failure_taxonomy_labels"] == ["lane_change_motion_failed"]
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
