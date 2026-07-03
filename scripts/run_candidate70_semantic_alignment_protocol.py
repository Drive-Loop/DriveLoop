from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_ACCEPTED_PROMPT_SELECTION = Path("outputs/driveloop/accepted_prompt/candidate70_accepted_prompt_v0.json")
DEFAULT_READINESS_GATE = Path("outputs/driveloop/gpu_smoke_readiness/candidate70_gpu_readiness_gate.json")
DEFAULT_OUTPUT_DIR = Path("outputs/driveloop/candidate70_semantic_alignment_protocol")
DEFAULT_SCENARIO_ID = "candidate70_night_cut_in_gpu_smoke"
DEFAULT_PROMPT = (
    "night urban street with a motorcycle making a visible cut-in from the left "
    "toward the ego vehicle, panoramic multi-view video."
)


def load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def source_entry(path: Path) -> Dict[str, Any]:
    return {"path": str(path), "exists": path.exists()}


def select_prompt(accepted_prompt_selection: Dict[str, Any]) -> str:
    selected = accepted_prompt_selection.get("selected_prompt", {})
    if isinstance(selected, dict):
        prompt = selected.get("prompt")
        if isinstance(prompt, str) and prompt.strip():
            return prompt
    prompt = accepted_prompt_selection.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        return prompt
    return DEFAULT_PROMPT


def required_semantic_checks() -> List[Dict[str, Any]]:
    return [
        {
            "name": "artifact.video_available_and_decodable",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Confirm the generated candidate video exists, opens, and has enough frames for review.",
        },
        {
            "name": "object_presence.motorcycle_or_scooter_visible",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Confirm the target two-wheeler is visible in sampled frames, not only implied by prompt text or tensors.",
        },
        {
            "name": "object_consistency.target_actor_trackable_across_frames",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Track the same target actor across sampled frames and reject one-frame or identity-swapping artifacts.",
        },
        {
            "name": "maneuver.cut_in_from_left_toward_ego_visible",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Verify a visible cut-in or lane-change motion from the left toward the ego path.",
        },
        {
            "name": "temporal_motion.lateral_displacement_visible",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Verify lateral displacement over time rather than static box or actor placement.",
        },
        {
            "name": "spatial_relation.starts_left_or_adjacent_lane_and_moves_toward_ego_path",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Confirm the target begins left or adjacent relative to ego and moves toward the ego lane/path.",
        },
        {
            "name": "road_context.night_urban_multilane_or_lane_markings_visible",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Confirm night urban road context with lane markings or multilane cues needed for the maneuver claim.",
        },
        {
            "name": "hdmap_alignment.lane_geometry_visually_consistent_with_scene",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Check that visible road/lane geometry is not contradicted by the local-map-vector HDMap replacement evidence.",
        },
        {
            "name": "control_binding.structural_evidence_referenced_without_overclaiming",
            "required": True,
            "passed": False,
            "score": 0.0,
            "evidence": "not_reviewed",
            "measurement_instruction": "Reference source-bound actor motion and HDMap audit evidence as conditioning evidence only, not as semantic proof.",
        },
    ]


def build_report_template(protocol: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "driveloop_candidate70_manual_alignment_report_template.v0",
        "status": "not_measured",
        "source": "candidate70_semantic_alignment_protocol_v0",
        "candidate": protocol["candidate"],
        "scenario_id": protocol["scenario_id"],
        "prompt": protocol["prompt"],
        "checks": protocol["required_semantic_checks"],
        "reviewer": "",
        "reviewed_at": "",
        "review_notes": [],
        "semantic_success_claim_allowed": False,
        "claim_boundary": {
            "template_is_not_measured_review": True,
            "candidate_video_artifact_is_not_semantic_success": True,
            "all_required_checks_must_be_measured_and_passed": True,
            "semantic_success_claim_allowed": False,
        },
    }


def build_candidate70_semantic_alignment_protocol(
    accepted_prompt_selection_path: Path = DEFAULT_ACCEPTED_PROMPT_SELECTION,
    readiness_gate_path: Path = DEFAULT_READINESS_GATE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    scenario_id: str = DEFAULT_SCENARIO_ID,
    pass_threshold: float = 0.8,
) -> Dict[str, Any]:
    accepted_prompt_selection = load_json(accepted_prompt_selection_path)
    readiness_gate = load_json(readiness_gate_path)
    readiness_checks = readiness_gate.get("checks", {}) if isinstance(readiness_gate.get("checks"), dict) else {}

    structural_evidence_ready = all(
        readiness_checks.get(name) is True
        for name in (
            "source_bound_actor_motion_runtime_connected",
            "source_bound_actor_motion_sample_identity_verified",
            "local_map_vector_hdmap_reaches_grounding_surface",
            "local_map_vector_hdmap_lane_geometry_override_verified",
            "runtime_motion_control_connected",
            "true_lane_geometry_replacement_available",
        )
    )

    return {
        "schema_version": "driveloop_candidate70_semantic_alignment_protocol.v0",
        "candidate": "candidate70",
        "scenario_id": scenario_id,
        "status": "protocol_defined",
        "does_not_run_gpu": True,
        "does_not_generate_video": True,
        "gpu_smoke_allowed": False,
        "semantic_success_claim_allowed": False,
        "prompt": select_prompt(accepted_prompt_selection),
        "accepted_prompt_selection": source_entry(accepted_prompt_selection_path),
        "readiness_gate": {
            **source_entry(readiness_gate_path),
            "readiness_status": readiness_gate.get("readiness_status"),
            "gpu_smoke_allowed": readiness_gate.get("gpu_smoke_allowed"),
            "blockers": readiness_gate.get("blockers", []),
            "structural_evidence_ready": structural_evidence_ready,
        },
        "required_semantic_checks": required_semantic_checks(),
        "measurement_acceptance_rule": {
            "report_status_must_be_measured": True,
            "all_required_checks_must_pass": True,
            "pass_threshold": pass_threshold,
            "semantic_success_claim_requires_video_semantic_claim": "measured_passed",
            "allowed_negative_result": "measured_failed",
            "not_allowed_inputs_for_success": [
                "prompt text alone",
                "tensor hash changes alone",
                "candidate video existence alone",
                "manual report template with status not_measured",
            ],
        },
        "review_artifacts": {
            "report_template": str(output_dir / "candidate70_manual_alignment_report_template.json"),
            "manual_review_pack_script": "scripts/run_manual_alignment_review_pack.py",
            "post_gpu_review_gate_script": "scripts/run_post_gpu_review_gate.py",
            "alignment_eval_script": "scripts/run_prompt_video_alignment_eval.py",
        },
        "next_required_steps": [
            "request explicit user approval before running candidate70 GPU smoke",
            "after GPU smoke, create a manual review pack or perception review report",
            "fill the report with explicit measured pass/fail evidence for every required check",
            "run scripts/run_prompt_video_alignment_eval.py with the completed measured report",
            "keep semantic_success_claim_allowed false unless the measured report passes all required checks",
        ],
        "claim_boundary": {
            "protocol_definition_is_not_gpu_approval": True,
            "protocol_definition_is_not_video_semantic_success": True,
            "candidate_video_artifact_is_not_semantic_success": True,
            "tensor_or_hash_change_is_not_semantic_success": True,
            "semantic_success_requires_explicit_measured_passed_review": True,
        },
    }


def write_protocol_outputs(protocol: Dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_path = output_dir / "candidate70_semantic_alignment_protocol.json"
    report_template_path = output_dir / "candidate70_manual_alignment_report_template.json"
    protocol_path.write_text(json.dumps(protocol, indent=2, ensure_ascii=False), encoding="utf-8")
    report_template_path.write_text(json.dumps(build_report_template(protocol), indent=2, ensure_ascii=False), encoding="utf-8")
    return {"protocol": str(protocol_path), "report_template": str(report_template_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Define the candidate70 semantic/alignment review protocol.")
    parser.add_argument("--accepted-prompt-selection", type=Path, default=DEFAULT_ACCEPTED_PROMPT_SELECTION)
    parser.add_argument("--readiness-gate", type=Path, default=DEFAULT_READINESS_GATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scenario-id", default=DEFAULT_SCENARIO_ID)
    parser.add_argument("--pass-threshold", type=float, default=0.8)
    args = parser.parse_args()

    protocol = build_candidate70_semantic_alignment_protocol(
        accepted_prompt_selection_path=args.accepted_prompt_selection,
        readiness_gate_path=args.readiness_gate,
        output_dir=args.output_dir,
        scenario_id=args.scenario_id,
        pass_threshold=args.pass_threshold,
    )
    outputs = write_protocol_outputs(protocol, args.output_dir)
    print(json.dumps({"outputs": outputs, "protocol": protocol}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
