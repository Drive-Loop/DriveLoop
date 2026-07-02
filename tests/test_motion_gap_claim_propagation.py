import json
from pathlib import Path

from scripts.run_experiment_status_dashboard import build_dashboard
from scripts.run_gpu_smoke_readiness_gate import build_readiness_report
from scripts.run_trajectory_runtime_surface_audit import build_audit


def write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def motion_gap_payload() -> dict:
    return {
        "claim": {
            "lane_change_motion_tensor_control": "not_verified",
            "semantic_lane_change_claim": "not_allowed",
            "semantic_success_claim_allowed": False,
        },
        "control_path_status": {
            "image_box_condition": "connected",
            "boxes3d_target_override": "not_applied",
            "trajectory_tensor": "not_implemented",
            "temporal_actor_motion": "not_implemented",
            "semantic_lane_change_claim": "not_allowed",
            "velocity_motion_control": "observed_only_not_condition_tensor",
        },
    }


def test_gpu_smoke_gate_requires_new_motion_gap_claim_boundary(tmp_path: Path):
    runtime_compare = write_json(
        tmp_path / "runtime.json",
        {
            "runtime_tensor_hash_changed": {
                "prompt_embed": True,
                "box_downsampler_input": False,
                "grounding_downsampler_input": False,
                "img_cond": False,
            }
        },
    )
    motion_gap = write_json(tmp_path / "motion_gap.json", motion_gap_payload())
    velocity = write_json(
        tmp_path / "velocity.json",
        {"claim": {"velocity_consumed_by_dd2_runtime": False}},
    )
    contract = tmp_path / "contract.md"
    config = tmp_path / "config.py"
    labels = tmp_path / "labels.pkl"
    weights = tmp_path / "weights.bin"
    for path in [contract, config, labels, weights]:
        path.write_text("x", encoding="utf-8")

    report = build_readiness_report(
        prompt="motorcycle cut-in",
        scenario_id="candidate70",
        runtime_compare=runtime_compare,
        motion_gap=motion_gap,
        velocity_surface=velocity,
        trajectory_contract_doc=contract,
        config_path=config,
        labels_path=labels,
        weights_path=weights,
    )

    assert report["gpu_smoke_allowed"] is True
    assert report["semantic_claim_allowed"] is False
    assert report["evidence_checks"]["motion_gap_semantic_lane_change_claim"] == "not_allowed"
    assert report["evidence_checks"]["motion_gap_semantic_success_claim_allowed"] is False


def test_trajectory_audit_reads_direct_dd2_runtime_audit_and_keeps_motion_blocked():
    audit = build_audit(
        prompt="A motorcycle cuts in from the left lane.",
        backend_summary={
            "schema_version": "dd2_runtime_input_audit.v0",
            "box_downsampler_input": {"available": True},
            "grounding_downsampler_input": {"available": True},
        },
        velocity_audit={"claim": {"dataset_velocity_surface_available": True, "velocity_consumed_by_dd2_runtime": False}},
        motion_gap=motion_gap_payload(),
        actor_track_audit={"claim": {"per_frame_actor_identity_observed": False, "per_frame_actor_boxes3d_grouped_by_identity": False}},
    )

    assert audit["status"] == "not_runtime_connected"
    assert audit["surfaces"]["box_condition"]["available"] is True
    assert audit["surfaces"]["per_frame_actor_boxes3d"]["current_surface"] == "image_box_condition_only_not_per_frame_actor_motion"
    assert "target_boxes3d_override_not_applied" in audit["blockers"]
    assert "semantic_success_claim_not_allowed_by_motion_gap" in audit["blockers"]
    assert audit["source_signals"]["motion_gap_semantic_success_claim_allowed"] is False


def test_dashboard_exposes_motion_gap_claim_boundary(tmp_path: Path):
    readiness = write_json(
        tmp_path / "readiness.json",
        {"scenario_id": "candidate70", "prompt": "motorcycle cut-in", "gpu_smoke_allowed": False, "semantic_claim_allowed": False},
    )
    motion_gap = write_json(tmp_path / "motion_gap.json", motion_gap_payload())

    dashboard = build_dashboard(
        readiness_path=readiness,
        motion_gap_path=motion_gap,
        manifest_path=tmp_path / "missing_manifest.json",
        bundle_validation_path=tmp_path / "missing_bundle.json",
        alignment_eval_path=tmp_path / "missing_alignment.json",
        runtime_compare_path=tmp_path / "missing_runtime.json",
        velocity_audit_path=tmp_path / "missing_velocity.json",
        evidence_index_path=tmp_path / "missing_evidence.md",
        claim_table_path=tmp_path / "missing_claims.md",
        candidate_audit_path=tmp_path / "missing_candidate.json",
        failure_taxonomy_path=tmp_path / "missing_taxonomy.json",
        prompt_object_transfer_audit_path=tmp_path / "missing_transfer.json",
        trajectory_runtime_surface_audit_path=tmp_path / "missing_traj.json",
        runtime_surface_code_audit_path=tmp_path / "missing_code.json",
        motion_metadata_runtime_audit_path=tmp_path / "missing_motion_runtime.json",
        actor_identity_surface_audit_path=tmp_path / "missing_actor.json",
        candidate70_converter_identity_summary_path=tmp_path / "missing_identity.json",
        candidate70_converter_actor_track_audit_path=tmp_path / "missing_actor_track.json",
        candidate70_hdmap_raster_probe_path=tmp_path / "missing_hdmap_probe.json",
        candidate70_hdmap_replacement_surface_audit_path=tmp_path / "missing_hdmap_replace.json",
        candidate70_dry_run_replacement_surface_audit_path=tmp_path / "missing_hdmap_dry.json",
        candidate70_gpu_readiness_gate_path=tmp_path / "missing_gpu_gate.json",
        candidate70_gpu_smoke_plan_draft_path=tmp_path / "missing_plan.json",
        candidate70_source_sample_binding_readiness_path=tmp_path / "missing_binding.json",
    )

    assert dashboard["summary"]["motion_gap_semantic_lane_change_claim"] == "not_allowed"
    assert dashboard["summary"]["motion_gap_semantic_success_claim_allowed"] is False
    assert dashboard["summary"]["motion_gap_boxes3d_target_override"] == "not_applied"
    assert dashboard["audit_signals"]["velocity_motion_control"] == "observed_only_not_condition_tensor"
