from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import Diagnosis, DriveLoopRequest, Evaluation


DEFAULT_ALIGNMENT_EVAL = Path(
    "outputs/driveloop/prompt_video_alignment_eval/"
    "candidate70_night_cut_in_gpu_smoke/"
    "prompt_video_alignment_evaluation.json"
)
DEFAULT_FAILURE_TAXONOMY = Path(
    "outputs/driveloop/alignment_failure_taxonomy/"
    "candidate70_night_cut_in_failure_taxonomy.json"
)
DEFAULT_PERCEPTION_EVAL = Path(
    "outputs/driveloop/perception_video_eval/"
    "candidate70_night_cut_in_yolov8n_cpu_8f_motorcycle/"
    "perception_video_evaluation.json"
)
DEFAULT_GPU_READINESS_GATE = Path(
    "outputs/driveloop/gpu_smoke_readiness/candidate70_gpu_readiness_gate.json"
)
DEFAULT_OUTPUT = Path(
    "outputs/driveloop/candidate70_retry_refinement_proposal/"
    "candidate70_retry_refinement_proposal.json"
)
SCENARIO_ID = "candidate70_night_cut_in_gpu_smoke"
DEFAULT_PROMPT = (
    "night urban street with a motorcycle making a visible cut-in from the left "
    "toward the ego vehicle, panoramic multi-view video."
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _checks_from_report(data: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("prompt_video_alignment", "video_alignment_report", "perception_alignment"):
        value = data.get(key)
        if isinstance(value, dict) and isinstance(value.get("checks"), list):
            return [item for item in value["checks"] if isinstance(item, dict)]
    checks = data.get("checks", [])
    return [item for item in checks if isinstance(item, dict)] if isinstance(checks, list) else []


def failed_alignment_checks(alignment_eval: dict[str, Any]) -> list[str]:
    reasons = (
        alignment_eval.get("evaluation", {})
        .get("diagnosis", {})
        .get("reasons", [])
    )
    failed = []
    if isinstance(reasons, list):
        for reason in reasons:
            if isinstance(reason, str) and reason.startswith("alignment_check_failed:"):
                failed.append(reason.split(":", 1)[1])

    for check in _checks_from_report(alignment_eval):
        if bool(check.get("required", True)) and not bool(check.get("passed", False)):
            name = check.get("name")
            if isinstance(name, str):
                failed.append(name)

    return list(dict.fromkeys(failed))


def prompt_from_sources(alignment_eval: dict[str, Any], perception_eval: dict[str, Any]) -> str:
    for data in (alignment_eval, perception_eval):
        prompt = data.get("generation", {}).get("prompt")
        if isinstance(prompt, str) and prompt.strip():
            return prompt.strip()
    return DEFAULT_PROMPT


def perception_reasons(perception_eval: dict[str, Any]) -> list[str]:
    reasons = perception_eval.get("evaluation", {}).get("diagnosis", {}).get("reasons", [])
    return [str(reason) for reason in reasons] if isinstance(reasons, list) else []


def perception_actions(perception_eval: dict[str, Any]) -> list[str]:
    actions = perception_eval.get("evaluation", {}).get("diagnosis", {}).get("suggested_actions", [])
    return [str(action) for action in actions] if isinstance(actions, list) else []


def build_retry_refinement_proposal(
    alignment_eval: dict[str, Any],
    failure_taxonomy: dict[str, Any],
    perception_eval: dict[str, Any],
    gpu_readiness_gate: dict[str, Any],
) -> dict[str, Any]:
    failed_checks = failed_alignment_checks(alignment_eval)
    reasons = [f"alignment_check_failed:{check}" for check in failed_checks]
    reasons.extend(perception_reasons(perception_eval))
    reasons = list(dict.fromkeys(reasons))

    actions = [
        "inspect failed alignment checks before making semantic claims",
        *perception_actions(perception_eval),
    ]

    prompt = prompt_from_sources(alignment_eval, perception_eval)
    evaluation = Evaluation(
        score=0.0,
        diagnosis=Diagnosis(
            passed=False,
            reasons=reasons,
            suggested_actions=list(dict.fromkeys(actions)),
        ),
    )
    refinement = RuleBasedRefiner().refine(DriveLoopRequest(prompt=prompt), evaluation)

    retry_gate = gpu_readiness_gate.get("gpu_retry_gate", {})
    if not isinstance(retry_gate, dict):
        retry_gate = {}
    retry_blockers = retry_gate.get("blockers", [])
    if not isinstance(retry_blockers, list):
        retry_blockers = []

    perception_claim = perception_eval.get("interpretation", {}).get("perception_claim")
    video_claim = alignment_eval.get("interpretation", {}).get("video_semantic_claim")
    taxonomy_labels = failure_taxonomy.get("taxonomy_labels", [])
    if not isinstance(taxonomy_labels, list):
        taxonomy_labels = []

    proposal_ready = (
        video_claim == "measured_failed"
        and perception_claim == "measured_failed"
        and bool(failed_checks)
        and "explicit_gpu_retry_approval_missing" in retry_blockers
    )
    status = (
        "retry_refinement_proposal_ready_blocked_on_explicit_approval"
        if proposal_ready
        else "retry_refinement_proposal_incomplete"
    )

    return {
        "schema_version": "driveloop_candidate70_retry_refinement_proposal.v0",
        "scenario_id": SCENARIO_ID,
        "status": status,
        "does_not_run_gpu": True,
        "does_not_generate_video": True,
        "semantic_success_claim_allowed": False,
        "source_prompt": prompt,
        "refined_prompt": refinement.prompt,
        "refinement_condition": refinement.condition,
        "refinement_notes": refinement.notes,
        "evidence_summary": {
            "video_semantic_claim": video_claim,
            "perception_claim": perception_claim,
            "failed_alignment_checks": failed_checks,
            "perception_failed_reasons": perception_reasons(perception_eval),
            "taxonomy_labels": taxonomy_labels,
            "gpu_retry_gate_status": retry_gate.get("status"),
            "gpu_retry_gate_allowed": retry_gate.get("allowed"),
            "gpu_retry_gate_blockers": retry_blockers,
        },
        "retry_policy": {
            "proposal_is_not_gpu_approval": True,
            "explicit_gpu_retry_approval_required": True,
            "post_gpu_review_required_after_any_retry": True,
            "approval_template_path": (
                "outputs/driveloop/gpu_retry_approval/"
                "candidate70_gpu_retry_approval.template.json"
            ),
        },
        "claim_boundary": {
            "retry_refinement_proposal_is_not_semantic_success": True,
            "taxonomy_is_diagnostic_not_success_claim": True,
            "perception_metrics_are_not_full_semantic_success": True,
            "gpu_retry_requires_explicit_user_approval": True,
        },
    }


def write_proposal(path: Path, proposal: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build candidate70 retry refinement proposal from measured-failed evidence.")
    parser.add_argument("--alignment-eval", type=Path, default=DEFAULT_ALIGNMENT_EVAL)
    parser.add_argument("--failure-taxonomy", type=Path, default=DEFAULT_FAILURE_TAXONOMY)
    parser.add_argument("--perception-eval", type=Path, default=DEFAULT_PERCEPTION_EVAL)
    parser.add_argument("--gpu-readiness-gate", type=Path, default=DEFAULT_GPU_READINESS_GATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    proposal = build_retry_refinement_proposal(
        load_json(args.alignment_eval),
        load_json(args.failure_taxonomy),
        load_json(args.perception_eval),
        load_json(args.gpu_readiness_gate),
    )
    write_proposal(args.output, proposal)
    print(args.output)
    print(json.dumps(proposal, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
