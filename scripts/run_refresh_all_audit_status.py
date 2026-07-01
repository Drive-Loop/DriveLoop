from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.run_candidate_artifact_manifest import build_manifest
from scripts.run_candidate_bundle_validator import validate_bundle
from scripts.run_experiment_status_dashboard import build_dashboard
from scripts.run_gpu_smoke_readiness_gate import build_readiness_report
from scripts.run_gpu_smoke_runbook import render_runbook
from scripts.run_single_gpu_smoke_command_plan import (
    DEFAULT_ALIGNMENT_EVAL_DIR,
    DEFAULT_CONFIG_NAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_GATE_DIR,
    DEFAULT_PROMPT,
    DEFAULT_SCENARIO_ID,
    build_command_plan,
    expected_video_path,
)

DEFAULT_READINESS_OUTPUT = Path("outputs/driveloop/gpu_smoke_readiness/motorcycle_refined_candidate_gate.json")
DEFAULT_COMMAND_PLAN_OUTPUT = Path("outputs/driveloop/gpu_smoke_command_plan/motorcycle_refined_candidate_plan.json")
DEFAULT_RUNBOOK_OUTPUT = Path("outputs/driveloop/gpu_smoke_runbook/motorcycle_refined_candidate_runbook.md")
DEFAULT_MANIFEST_OUTPUT = Path("outputs/driveloop/candidate_artifact_manifest/motorcycle_refined_candidate_manifest.json")
DEFAULT_VALIDATION_OUTPUT = Path("outputs/driveloop/candidate_bundle_validation/motorcycle_refined_candidate_validation.json")
DEFAULT_DASHBOARD_OUTPUT = Path("outputs/driveloop/experiment_status_dashboard/motorcycle_refined_candidate_dashboard.json")
DEFAULT_SUMMARY_OUTPUT = Path("outputs/driveloop/refresh_all_audit_status/motorcycle_refined_candidate_refresh.json")

DEFAULT_RUNTIME_COMPARE = Path("outputs/driveloop/dd2_runtime_hash_compare/motorcycle_earlier_vs_refined.json")
DEFAULT_MOTION_GAP = Path("outputs/driveloop/motion_control_gap_audit/motorcycle_manual_feedback_motion_gap.json")
DEFAULT_VELOCITY_SURFACE = Path("outputs/driveloop/dd2_velocity_surface_audit/mini_velocity_surface.json")
DEFAULT_TRAJECTORY_CONTRACT_DOC = Path("experiments/2026-06-28_trajectory_control_contract_v0.md")
DEFAULT_CONFIG_PATH = Path("dreamer-train/projects/DriveDreamer2/configs/drivedreamer2_img_cond_mini_local.py")
DEFAULT_LABELS_PATH = Path("/data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_val/v0.0.2/labels/data.pkl")
DEFAULT_WEIGHTS_PATH = Path("/data/projects/DriveLoop/pretrained_models/drivedreamer2_img_cond/pytorch_gligen_weights.bin")
DEFAULT_EVIDENCE_INDEX = Path("experiments/2026-06-28_motorcycle_alignment_evidence_index.md")
DEFAULT_CLAIM_TABLE = Path("experiments/2026-06-28_paper_claim_table_v0.md")
DEFAULT_PROMPT_OBJECT_TRANSFER_AUDIT = Path("outputs/driveloop/prompt_object_transfer_audit/motorcycle_refined_object_transfer_audit.json")
DEFAULT_TRAJECTORY_RUNTIME_SURFACE_AUDIT = Path("outputs/driveloop/trajectory_runtime_surface_audit/motorcycle_refined_trajectory_runtime_surface_audit.json")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def artifact_entry(path: Path, role: str) -> dict[str, Any]:
    return {"role": role, "path": str(path), "exists_after_refresh": path.exists()}


def build_refresh_summary(
    *,
    prompt: str,
    scenario_id: str,
    readiness_output: Path,
    command_plan_output: Path,
    runbook_output: Path,
    manifest_output: Path,
    validation_output: Path,
    dashboard_output: Path,
    readiness: dict[str, Any],
    manifest: dict[str, Any],
    validation: dict[str, Any],
    dashboard: dict[str, Any],
    prompt_object_transfer_audit: Path,
    trajectory_runtime_surface_audit: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "driveloop_refresh_all_audit_status.v0",
        "scenario_id": scenario_id,
        "prompt": prompt,
        "does_not_run_gpu": True,
        "does_not_generate_video": True,
        "semantic_success_claim_allowed": False,
        "refreshed_artifacts": {
            "readiness_gate": artifact_entry(readiness_output, "gpu_smoke_readiness_gate"),
            "command_plan": artifact_entry(command_plan_output, "single_gpu_smoke_command_plan"),
            "runbook": artifact_entry(runbook_output, "gpu_smoke_runbook"),
            "candidate_manifest": artifact_entry(manifest_output, "candidate_artifact_manifest"),
            "bundle_validation": artifact_entry(validation_output, "candidate_bundle_validation"),
            "experiment_dashboard": artifact_entry(dashboard_output, "experiment_status_dashboard"),
            "prompt_object_transfer_audit": artifact_entry(prompt_object_transfer_audit, "prompt_object_transfer_audit"),
            "trajectory_runtime_surface_audit": artifact_entry(trajectory_runtime_surface_audit, "trajectory_runtime_surface_audit"),
        },
        "refresh_order": [
            "readiness_gate",
            "command_plan",
            "runbook",
            "candidate_manifest",
            "bundle_validation",
            "experiment_dashboard",
            "prompt_object_transfer_audit",
            "trajectory_runtime_surface_audit",
        ],
        "status_summary": {
            "gpu_smoke_allowed": readiness.get("gpu_smoke_allowed"),
            "candidate_status": manifest.get("candidate_status"),
            "bundle_status": validation.get("bundle_status"),
            "dashboard_status": dashboard.get("dashboard_status"),
            "video_semantic_claim": dashboard.get("summary", {}).get(
                "video_semantic_claim", manifest.get("video_semantic_claim")
            ),
            "candidate_manifest_video_semantic_claim": manifest.get("video_semantic_claim"),
            "dashboard_semantic_success_claim_allowed": dashboard.get("summary", {}).get(
                "semantic_success_claim_allowed"
            ),
            "object_transfer_status": dashboard.get("summary", {}).get("object_transfer_status"),
            "trajectory_runtime_surface_status": dashboard.get("summary", {}).get(
                "trajectory_runtime_surface_status"
            ),
        },
        "claim_boundary": {
            "refresh_all_is_audit_only": True,
            "video_generation_is_not_semantic_success": True,
            "runtime_tensor_audit_is_not_video_semantic_success": True,
            "semantic_success_requires_explicit_measured_passed_review": True,
        },
    }


def refresh_all(
    *,
    prompt: str = DEFAULT_PROMPT,
    scenario_id: str = DEFAULT_SCENARIO_ID,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    readiness_output: Path = DEFAULT_READINESS_OUTPUT,
    command_plan_output: Path = DEFAULT_COMMAND_PLAN_OUTPUT,
    runbook_output: Path = DEFAULT_RUNBOOK_OUTPUT,
    manifest_output: Path = DEFAULT_MANIFEST_OUTPUT,
    validation_output: Path = DEFAULT_VALIDATION_OUTPUT,
    dashboard_output: Path = DEFAULT_DASHBOARD_OUTPUT,
    summary_output: Path = DEFAULT_SUMMARY_OUTPUT,
    post_gate_dir: Path = DEFAULT_POST_GATE_DIR,
    alignment_eval_dir: Path = DEFAULT_ALIGNMENT_EVAL_DIR,
    config_name: str = DEFAULT_CONFIG_NAME,
    runtime_compare: Path = DEFAULT_RUNTIME_COMPARE,
    motion_gap: Path = DEFAULT_MOTION_GAP,
    velocity_surface: Path = DEFAULT_VELOCITY_SURFACE,
    trajectory_contract_doc: Path = DEFAULT_TRAJECTORY_CONTRACT_DOC,
    config_path: Path = DEFAULT_CONFIG_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    weights_path: Path = DEFAULT_WEIGHTS_PATH,
    evidence_index: Path = DEFAULT_EVIDENCE_INDEX,
    claim_table: Path = DEFAULT_CLAIM_TABLE,
    runtime_audit: Path | None = None,
    prompt_object_transfer_audit: Path = DEFAULT_PROMPT_OBJECT_TRANSFER_AUDIT,
    trajectory_runtime_surface_audit: Path = DEFAULT_TRAJECTORY_RUNTIME_SURFACE_AUDIT,
) -> dict[str, Any]:
    readiness = build_readiness_report(
        prompt=prompt,
        scenario_id=scenario_id,
        runtime_compare=runtime_compare,
        motion_gap=motion_gap,
        velocity_surface=velocity_surface,
        trajectory_contract_doc=trajectory_contract_doc,
        config_path=config_path,
        labels_path=labels_path,
        weights_path=weights_path,
    )
    write_json(readiness_output, readiness)

    command_plan = build_command_plan(
        prompt=prompt,
        scenario_id=scenario_id,
        output_dir=output_dir,
        readiness_output=readiness_output,
        post_gate_dir=post_gate_dir,
        alignment_eval_dir=alignment_eval_dir,
        config_name=config_name,
    )
    write_json(command_plan_output, command_plan)

    runbook = render_runbook(command_plan)
    write_text(runbook_output, runbook)

    video_path = expected_video_path(output_dir, scenario_id)
    runtime_audit_path = runtime_audit or (output_dir / "artifacts" / scenario_id / "dd2_runtime_input_audit_00.json")
    manifest = build_manifest(
        prompt=prompt,
        scenario_id=scenario_id,
        video_path=video_path,
        readiness_gate=readiness_output,
        command_plan=command_plan_output,
        runbook=runbook_output,
        post_gpu_gate=post_gate_dir / "post_gpu_review_gate.json",
        manual_report=post_gate_dir / "manual_review_pack" / "manual_alignment_report.json",
        alignment_eval=alignment_eval_dir / f"{scenario_id}_manual_review" / "prompt_video_alignment_evaluation.json",
        runtime_audit=runtime_audit_path,
    )
    write_json(manifest_output, manifest)

    validation = validate_bundle(manifest)
    write_json(validation_output, validation)

    dashboard = build_dashboard(
        readiness_path=readiness_output,
        manifest_path=manifest_output,
        bundle_validation_path=validation_output,
        runtime_compare_path=runtime_compare,
        motion_gap_path=motion_gap,
        velocity_audit_path=velocity_surface,
        evidence_index_path=evidence_index,
        claim_table_path=claim_table,
        prompt_object_transfer_audit_path=prompt_object_transfer_audit,
        trajectory_runtime_surface_audit_path=trajectory_runtime_surface_audit,
    )
    write_json(dashboard_output, dashboard)

    summary = build_refresh_summary(
        prompt=prompt,
        scenario_id=scenario_id,
        readiness_output=readiness_output,
        command_plan_output=command_plan_output,
        runbook_output=runbook_output,
        manifest_output=manifest_output,
        validation_output=validation_output,
        dashboard_output=dashboard_output,
        readiness=readiness,
        manifest=manifest,
        validation=validation,
        dashboard=dashboard,
        prompt_object_transfer_audit=prompt_object_transfer_audit,
        trajectory_runtime_surface_audit=trajectory_runtime_surface_audit,
    )
    write_json(summary_output, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh DriveLoop audit/status artifacts without running GPU generation."
    )
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    args = parser.parse_args()

    summary = refresh_all(summary_output=args.summary_output)
    print(args.summary_output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
