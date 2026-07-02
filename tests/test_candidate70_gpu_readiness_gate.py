import json
from pathlib import Path

from scripts.run_candidate70_gpu_readiness_gate import build_candidate70_readiness_gate, write_gate


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_candidate70_gate_blocks_without_accepted_prompt_and_runtime_motion(tmp_path):
    prompt_bank = tmp_path / "prompt_bank.json"
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
    runtime_surface = tmp_path / "runtime_surface.json"
    trajectory_surface = tmp_path / "trajectory_surface.json"
    dry_run = tmp_path / "dry_run.json"

    write_json(prompt_bank, {"accepted_for_generate_count": 1, "candidate70_allowed_count": 4})
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
        runtime_surface_audit_path=runtime_surface,
        trajectory_surface_audit_path=trajectory_surface,
        dry_run_replacement_audit_path=dry_run,
    )

    assert gate["gpu_smoke_allowed"] is False
    assert "accepted_prompt_required_before_generate" not in gate["blockers"]
    assert "runtime_motion_control_not_connected" in gate["blockers"]
    assert "semantic_success_claim_not_allowed" in gate["blockers"]


def test_candidate70_gate_writes_output(tmp_path):
    output = tmp_path / "gate.json"
    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=tmp_path / "missing_prompt_bank.json",
        runtime_surface_audit_path=tmp_path / "missing_runtime.json",
        trajectory_surface_audit_path=tmp_path / "missing_trajectory.json",
        dry_run_replacement_audit_path=tmp_path / "missing_dry_run.json",
    )

    write_gate(output, gate)
    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert loaded["gpu_smoke_allowed"] is False
    assert loaded["sources"]["prompt_bank_audit"]["exists"] is False
    assert "candidate70_prompt_bank_audit_missing" in loaded["blockers"]
