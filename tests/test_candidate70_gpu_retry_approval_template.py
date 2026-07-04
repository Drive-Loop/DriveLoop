import json
from pathlib import Path

from scripts.run_candidate70_gpu_retry_approval_template import build_approval_template, write_template


def candidate70_gate_payload():
    return {
        "schema_version": "driveloop_candidate70_gpu_readiness_gate.v0",
        "scenario_id": "candidate70_night_cut_in_gpu_smoke",
        "readiness_status": "blocked",
        "gpu_retry_gate": {
            "schema_version": "driveloop_candidate70_gpu_retry_gate.v0",
            "status": "blocked_requires_explicit_user_approval",
            "allowed": False,
            "requires_post_gpu_review": True,
            "does_not_claim_semantic_success": True,
            "blockers": ["explicit_gpu_retry_approval_missing"],
            "checks": {
                "source_bound_actor_motion_full_coverage_verified": True,
                "true_lane_geometry_replacement_available": True,
                "semantic_alignment_protocol_defined": True,
                "closed_loop_status_has_perception_measured_failed": True,
                "perception_eval_measured_failed": True,
                "explicit_gpu_retry_approved": False,
                "semantic_success_claim_allowed_remains_false": True,
            },
        },
    }


def test_candidate70_gpu_retry_approval_template_is_not_approved_by_default(tmp_path: Path):
    payload = build_approval_template(
        candidate70_gate_payload(),
        readiness_gate_path=tmp_path / "gate.json",
    )

    assert payload["approval_status"] == "template_not_approved"
    assert payload["approved_for_candidate70_gpu_retry"] is False
    assert payload["requires_post_gpu_review"] is True
    assert payload["approval_is_not_semantic_success"] is True
    assert payload["preconditions"]["ready_except_explicit_approval"] is True
    assert "explicit_user_approval_not_recorded" in payload["approval_blockers"]


def test_candidate70_gpu_retry_approval_can_record_explicit_approval(tmp_path: Path):
    payload = build_approval_template(
        candidate70_gate_payload(),
        readiness_gate_path=tmp_path / "gate.json",
        approve=True,
        approved_by="user",
        approval_note="explicit one-shot candidate70 retry approval",
    )

    assert payload["approval_status"] == "approved_for_one_short_gpu_retry"
    assert payload["approved_for_candidate70_gpu_retry"] is True
    assert payload["approved_by"] == "user"
    assert payload["approval_blockers"] == []
    assert payload["claim_boundary"]["approval_is_not_video_semantic_success"] is True


def test_candidate70_gpu_retry_approval_template_rejects_missing_preconditions(tmp_path: Path):
    gate = candidate70_gate_payload()
    gate["gpu_retry_gate"]["checks"]["perception_eval_measured_failed"] = False

    payload = build_approval_template(
        gate,
        readiness_gate_path=tmp_path / "gate.json",
        approve=True,
        approved_by="user",
        approval_note="try approval with missing perception evidence",
    )

    assert payload["approved_for_candidate70_gpu_retry"] is False
    assert "non_gpu_retry_preconditions_not_satisfied" in payload["approval_blockers"]
    assert "approval_rejected_by_gate_preconditions" in payload["approval_blockers"]


def test_candidate70_gpu_retry_approval_template_writes_json(tmp_path: Path):
    output = tmp_path / "approval.template.json"
    payload = build_approval_template(candidate70_gate_payload(), readiness_gate_path=tmp_path / "gate.json")

    write_template(output, payload)
    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert loaded["schema_version"] == "driveloop_candidate70_gpu_retry_approval.v0"
    assert loaded["approved_for_candidate70_gpu_retry"] is False
