from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Optional


DEFAULT_PROMPT_BANK_AUDIT = Path("outputs/driveloop/prompt_bank/candidate70_prompt_bank_support_audit_v0.json")
DEFAULT_ACCEPTED_PROMPT_SELECTION = Path("outputs/driveloop/accepted_prompt/candidate70_accepted_prompt_v0.json")
DEFAULT_RUNTIME_SURFACE_AUDIT = Path("outputs/driveloop/runtime_surface_code_audit/candidate70_runtime_surface_code_audit.json")
DEFAULT_TRAJECTORY_SURFACE_AUDIT = Path("outputs/driveloop/trajectory_runtime_surface_audit/candidate70_night_cut_in_trajectory_runtime_surface_audit.json")
DEFAULT_DRY_RUN_REPLACEMENT_AUDIT = Path("outputs/driveloop/candidate70_hdmap_dry_run_replacement_surface_audit/candidate70_dry_run_raster_to_grounding_surface.json")
DEFAULT_LOCAL_MAP_VECTOR_HDMAP_AUDIT = Path(
    "outputs/driveloop/candidate70_hdmap_lane_geometry_replacement_surface_audit/"
    "candidate70_lane_geometry_replacement_candidate_to_grounding_surface.json"
)
DEFAULT_SOURCE_BOUND_ACTOR_MOTION_AUDIT = Path(
    "outputs/driveloop/candidate70_8frame_actor_motion_audit_only"
)
DEFAULT_SEMANTIC_ALIGNMENT_PROTOCOL = Path(
    "outputs/driveloop/candidate70_semantic_alignment_protocol/candidate70_semantic_alignment_protocol.json"
)
DEFAULT_OUTPUT = Path("outputs/driveloop/gpu_smoke_readiness/candidate70_gpu_readiness_gate.json")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def source_entry(path: Optional[Path]) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False}
    return {"path": str(path), "exists": path.exists()}


def first_key(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = first_key(child, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = first_key(child, key)
            if found is not None:
                return found
    return None


def find_artifact_file(root: Path, filename: str) -> Path:
    direct = root / "artifacts" / filename
    if direct.exists():
        return direct

    artifacts_dir = root / "artifacts"
    if artifacts_dir.exists():
        matches = sorted(artifacts_dir.glob(f"**/{filename}"))
        if matches:
            return matches[0]

    return direct


def load_source_bound_actor_motion_evidence(root: Optional[Path]) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "path": str(root) if root is not None else None,
        "exists": False,
        "connected": False,
        "override_changed_counts": {},
        "applied_per_frame_append_count": 0,
        "sample_identity_applied_count": 0,
    }
    if root is None:
        return evidence

    result_path = root / "result.json"
    case_path = root / "case_summary.json"
    override_path = find_artifact_file(root, "dd2_override_audit_00.jsonl")
    runtime_audit_path = find_artifact_file(root, "dd2_runtime_input_audit_00.json")
    paper_report_path = find_artifact_file(root, "paper_alignment_report_00.json")
    evidence.update(
        {
            "exists": root.exists(),
            "result_exists": result_path.exists(),
            "case_summary_exists": case_path.exists(),
            "override_audit_exists": override_path.exists(),
            "runtime_input_audit_exists": runtime_audit_path.exists(),
            "paper_alignment_report_exists": paper_report_path.exists(),
            "override_audit_path": str(override_path),
            "runtime_input_audit_path": str(runtime_audit_path),
            "paper_alignment_report_path": str(paper_report_path),
        }
    )

    case = load_json(case_path)
    result = load_json(result_path)
    attempts = result.get("attempt_history") if isinstance(result.get("attempt_history"), list) else []
    attempt = attempts[0] if attempts else {}

    source_binding = first_key(attempt, "dd2_source_sample_binding") or {}
    frame_mapping = first_key(attempt, "actor_motion_frame_mapping") or {}
    trace_metadata = first_key(attempt, "trace_metadata") or {}
    case_claim_boundary = case.get("claim_boundary", {}) if isinstance(case.get("claim_boundary"), dict) else {}

    rows = []
    if override_path.exists():
        for line in override_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    evidence["override_audit_json_error"] = True

    changed_counts = Counter()
    skip_reasons = Counter()
    applied_camera_counts = Counter()
    applied_frame_counts = Counter()
    applied_per_frame_append_count = 0
    sample_identity_applied_count = 0
    per_frame_append_row_count = 0

    for row in rows:
        for target, changed in row.get("changed", {}).items():
            if changed:
                changed_counts[target] += 1

        for item in row.get("applied", []):
            if item.get("target") == "boxes3d" and item.get("mode") == "per_frame_append":
                per_frame_append_row_count += 1
                accepted_entries = item.get("accepted_entries", [])
                if isinstance(accepted_entries, list):
                    applied_per_frame_append_count += len(accepted_entries)
                    for entry in accepted_entries:
                        if not isinstance(entry, dict):
                            continue
                        sample_identity = entry.get("sample_identity")
                        if (
                            isinstance(sample_identity, dict)
                            and entry.get("relative_frame_idx") is not None
                            and entry.get("source_record_index") is not None
                        ):
                            sample_identity_applied_count += 1
                            cam_type = sample_identity.get("cam_type")
                            frame_idx = sample_identity.get("frame_idx")
                            if cam_type is not None:
                                applied_camera_counts[str(cam_type)] += 1
                            if frame_idx is not None:
                                applied_frame_counts[str(frame_idx)] += 1
                else:
                    applied_per_frame_append_count += int(item.get("accepted_count") or 0)

        for item in row.get("skipped", []):
            target = item.get("target", "unknown")
            mode = item.get("mode", "unknown")
            reason = item.get("reason", "unknown")
            skip_reasons[f"{target}:{mode}:{reason}"] += 1

    expected_coverage_rows = 48
    no_matching_frame_idx_count = skip_reasons.get("boxes3d:per_frame_append:no_matching_frame_idx", 0)
    full_coverage_verified = (
        len(rows) == expected_coverage_rows
        and changed_counts.get("boxes3d", 0) == expected_coverage_rows
        and changed_counts.get("image_box", 0) == expected_coverage_rows
        and per_frame_append_row_count == expected_coverage_rows
        and applied_per_frame_append_count == expected_coverage_rows
        and sample_identity_applied_count == expected_coverage_rows
        and no_matching_frame_idx_count == 0
        and runtime_audit_path.exists()
        and paper_report_path.exists()
    )

    legacy_connected = (
        case.get("status") == "accepted"
        and source_binding.get("ready") is True
        and source_binding.get("selector", {}).get("source_candidate_id") == "candidate70"
        and frame_mapping.get("available") is True
        and int(frame_mapping.get("mapped_entry_count") or 0) > 0
        and frame_mapping.get("unmapped_relative_frame_idx") == []
        and trace_metadata.get("tensor_control_ready") is True
        and trace_metadata.get("actor_motion_surface_ready") is True
        and changed_counts.get("boxes3d", 0) > 0
        and changed_counts.get("image_box", 0) > 0
        and applied_per_frame_append_count > 0
        and sample_identity_applied_count > 0
    )
    connected = legacy_connected or full_coverage_verified

    evidence.update(
        {
            "case_status": case.get("status"),
            "case_claim_boundary": case_claim_boundary,
            "source_binding_ready": source_binding.get("ready") is True,
            "source_candidate_id": source_binding.get("selector", {}).get("source_candidate_id"),
            "actor_motion_frame_mapping": {
                "available": frame_mapping.get("available") is True,
                "mode": frame_mapping.get("mode"),
                "source_identity_count": frame_mapping.get("source_identity_count"),
                "input_per_frame_count": frame_mapping.get("input_per_frame_count"),
                "mapped_entry_count": frame_mapping.get("mapped_entry_count"),
                "unmapped_relative_frame_idx": frame_mapping.get("unmapped_relative_frame_idx"),
            },
            "trace_metadata": {
                "tensor_control_ready": trace_metadata.get("tensor_control_ready") is True,
                "actor_motion_surface_ready": trace_metadata.get("actor_motion_surface_ready") is True,
                "limitations": trace_metadata.get("limitations", []),
            },
            "override_entry_count": len(rows),
            "expected_coverage_rows": expected_coverage_rows,
            "override_changed_counts": dict(changed_counts),
            "applied_per_frame_append_row_count": per_frame_append_row_count,
            "applied_per_frame_append_count": applied_per_frame_append_count,
            "sample_identity_applied_count": sample_identity_applied_count,
            "skip_reason_counts": dict(skip_reasons),
            "applied_camera_counts": dict(applied_camera_counts),
            "applied_frame_counts": dict(applied_frame_counts),
            "no_matching_frame_idx_count": no_matching_frame_idx_count,
            "full_coverage_verified": full_coverage_verified,
            "coverage": {
                "expected_rows": expected_coverage_rows,
                "override_entry_count": len(rows),
                "boxes3d_changed_count": changed_counts.get("boxes3d", 0),
                "image_box_changed_count": changed_counts.get("image_box", 0),
                "per_frame_append_row_count": per_frame_append_row_count,
                "per_frame_append_count": applied_per_frame_append_count,
                "sample_identity_applied_count": sample_identity_applied_count,
                "no_matching_frame_idx_count": no_matching_frame_idx_count,
            },
            "connected": connected,
            "claim_boundary": {
                "source_bound_actor_motion_audit_is_not_gpu_approval": True,
                "source_bound_actor_motion_audit_is_not_video_semantic_success": True,
                "source_bound_actor_motion_surface_is_tensor_conditioning_not_semantic_proof": True,
            "source_bound_actor_motion_full_coverage_required_before_gpu_retry": True,
                "semantic_success_claim_allowed_by_this_evidence": False,
            },
        }
    )
    return evidence


def load_local_map_vector_hdmap_evidence(path: Optional[Path]) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "path": str(path) if path is not None else None,
        "exists": False,
        "reaches_grounding_surface": False,
        "true_lane_geometry_replacement_available": False,
    }
    if path is None:
        return evidence

    data = load_json(path)
    claim = data.get("claim", {}) if isinstance(data.get("claim"), dict) else {}
    surfaces = data.get("surfaces", {}) if isinstance(data.get("surfaces"), dict) else {}
    candidate_source = data.get("candidate_source", {}) if isinstance(data.get("candidate_source"), dict) else {}
    operation = candidate_source.get("operation", {}) if isinstance(candidate_source.get("operation"), dict) else {}

    image_hdmap = surfaces.get("image_hdmap_override", {}) if isinstance(surfaces.get("image_hdmap_override"), dict) else {}
    grounding = surfaces.get("grounding_downsampler_input", {}) if isinstance(surfaces.get("grounding_downsampler_input"), dict) else {}
    box = surfaces.get("box_downsampler_input", {}) if isinstance(surfaces.get("box_downsampler_input"), dict) else {}
    input_image = surfaces.get("input_image", {}) if isinstance(surfaces.get("input_image"), dict) else {}

    reaches_grounding = (
        path.exists()
        and data.get("status") == "local_map_vector_lane_geometry_replacement_reaches_grounding_surface"
        and candidate_source.get("available") is True
        and operation.get("operation") == "offset_lane_divider_local_map_vector_before_camera_projection"
        and operation.get("coordinate_frame") == "ego_aligned_local_map_patch"
        and image_hdmap.get("changed") is True
        and grounding.get("changed") is True
        and box.get("changed") is False
        and input_image.get("changed") is False
        and claim.get("candidate70_local_map_vector_lane_geometry_replacement_reaches_grounding_downsampler_input") is True
        and claim.get("candidate70_true_lane_geometry_replacement_available") is True
        and claim.get("hdmap_lane_geometry_override_verified") is True
    )

    evidence.update(
        {
            "exists": path.exists(),
            "schema_version": data.get("schema_version"),
            "status": data.get("status"),
            "reaches_grounding_surface": reaches_grounding,
            "true_lane_geometry_replacement_available": reaches_grounding,
            "hdmap_lane_geometry_override_verified": claim.get("hdmap_lane_geometry_override_verified") is True,
            "candidate_source": {
                "available": candidate_source.get("available") is True,
                "frame_index": candidate_source.get("frame_index"),
                "data_index": candidate_source.get("data_index"),
                "frame_idx": candidate_source.get("frame_idx"),
                "path": candidate_source.get("path"),
                "path_exists": candidate_source.get("path_exists"),
                "expected_sha256": candidate_source.get("expected_sha256"),
                "operation": operation,
                "provenance": candidate_source.get("provenance"),
            },
            "surfaces": {
                "image_hdmap_override_changed": image_hdmap.get("changed") is True,
                "grounding_downsampler_input_changed": grounding.get("changed") is True,
                "box_downsampler_input_changed": box.get("changed") is True,
                "input_image_changed": input_image.get("changed") is True,
            },
            "claim_boundary": {
                "local_map_vector_lane_geometry_replacement_is_not_gpu_approval": True,
                "local_map_vector_lane_geometry_replacement_is_not_lane_change_control": True,
                "runtime_tensor_audit_is_not_video_semantic_success": True,
                "semantic_success_claim_allowed_by_this_evidence": False,
            },
        }
    )
    return evidence


def load_semantic_alignment_protocol_evidence(path: Optional[Path]) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "path": str(path) if path is not None else None,
        "exists": False,
        "protocol_defined": False,
        "required_check_count": 0,
        "required_check_names": [],
    }
    if path is None:
        return evidence

    data = load_json(path)
    checks = data.get("required_semantic_checks", [])
    required_checks = [
        check for check in checks
        if isinstance(check, dict) and check.get("required") is True
    ]
    required_names = [
        str(check.get("name")) for check in required_checks
        if check.get("name")
    ]
    acceptance_rule = data.get("measurement_acceptance_rule", {})
    if not isinstance(acceptance_rule, dict):
        acceptance_rule = {}
    claim_boundary = data.get("claim_boundary", {})
    if not isinstance(claim_boundary, dict):
        claim_boundary = {}

    protocol_defined = (
        path.exists()
        and data.get("status") == "protocol_defined"
        and data.get("does_not_run_gpu") is True
        and data.get("does_not_generate_video") is True
        and data.get("semantic_success_claim_allowed") is False
        and len(required_checks) >= 5
        and acceptance_rule.get("report_status_must_be_measured") is True
        and acceptance_rule.get("all_required_checks_must_pass") is True
        and claim_boundary.get("protocol_definition_is_not_video_semantic_success") is True
    )

    evidence.update(
        {
            "exists": path.exists(),
            "schema_version": data.get("schema_version"),
            "status": data.get("status"),
            "protocol_defined": protocol_defined,
            "required_check_count": len(required_checks),
            "required_check_names": required_names,
            "measurement_acceptance_rule": acceptance_rule,
            "claim_boundary": claim_boundary,
        }
    )
    return evidence


def build_candidate70_readiness_gate(
    *,
    prompt_bank_audit_path: Path = DEFAULT_PROMPT_BANK_AUDIT,
    accepted_prompt_selection_path: Path = DEFAULT_ACCEPTED_PROMPT_SELECTION,
    runtime_surface_audit_path: Path = DEFAULT_RUNTIME_SURFACE_AUDIT,
    trajectory_surface_audit_path: Path = DEFAULT_TRAJECTORY_SURFACE_AUDIT,
    dry_run_replacement_audit_path: Path = DEFAULT_DRY_RUN_REPLACEMENT_AUDIT,
    source_bound_actor_motion_audit_path: Optional[Path] = None,
    local_map_vector_hdmap_audit_path: Optional[Path] = None,
    semantic_alignment_protocol_path: Optional[Path] = DEFAULT_SEMANTIC_ALIGNMENT_PROTOCOL,
) -> dict[str, Any]:
    prompt_bank = load_json(prompt_bank_audit_path)
    accepted_prompt_selection = load_json(accepted_prompt_selection_path)
    runtime_surface = load_json(runtime_surface_audit_path)
    trajectory_surface = load_json(trajectory_surface_audit_path)
    dry_run = load_json(dry_run_replacement_audit_path)
    actor_motion_evidence = load_source_bound_actor_motion_evidence(source_bound_actor_motion_audit_path)
    local_map_vector_hdmap_evidence = load_local_map_vector_hdmap_evidence(local_map_vector_hdmap_audit_path)
    semantic_alignment_protocol_evidence = load_semantic_alignment_protocol_evidence(semantic_alignment_protocol_path)

    supported_count = prompt_bank.get("candidate70_allowed_count")
    accepted_prompt_selected = accepted_prompt_selection.get("accepted_prompt_selected") is True
    runtime_status = runtime_surface.get("status")
    trajectory_status = trajectory_surface.get("status")
    trajectory_surfaces = trajectory_surface.get("surfaces", {})
    trajectory_source_signals = trajectory_surface.get("source_signals", {})
    trajectory_blockers = trajectory_surface.get("blockers", [])
    dry_run_claim = dry_run.get("claim", {})
    actor_motion_connected = actor_motion_evidence.get("connected") is True
    actor_full_coverage_verified = actor_motion_evidence.get("full_coverage_verified") is True
    actor_changed_counts = actor_motion_evidence.get("override_changed_counts", {})

    boxes3d_image_box_structural_override_ready = (
        (
            trajectory_source_signals.get("motion_gap_boxes3d_target_override") == "applied"
            and trajectory_surfaces.get("box_condition", {}).get("available") is True
        )
        or actor_full_coverage_verified
    )

    runtime_motion_control_connected = (
        dry_run_claim.get("runtime_motion_control_connected") is True
        or actor_motion_connected
    )
    true_lane_geometry_replacement_available = (
        dry_run_claim.get("candidate70_true_lane_geometry_replacement_available") is True
        or local_map_vector_hdmap_evidence.get("true_lane_geometry_replacement_available") is True
    )

    checks = {
        "prompt_bank_audit_exists": prompt_bank_audit_path.exists(),
        "candidate70_supported_prompts_available": bool(supported_count and supported_count > 0),
        "accepted_prompt_selection_exists": accepted_prompt_selection_path.exists(),
        "accepted_prompt_selected": accepted_prompt_selected,
        "accepted_prompt_for_generate": accepted_prompt_selection.get("accepted_for_generate") is True,
        "runtime_surface_not_connected": runtime_status == "not_runtime_connected" and not actor_motion_connected,
        "trajectory_surface_not_connected": trajectory_status == "not_runtime_connected" and not actor_motion_connected,
        "boxes3d_target_override_applied": (
            trajectory_source_signals.get("motion_gap_boxes3d_target_override") == "applied"
            or actor_changed_counts.get("boxes3d", 0) > 0
        ),
        "image_box_condition_connected": (
            trajectory_surfaces.get("box_condition", {}).get("available") is True
            or actor_changed_counts.get("image_box", 0) > 0
        ),
        "boxes3d_image_box_structural_override_ready": boxes3d_image_box_structural_override_ready,
        "static_box_condition_is_not_temporal_motion_control": (
            "static_box_condition_available_but_not_temporal_motion_control" in trajectory_blockers
        ),
        "source_bound_actor_motion_audit_exists": actor_motion_evidence.get("exists") is True,
        "source_bound_actor_motion_runtime_connected": actor_motion_connected,
        "source_bound_actor_motion_sample_identity_verified": actor_motion_evidence.get("sample_identity_applied_count", 0) > 0,
        "source_bound_actor_motion_full_coverage_verified": actor_full_coverage_verified,
        "source_bound_actor_motion_boxes3d_changed": actor_changed_counts.get("boxes3d", 0) > 0,
        "source_bound_actor_motion_image_box_changed": actor_changed_counts.get("image_box", 0) > 0,
        "dry_run_raster_reaches_grounding_downsampler_input": dry_run_claim.get("candidate70_dry_run_raster_reaches_grounding_downsampler_input") is True,
        "true_lane_geometry_replacement_available": true_lane_geometry_replacement_available,
        "local_map_vector_hdmap_audit_exists": local_map_vector_hdmap_evidence.get("exists") is True,
        "local_map_vector_hdmap_reaches_grounding_surface": local_map_vector_hdmap_evidence.get("reaches_grounding_surface") is True,
        "local_map_vector_hdmap_lane_geometry_override_verified": local_map_vector_hdmap_evidence.get("hdmap_lane_geometry_override_verified") is True,
        "runtime_motion_control_connected": runtime_motion_control_connected,
        "semantic_success_claim_allowed": dry_run_claim.get("semantic_success_claim_allowed") is True,
        "semantic_alignment_protocol_exists": semantic_alignment_protocol_evidence.get("exists") is True,
        "semantic_alignment_protocol_defined": semantic_alignment_protocol_evidence.get("protocol_defined") is True,
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
    if (
        checks["source_bound_actor_motion_audit_exists"]
        and not checks["source_bound_actor_motion_full_coverage_verified"]
    ):
        blockers.append("source_bound_actor_motion_full_coverage_not_verified")
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
        "evidence": {
            "source_bound_actor_motion": actor_motion_evidence,
            "local_map_vector_hdmap": local_map_vector_hdmap_evidence,
            "semantic_alignment_protocol": semantic_alignment_protocol_evidence,
        },
        "sources": {
            "prompt_bank_audit": source_entry(prompt_bank_audit_path),
            "accepted_prompt_selection": source_entry(accepted_prompt_selection_path),
            "runtime_surface_audit": source_entry(runtime_surface_audit_path),
            "trajectory_surface_audit": source_entry(trajectory_surface_audit_path),
            "dry_run_replacement_audit": source_entry(dry_run_replacement_audit_path),
            "source_bound_actor_motion_audit": source_entry(source_bound_actor_motion_audit_path),
            "local_map_vector_hdmap_audit": source_entry(local_map_vector_hdmap_audit_path),
            "semantic_alignment_protocol": source_entry(semantic_alignment_protocol_path),
        },
        "claim_boundary": {
            "candidate70_readiness_gate_is_not_gpu_approval": True,
            "candidate70_readiness_gate_is_not_video_semantic_success": True,
            "accepted_prompt_required_before_generate": True,
            "dry_run_raster_is_not_true_lane_geometry_replacement": True,
            "runtime_motion_control_required_before_lane_change_control_claim": True,
            "boxes3d_image_box_structural_override_is_not_temporal_motion_control": True,
            "source_bound_actor_motion_audit_is_not_gpu_approval": True,
            "source_bound_actor_motion_audit_is_not_video_semantic_success": True,
            "source_bound_actor_motion_surface_is_tensor_conditioning_not_semantic_proof": True,
            "source_bound_actor_motion_full_coverage_required_before_gpu_retry": True,
            "local_map_vector_hdmap_replacement_is_not_gpu_approval": True,
            "local_map_vector_hdmap_replacement_is_not_video_semantic_success": True,
            "semantic_alignment_protocol_is_not_video_semantic_success": True,
            "semantic_success_requires_explicit_measured_passed_review": True,
        },
        "next_required_steps": [
            "wire the accepted prompt into any GPU smoke command only after explicit user approval",
            "do not reuse the old daytime motorcycle_refined_candidate_gpu_smoke gate as candidate70 approval",
            "use source-bound actor-motion tensor evidence only as structural runtime conditioning evidence",
            "keep boxes3d/image_box structural override separate from video semantic-success claims",
            "run measured semantic/alignment evaluation before any semantic-success claim",
            "use the candidate70 semantic alignment protocol as the required review checklist after GPU smoke",
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
    parser.add_argument("--source-bound-actor-motion-audit", type=Path, default=DEFAULT_SOURCE_BOUND_ACTOR_MOTION_AUDIT)
    parser.add_argument("--local-map-vector-hdmap-audit", type=Path, default=DEFAULT_LOCAL_MAP_VECTOR_HDMAP_AUDIT)
    parser.add_argument("--semantic-alignment-protocol", type=Path, default=DEFAULT_SEMANTIC_ALIGNMENT_PROTOCOL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gate = build_candidate70_readiness_gate(
        prompt_bank_audit_path=args.prompt_bank_audit,
        accepted_prompt_selection_path=args.accepted_prompt_selection,
        runtime_surface_audit_path=args.runtime_surface_audit,
        trajectory_surface_audit_path=args.trajectory_surface_audit,
        dry_run_replacement_audit_path=args.dry_run_replacement_audit,
        source_bound_actor_motion_audit_path=args.source_bound_actor_motion_audit,
        local_map_vector_hdmap_audit_path=args.local_map_vector_hdmap_audit,
        semantic_alignment_protocol_path=args.semantic_alignment_protocol,
    )
    write_gate(args.output, gate)
    print(args.output)
    print(json.dumps(gate, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
