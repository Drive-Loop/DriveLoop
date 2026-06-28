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
    )

    assert dashboard["dashboard_status"] == "pre_gpu_ready"
    assert dashboard["summary"]["semantic_success_claim_allowed"] is False
    assert dashboard["claim_boundary"]["readiness_allows_gpu_candidate_only"] is True
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
    )

    assert dashboard["audit_signals"]["runtime_tensor_hash_changed"] == {"prompt_embed": True}
    assert dashboard["audit_signals"]["lane_change_motion_tensor_control"] == "not_verified"
    assert dashboard["audit_signals"]["velocity_consumed_by_dd2_runtime"] is False
    assert dashboard["audit_signals"]["trajectory_or_temporal_motion_verified"] is False
