from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_PROMPT_BANK_AUDIT = Path("outputs/driveloop/prompt_bank/candidate70_prompt_bank_support_audit_v0.json")
DEFAULT_ACCEPTED_PROMPT_SELECTION = Path("outputs/driveloop/accepted_prompt/candidate70_accepted_prompt_v0.json")
DEFAULT_RUNTIME_SURFACE_AUDIT = Path("outputs/driveloop/runtime_surface_code_audit/candidate70_runtime_surface_code_audit.json")
DEFAULT_TRAJECTORY_SURFACE_AUDIT = Path("outputs/driveloop/trajectory_runtime_surface_audit/candidate70_night_cut_in_trajectory_runtime_surface_audit.json")
DEFAULT_DRY_RUN_REPLACEMENT_AUDIT = Path("outputs/driveloop/candidate70_hdmap_dry_run_replacement_surface_audit/candidate70_dry_run_raster_to_grounding_surface.json")
DEFAULT_OUTPUT = Path("outputs/driveloop/gpu_smoke_readiness/candidate70_gpu_readiness_gate.json")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def source_entry(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": path.exists()}


def build_candidate70_readiness_gate(
    *,
    prompt_bank_audit_path: Path = DEFAULT_PROMPT_BANK_AUDIT,
    accepted_prompt_selection_path: Path = DEFAULT_ACCEPTED_PROMPT_SELECTION,
    runtime_surface_audit_path: Path = DEFAULT_RUNTIME_SURFACE_AUDIT,
    trajectory_surface_audit_path: Path = DEFAULT_TRAJECTORY_SURFACE_AUDIT,
    dry_run_replacement_audit_path: Path = DEFAULT_DRY_RUN_REPLACEMENT_AUDIT,
) -> dict[str, Any]:
    prompt_bank = load_json(prompt_bank_audit_path)
    accepted_prompt_selection = load_json(accepted_prompt_selection_path)
    runtime_surface = load_json(runtime_surface_audit_path)
    trajectory_surface = load_json(trajectory_surface_audit_path)
    dry_run = load_json(dry_run_replacement_audit_path)

    supported_count = prompt_bank.get("candidate70_allowed_count")
    accepted_prompt_selected = accepted_prompt_selection.get("accepted_prompt_selected") is True
    runtime_status = runtime_surface.get("status")
    trajectory_status = trajectory_surface.get("status")
    dry_run_claim = dry_run.get("claim", {})

    checks = {
        "prompt_bank_audit_exists": prompt_bank_audit_path.exists(),
        "candidate70_supported_prompts_available": bool(supported_count and supported_count > 0),
        "accepted_prompt_selection_exists": accepted_prompt_selection_path.exists(),
        "accepted_prompt_selected": accepted_prompt_selected,
        "accepted_prompt_for_generate": accepted_prompt_selection.get("accepted_for_generate") is True,
        "runtime_surface_not_connected": runtime_status == "not_runtime_connected",
        "trajectory_surface_not_connected": trajectory_status == "not_runtime_connected",
        "dry_run_raster_reaches_grounding_downsampler_input": dry_run_claim.get("candidate70_dry_run_raster_reaches_grounding_downsampler_input") is True,
        "true_lane_geometry_replacement_available": dry_run_claim.get("candidate70_true_lane_geometry_replacement_available") is True,
        "runtime_motion_control_connected": dry_run_claim.get("runtime_motion_control_connected") is True,
        "semantic_success_claim_allowed": dry_run_claim.get("semantic_success_claim_allowed") is True,
    }

    blockers = []
    if not checks["prompt_bank_audit_exists"]:
        blockers.append("candidate70_prompt_bank_audit_missing")
    if not checks["candidate70_supported_prompts_available"]:
        blockers.append("candidate70_supported_prompt_not_available")
    if not checks["accepted_prompt_selected"]:
        blockers.append("accepted_prompt_required_before_generate")
    if checks["runtime_surface_not_connected"]:
        blockers.append("runtime_motion_control_not_connected")
    if checks["trajectory_surface_not_connected"]:
        blockers.append("trajectory_runtime_surface_not_connected")
    if not checks["true_lane_geometry_replacement_available"]:
        blockers.append("true_lane_geometry_replacement_not_available")
    if not checks["runtime_motion_control_connected"]:
        blockers.append("runtime_motion_control_claim_not_allowed")
    if not checks["semantic_success_claim_allowed"]:
        blockers.append("semantic_success_claim_not_allowed")

    return {
        "schema_version": "driveloop_candidate70_gpu_readiness_gate.v0",
        "candidate": "candidate70",
        "scenario_id": "candidate70_night_cut_in_gpu_smoke",
        "readiness_status": "blocked" if blockers else "allowed",
        "gpu_smoke_allowed": not blockers,
        "allowed_claim_after_gpu": "candidate_video_only_if_separately_approved",
        "does_not_run_gpu": True,
        "does_not_generate_video": True,
        "checks": checks,
        "blockers": blockers,
        "sources": {
            "prompt_bank_audit": source_entry(prompt_bank_audit_path),
            "accepted_prompt_selection": source_entry(accepted_prompt_selection_path),
            "runtime_surface_audit": source_entry(runtime_surface_audit_path),
            "trajectory_surface_audit": source_entry(trajectory_surface_audit_path),
            "dry_run_replacement_audit": source_entry(dry_run_replacement_audit_path),
        },
        "claim_boundary": {
            "candidate70_readiness_gate_is_not_gpu_approval": True,
            "candidate70_readiness_gate_is_not_video_semantic_success": True,
            "accepted_prompt_required_before_generate": True,
            "dry_run_raster_is_not_true_lane_geometry_replacement": True,
            "runtime_motion_control_required_before_lane_change_control_claim": True,
            "semantic_success_requires_explicit_measured_passed_review": True,
        },
        "next_required_steps": [
            "wire the accepted prompt into any GPU smoke command only after explicit user approval",
            "do not reuse the old daytime motorcycle_refined_candidate_gpu_smoke gate as candidate70 approval",
            "connect or explicitly mark unavailable candidate70 runtime motion control surfaces",
            "obtain true lane-geometry replacement evidence before any HDMap override claim",
            "request explicit user approval before any short GPU smoke",
        ],
    }


def write_gate(output: Path, gate: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the candidate70-specific non-GPU readiness gate.")
    parser.add_argument("--prompt-bank-audit", type=Path, default=DEFAULT_PROMPT_BANK_AUDIT)
    parser.add_argument("--accepted-prompt-selection", type=Path, default=DEFAULT_ACCEPTED_PROMPT_SELECTION)
    parser.add_argument("--runtime-surface-audit", type=Path, default=DEFAULT_RUNTIME_SURFACE_AUDIT)
    parser.add_argument("--trajectory-surface-audit", type=Path, default=DEFAULT_TRAJECTORY_SURFACE_AUDIT)
    parser.add_argument("--dry-run-replacement-audit", type=Path, default=DEFAULT_DRY_RUN_REPLACEMENT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=args.prompt_bank_audit,
        accepted_prompt_selection_path=args.accepted_prompt_selection,
        runtime_surface_audit_path=args.runtime_surface_audit,
        trajectory_surface_audit_path=args.trajectory_surface_audit,
        dry_run_replacement_audit_path=args.dry_run_replacement_audit,
    )
    write_gate(args.output, gate)
    print(args.output)
    print(json.dumps(gate, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
