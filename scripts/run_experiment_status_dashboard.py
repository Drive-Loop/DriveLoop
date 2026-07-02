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
DEFAULT_FAILURE_TAXONOMY = Path("outputs/driveloop/alignment_failure_taxonomy/motorcycle_refined_candidate_failure_taxonomy.json")
DEFAULT_PROMPT_OBJECT_TRANSFER_AUDIT = Path("outputs/driveloop/prompt_object_transfer_audit/motorcycle_refined_object_transfer_audit.json")
DEFAULT_TRAJECTORY_RUNTIME_SURFACE_AUDIT = Path("outputs/driveloop/trajectory_runtime_surface_audit/motorcycle_refined_trajectory_runtime_surface_audit.json")
DEFAULT_RUNTIME_SURFACE_CODE_AUDIT = Path("outputs/driveloop/runtime_surface_code_audit/motorcycle_refined_runtime_surface_code_audit.json")
DEFAULT_MOTION_METADATA_RUNTIME_AUDIT = Path("outputs/driveloop/motorcycle_motion_metadata_audit_only/motorcycle_motion_metadata_audit_only/dd2_runtime_input_audit_00.json")
DEFAULT_ACTOR_IDENTITY_SURFACE_AUDIT = Path("outputs/driveloop/actor_identity_surface_audit/mini_actor_identity_surface_audit.json")
DEFAULT_CANDIDATE70_CONVERTER_IDENTITY_SUMMARY = Path("outputs/driveloop/candidate70_converter_identity_probe/cam_front_8/v0.0.1/labels/summary.json")
DEFAULT_CANDIDATE70_CONVERTER_ACTOR_TRACK_AUDIT = Path("outputs/driveloop/actor_track_surface_audit/candidate70_converter_identity_probe_actor_track_surface_audit.json")
DEFAULT_CANDIDATE70_HDMAP_RASTER_PROBE = Path("outputs/driveloop/candidate70_hdmap_raster_probe/candidate70_hdmap_raster_probe_summary.json")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def source_entry(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": path.exists()}




def candidate70_hdmap_probe_status(probe: dict[str, Any]) -> dict[str, Any]:
    records = probe.get("records", [])
    if not isinstance(records, list):
        records = []
    frame_count = probe.get("frame_count")
    all_generated_nonzero = bool(records) and all(
        ((record.get("converter_signature") or {}).get("nonzero") or 0) > 0
        for record in records
        if isinstance(record, dict)
    )
    match_true = 0
    match_false = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        for match in record.get("processed_matches", []):
            if not isinstance(match, dict):
                continue
            if match.get("matches_converter") is True:
                match_true += 1
            elif match.get("matches_converter") is False:
                match_false += 1
    processed_matches_converter = bool(records) and match_false == 0 and match_true >= len(records)
    baseline_reproducible = frame_count == len(records) and all_generated_nonzero and processed_matches_converter
    return {
        "frame_count": frame_count,
        "all_generated_nonzero": all_generated_nonzero,
        "processed_match_true": match_true,
        "processed_match_false": match_false,
        "processed_hdmap_matches_converter": processed_matches_converter,
        "baseline_hdmap_raster_reproducible": baseline_reproducible,
    }


def motion_metadata_status(runtime_audit: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    motion_metadata = runtime_audit.get("motion_metadata", {})
    if not isinstance(motion_metadata, dict):
        motion_metadata = {}
    if motion_metadata.get("available") is True:
        return "metadata_observed_not_runtime_control", motion_metadata
    return "not_observed", motion_metadata


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
    failure_taxonomy_path: Path = DEFAULT_FAILURE_TAXONOMY,
    prompt_object_transfer_audit_path: Path = DEFAULT_PROMPT_OBJECT_TRANSFER_AUDIT,
    trajectory_runtime_surface_audit_path: Path = DEFAULT_TRAJECTORY_RUNTIME_SURFACE_AUDIT,
    runtime_surface_code_audit_path: Path = DEFAULT_RUNTIME_SURFACE_CODE_AUDIT,
    motion_metadata_runtime_audit_path: Path = DEFAULT_MOTION_METADATA_RUNTIME_AUDIT,
    actor_identity_surface_audit_path: Path = DEFAULT_ACTOR_IDENTITY_SURFACE_AUDIT,
    candidate70_converter_identity_summary_path: Path = DEFAULT_CANDIDATE70_CONVERTER_IDENTITY_SUMMARY,
    candidate70_converter_actor_track_audit_path: Path = DEFAULT_CANDIDATE70_CONVERTER_ACTOR_TRACK_AUDIT,
    candidate70_hdmap_raster_probe_path: Path = DEFAULT_CANDIDATE70_HDMAP_RASTER_PROBE,
) -> dict[str, Any]:
    readiness = load_json(readiness_path)
    manifest = load_json(manifest_path)
    bundle_validation = load_json(bundle_validation_path)
    alignment_eval = load_json(alignment_eval_path)
    runtime_compare = load_json(runtime_compare_path)
    motion_gap = load_json(motion_gap_path)
    velocity_audit = load_json(velocity_audit_path)
    candidate_audit = load_json(candidate_audit_path)
    failure_taxonomy = load_json(failure_taxonomy_path)
    prompt_object_transfer_audit = load_json(prompt_object_transfer_audit_path)
    trajectory_runtime_surface_audit = load_json(trajectory_runtime_surface_audit_path)
    runtime_surface_code_audit = load_json(runtime_surface_code_audit_path)
    motion_metadata_runtime_audit = load_json(motion_metadata_runtime_audit_path)
    motion_metadata_runtime_status, motion_metadata = motion_metadata_status(motion_metadata_runtime_audit)
    actor_identity_surface_audit = load_json(actor_identity_surface_audit_path)
    actor_identity_claim = actor_identity_surface_audit.get("claim", {})
    candidate70_identity_summary = load_json(candidate70_converter_identity_summary_path)
    candidate70_actor_track_audit = load_json(candidate70_converter_actor_track_audit_path)
    candidate70_hdmap_raster_probe = load_json(candidate70_hdmap_raster_probe_path)
    candidate70_hdmap_status = candidate70_hdmap_probe_status(candidate70_hdmap_raster_probe)
    candidate70_target_token = candidate70_identity_summary.get("target_raw_instance_token")
    candidate70_frame_count = candidate70_identity_summary.get("frame_count")
    candidate70_tracks = candidate70_actor_track_audit.get("track_surface", {}).get("tracks_preview", [])
    candidate70_target_track = next((t for t in candidate70_tracks if t.get("instance_token") == candidate70_target_token), {})
    candidate70_target_track_covers_all_frames = (
        bool(candidate70_target_token)
        and candidate70_target_track.get("observation_count") == candidate70_frame_count
    )

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
            "object_transfer_status": prompt_object_transfer_audit.get("status", "unknown"),
            "trajectory_runtime_surface_status": trajectory_runtime_surface_audit.get("status", "unknown"),
            "runtime_surface_code_audit_status": runtime_surface_code_audit.get("status", "unknown"),
            "motion_metadata_runtime_status": motion_metadata_runtime_status,
            "motion_metadata_claim": motion_metadata.get("claim", "unknown"),
            "actor_identity_surface_status": actor_identity_surface_audit.get("status", "unknown"),
            "actor_identity_available_in_processed_labels": actor_identity_claim.get("actor_identity_available_in_processed_labels"),
            "actor_identity_available_upstream": actor_identity_claim.get("actor_identity_available_upstream"),
            "actor_identity_surface_blockers": actor_identity_surface_audit.get("blockers", []),
            "candidate70_converter_identity_subset_created": candidate70_identity_summary.get("claim", {}).get("candidate70_converter_derived_identity_subset_created") is True,
            "candidate70_converter_identity_all_frames_have_target": candidate70_identity_summary.get("all_frames_have_target"),
            "candidate70_converter_identity_track_observed": candidate70_actor_track_audit.get("status") == "per_frame_actor_tracks_observed",
            "candidate70_target_motorcycle_track_covers_all_8_frames": candidate70_target_track_covers_all_frames,
            "candidate70_full_processed_labels_rebuilt_with_identity": False,
            "candidate70_baseline_hdmap_raster_reproducible": candidate70_hdmap_status["baseline_hdmap_raster_reproducible"],
            "candidate70_processed_hdmap_matches_converter": candidate70_hdmap_status["processed_hdmap_matches_converter"],
            "candidate70_verified_replacement_hdmap_raster_available": False,
            "failure_taxonomy_labels": failure_taxonomy.get("taxonomy_labels", []),
        },
        "claim_boundary": {
            "readiness_allows_gpu_candidate_only": gpu_smoke_allowed and not semantic_claim_allowed_by_readiness,
            "video_generation_is_not_semantic_success": True,
            "runtime_tensor_audit_is_not_video_semantic_success": True,
            "semantic_success_requires_measured_passed_alignment_eval": True,
            "source_candidate_support_is_not_generation_success": True,
            "failure_taxonomy_is_diagnostic_not_success_claim": True,
            "object_transfer_audit_is_not_video_semantic_success": True,
            "trajectory_surface_audit_is_not_video_semantic_success": True,
            "runtime_surface_code_audit_is_not_video_semantic_success": True,
            "motion_metadata_audit_is_not_runtime_motion_control": True,
            "motion_metadata_audit_is_not_video_semantic_success": True,
            "actor_identity_surface_audit_is_not_runtime_motion_control": True,
            "actor_identity_surface_audit_is_not_video_semantic_success": True,
            "candidate70_hdmap_raster_source_probe_is_not_lane_geometry_override": True,
            "candidate70_hdmap_raster_source_probe_is_not_video_semantic_success": True,
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
            "failure_taxonomy_labels": failure_taxonomy.get("taxonomy_labels", []),
            "failure_taxonomy_intervention_hints": failure_taxonomy.get("intervention_hints", []),
            "object_transfer_status": prompt_object_transfer_audit.get("status", "unknown"),
            "object_transfer_blockers": prompt_object_transfer_audit.get("blockers", []),
            "runtime_tensor_class_label_observable": prompt_object_transfer_audit.get("checks", {})
            .get("runtime_tensor_class_labels", {})
            .get("class_label_observable"),
            "trajectory_runtime_surface_status": trajectory_runtime_surface_audit.get("status", "unknown"),
            "trajectory_runtime_surface_blockers": trajectory_runtime_surface_audit.get("blockers", []),
            "trajectory_tensor_available": trajectory_runtime_surface_audit.get("surfaces", {})
            .get("trajectory_tensor", {})
            .get("available"),
            "per_frame_actor_boxes3d_verified": trajectory_runtime_surface_audit.get("surfaces", {})
            .get("per_frame_actor_boxes3d", {})
            .get("verified"),
            "hdmap_lane_geometry_override_verified": trajectory_runtime_surface_audit.get("surfaces", {})
            .get("hdmap_lane_geometry", {})
            .get("override_verified"),
            "runtime_surface_code_audit_status": runtime_surface_code_audit.get("status", "unknown"),
            "dataset_velocity_status": runtime_surface_code_audit.get("surfaces", {})
            .get("dataset_velocity", {})
            .get("status"),
            "dataset_lane_hdmap_status": runtime_surface_code_audit.get("surfaces", {})
            .get("dataset_lane_hdmap", {})
            .get("status"),
            "direct_motion_runtime_surface_status": runtime_surface_code_audit.get("surfaces", {})
            .get("direct_motion_runtime_surface", {})
            .get("status"),
            "motion_metadata_runtime_status": motion_metadata_runtime_status,
            "motion_metadata_available": motion_metadata.get("available") is True,
            "velocities_available_in_batch_any": motion_metadata.get("velocities_available_in_batch_any"),
            "velocities_available_in_batch_all": motion_metadata.get("velocities_available_in_batch_all"),
            "actor_identity_available_in_batch_any": motion_metadata.get("actor_identity_available_in_batch_any"),
            "boxes3d_available_in_batch_any": motion_metadata.get("boxes3d_available_in_batch_any"),
            "per_frame_actor_boxes3d_observed_any": motion_metadata.get("per_frame_actor_boxes3d_observed_any"),
            "motion_metadata_claim": motion_metadata.get("claim", "unknown"),
            "actor_identity_surface_status": actor_identity_surface_audit.get("status", "unknown"),
            "actor_identity_available_in_processed_labels": actor_identity_claim.get("actor_identity_available_in_processed_labels"),
            "actor_identity_available_upstream": actor_identity_claim.get("actor_identity_available_upstream"),
            "actor_identity_surface_blockers": actor_identity_surface_audit.get("blockers", []),
            "candidate70_converter_identity_subset_created": candidate70_identity_summary.get("claim", {}).get("candidate70_converter_derived_identity_subset_created") is True,
            "candidate70_converter_identity_all_frames_have_target": candidate70_identity_summary.get("all_frames_have_target"),
            "candidate70_converter_actor_track_status": candidate70_actor_track_audit.get("status", "unknown"),
            "candidate70_target_motorcycle_track_observation_count": candidate70_target_track.get("observation_count"),
            "candidate70_target_motorcycle_track_covers_all_8_frames": candidate70_target_track_covers_all_frames,
            "candidate70_identity_subset_is_not_runtime_motion_control": True,
            "candidate70_hdmap_raster_probe_frame_count": candidate70_hdmap_status["frame_count"],
            "candidate70_hdmap_raster_probe_all_generated_nonzero": candidate70_hdmap_status["all_generated_nonzero"],
            "candidate70_hdmap_raster_probe_processed_match_true": candidate70_hdmap_status["processed_match_true"],
            "candidate70_hdmap_raster_probe_processed_match_false": candidate70_hdmap_status["processed_match_false"],
            "candidate70_baseline_hdmap_raster_reproducible": candidate70_hdmap_status["baseline_hdmap_raster_reproducible"],
            "candidate70_processed_hdmap_matches_converter": candidate70_hdmap_status["processed_hdmap_matches_converter"],
            "candidate70_verified_replacement_hdmap_raster_available": False,
            "candidate70_hdmap_raster_source_probe_is_not_lane_geometry_override": True,
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
            "alignment_failure_taxonomy": source_entry(failure_taxonomy_path),
            "prompt_object_transfer_audit": source_entry(prompt_object_transfer_audit_path),
            "trajectory_runtime_surface_audit": source_entry(trajectory_runtime_surface_audit_path),
            "runtime_surface_code_audit": source_entry(runtime_surface_code_audit_path),
            "motion_metadata_runtime_audit": source_entry(motion_metadata_runtime_audit_path),
            "actor_identity_surface_audit": source_entry(actor_identity_surface_audit_path),
            "candidate70_converter_identity_summary": source_entry(candidate70_converter_identity_summary_path),
            "candidate70_converter_actor_track_audit": source_entry(candidate70_converter_actor_track_audit_path),
            "candidate70_hdmap_raster_probe": source_entry(candidate70_hdmap_raster_probe_path),
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
    parser.add_argument("--failure-taxonomy", type=Path, default=DEFAULT_FAILURE_TAXONOMY)
    parser.add_argument("--prompt-object-transfer-audit", type=Path, default=DEFAULT_PROMPT_OBJECT_TRANSFER_AUDIT)
    parser.add_argument("--trajectory-runtime-surface-audit", type=Path, default=DEFAULT_TRAJECTORY_RUNTIME_SURFACE_AUDIT)
    parser.add_argument("--runtime-surface-code-audit", type=Path, default=DEFAULT_RUNTIME_SURFACE_CODE_AUDIT)
    parser.add_argument("--motion-metadata-runtime-audit", type=Path, default=DEFAULT_MOTION_METADATA_RUNTIME_AUDIT)
    parser.add_argument("--actor-identity-surface-audit", type=Path, default=DEFAULT_ACTOR_IDENTITY_SURFACE_AUDIT)
    parser.add_argument("--candidate70-converter-identity-summary", type=Path, default=DEFAULT_CANDIDATE70_CONVERTER_IDENTITY_SUMMARY)
    parser.add_argument("--candidate70-converter-actor-track-audit", type=Path, default=DEFAULT_CANDIDATE70_CONVERTER_ACTOR_TRACK_AUDIT)
    parser.add_argument("--candidate70-hdmap-raster-probe", type=Path, default=DEFAULT_CANDIDATE70_HDMAP_RASTER_PROBE)
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
        failure_taxonomy_path=args.failure_taxonomy,
        prompt_object_transfer_audit_path=args.prompt_object_transfer_audit,
        trajectory_runtime_surface_audit_path=args.trajectory_runtime_surface_audit,
        runtime_surface_code_audit_path=args.runtime_surface_code_audit,
        motion_metadata_runtime_audit_path=args.motion_metadata_runtime_audit,
        actor_identity_surface_audit_path=args.actor_identity_surface_audit,
        candidate70_converter_identity_summary_path=args.candidate70_converter_identity_summary,
        candidate70_converter_actor_track_audit_path=args.candidate70_converter_actor_track_audit,
        candidate70_hdmap_raster_probe_path=args.candidate70_hdmap_raster_probe,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    print(args.output)
    print(json.dumps(dashboard, indent=2))


if __name__ == "__main__":
    main()
