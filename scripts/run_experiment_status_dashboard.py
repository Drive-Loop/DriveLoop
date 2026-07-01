from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_READINESS = Path("outputs/driveloop/gpu_smoke_readiness/motorcycle_refined_candidate_gate.json")
DEFAULT_MANIFEST = Path("outputs/driveloop/candidate_artifact_manifest/motorcycle_refined_candidate_manifest.json")
DEFAULT_BUNDLE_VALIDATION = Path("outputs/driveloop/candidate_bundle_validation/motorcycle_refined_candidate_validation.json")
DEFAULT_ALIGNMENT_EVAL = Path("outputs/driveloop/prompt_video_alignment_eval/motorcycle_refined_candidate_gpu_smoke_manual_review/prompt_video_alignment_evaluation.json")
DEFAULT_RUNTIME_COMPARE = Path("outputs/driveloop/dd2_runtime_hash_compare/motorcycle_earlier_vs_refined.json")
DEFAULT_MOTION_GAP = Path("outputs/driveloop/motion_control_gap_audit/motorcycle_manual_feedback_motion_gap.json")
DEFAULT_VELOCITY_AUDIT = Path("outputs/driveloop/dd2_velocity_surface_audit/mini_velocity_surface.json")
DEFAULT_EVIDENCE_INDEX = Path("experiments/2026-06-28_motorcycle_alignment_evidence_index.md")
DEFAULT_CLAIM_TABLE = Path("experiments/2026-06-28_paper_claim_table_v0.md")
DEFAULT_CANDIDATE_AUDIT = Path("outputs/driveloop/prompt_conditional_candidate_audit/motorcycle_source_candidate_rank16_audit.json")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def source_entry(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": path.exists()}


def build_dashboard(
    readiness_path: Path = DEFAULT_READINESS,
    manifest_path: Path = DEFAULT_MANIFEST,
    bundle_validation_path: Path = DEFAULT_BUNDLE_VALIDATION,
    alignment_eval_path: Path = DEFAULT_ALIGNMENT_EVAL,
    runtime_compare_path: Path = DEFAULT_RUNTIME_COMPARE,
    motion_gap_path: Path = DEFAULT_MOTION_GAP,
    velocity_audit_path: Path = DEFAULT_VELOCITY_AUDIT,
    evidence_index_path: Path = DEFAULT_EVIDENCE_INDEX,
    claim_table_path: Path = DEFAULT_CLAIM_TABLE,
    candidate_audit_path: Path = DEFAULT_CANDIDATE_AUDIT,
) -> dict[str, Any]:
    readiness = load_json(readiness_path)
    manifest = load_json(manifest_path)
    bundle_validation = load_json(bundle_validation_path)
    alignment_eval = load_json(alignment_eval_path)
    runtime_compare = load_json(runtime_compare_path)
    motion_gap = load_json(motion_gap_path)
    velocity_audit = load_json(velocity_audit_path)
    candidate_audit = load_json(candidate_audit_path)

    gpu_smoke_allowed = readiness.get("gpu_smoke_allowed") is True
    semantic_claim_allowed_by_readiness = readiness.get("semantic_claim_allowed") is True
    candidate_status = manifest.get("candidate_status", "unknown")
    alignment_interpretation = alignment_eval.get("interpretation", {})
    video_semantic_claim = alignment_interpretation.get(
        "video_semantic_claim", manifest.get("video_semantic_claim", "unknown")
    )
    bundle_status = bundle_validation.get("bundle_status", "unknown")

    runtime_changed = runtime_compare.get("runtime_tensor_hash_changed", {})
    motion_claim = motion_gap.get("claim", {})
    velocity_claim = velocity_audit.get("claim", {})

    dashboard_status = "pre_gpu_ready" if gpu_smoke_allowed else "pre_gpu_blocked"
    if candidate_status == "candidate_video_only":
        dashboard_status = "candidate_generated"
    if bundle_status == "review_ready":
        dashboard_status = "review_ready"
    if bundle_status == "measured_ready":
        dashboard_status = "measured_ready"

    return {
        "schema_version": "driveloop_experiment_status_dashboard.v0",
        "scenario_id": readiness.get("scenario_id") or manifest.get("scenario_id"),
        "prompt": readiness.get("prompt") or manifest.get("prompt"),
        "dashboard_status": dashboard_status,
        "summary": {
            "gpu_smoke_allowed": gpu_smoke_allowed,
            "candidate_status": candidate_status,
            "bundle_status": bundle_status,
            "video_semantic_claim": video_semantic_claim,
            "semantic_success_claim_allowed": False,
            "source_candidate_support_status": candidate_audit.get("status", "unknown"),
            "source_candidate_support_allowed": candidate_audit.get("allowed") is True,
        },
        "claim_boundary": {
            "readiness_allows_gpu_candidate_only": gpu_smoke_allowed and not semantic_claim_allowed_by_readiness,
            "video_generation_is_not_semantic_success": True,
            "runtime_tensor_audit_is_not_video_semantic_success": True,
            "semantic_success_requires_measured_passed_alignment_eval": True,
            "source_candidate_support_is_not_generation_success": True,
        },
        "audit_signals": {
            "runtime_tensor_hash_changed": runtime_changed,
            "lane_change_motion_tensor_control": motion_claim.get("lane_change_motion_tensor_control"),
            "velocity_consumed_by_dd2_runtime": velocity_claim.get("velocity_consumed_by_dd2_runtime"),
            "trajectory_or_temporal_motion_verified": False,
            "prompt_conditional_candidate_allowed": candidate_audit.get("allowed") is True,
            "prompt_conditional_candidate_status": candidate_audit.get("status", "unknown"),
            "prompt_conditional_candidate_missing_support": candidate_audit.get("missing_requested_support", []),
            "prompt_conditional_candidate_unrequested_bias": candidate_audit.get("unrequested_selection_bias", []),
        },
        "sources": {
            "readiness": source_entry(readiness_path),
            "manifest": source_entry(manifest_path),
            "bundle_validation": source_entry(bundle_validation_path),
            "alignment_eval": source_entry(alignment_eval_path),
            "runtime_compare": source_entry(runtime_compare_path),
            "motion_gap": source_entry(motion_gap_path),
            "velocity_audit": source_entry(velocity_audit_path),
            "evidence_index": source_entry(evidence_index_path),
            "claim_table": source_entry(claim_table_path),
            "prompt_conditional_candidate_audit": source_entry(candidate_audit_path),
        },
        "next_recommended_action": next_action(
            gpu_smoke_allowed=gpu_smoke_allowed,
            candidate_status=candidate_status,
            bundle_status=bundle_status,
        ),
    }


def next_action(gpu_smoke_allowed: bool, candidate_status: str, bundle_status: str) -> str:
    if not gpu_smoke_allowed:
        return "refresh readiness evidence before any GPU smoke"
    if candidate_status != "candidate_video_only":
        return "optionally run one gated GPU smoke candidate, then regenerate manifest and validation"
    if bundle_status == "blocked":
        return "run post-GPU review gate and complete explicit review report"
    if bundle_status == "review_ready":
        return "run prompt-video alignment evaluation and preserve measured result"
    if bundle_status == "measured_ready":
        return "inspect alignment evaluation result before any semantic claim"
    return "inspect dashboard sources"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a DriveLoop experiment status dashboard JSON.")
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--bundle-validation", type=Path, default=DEFAULT_BUNDLE_VALIDATION)
    parser.add_argument("--alignment-eval", type=Path, default=DEFAULT_ALIGNMENT_EVAL)
    parser.add_argument("--runtime-compare", type=Path, default=DEFAULT_RUNTIME_COMPARE)
    parser.add_argument("--motion-gap", type=Path, default=DEFAULT_MOTION_GAP)
    parser.add_argument("--velocity-audit", type=Path, default=DEFAULT_VELOCITY_AUDIT)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    parser.add_argument("--claim-table", type=Path, default=DEFAULT_CLAIM_TABLE)
    parser.add_argument("--candidate-audit", type=Path, default=DEFAULT_CANDIDATE_AUDIT)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    dashboard = build_dashboard(
        readiness_path=args.readiness,
        manifest_path=args.manifest,
        bundle_validation_path=args.bundle_validation,
        alignment_eval_path=args.alignment_eval,
        runtime_compare_path=args.runtime_compare,
        motion_gap_path=args.motion_gap,
        velocity_audit_path=args.velocity_audit,
        evidence_index_path=args.evidence_index,
        claim_table_path=args.claim_table,
        candidate_audit_path=args.candidate_audit,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    print(args.output)
    print(json.dumps(dashboard, indent=2))


if __name__ == "__main__":
    main()
