from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_value(value: Any) -> str:
    if value is None:
        return "not_available"
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def alignment_summary(alignment_eval: dict[str, Any]) -> dict[str, Any]:
    evaluation = as_dict(alignment_eval.get("evaluation"))
    metrics = as_dict(evaluation.get("metrics"))
    diagnosis = as_dict(evaluation.get("diagnosis"))
    interpretation = as_dict(alignment_eval.get("interpretation"))

    passed = first_present(diagnosis.get("passed"), alignment_eval.get("passed"))
    reasons = [str(reason) for reason in as_list(diagnosis.get("reasons"))]

    return {
        "video_semantic_claim": first_present(
            interpretation.get("video_semantic_claim"),
            alignment_eval.get("video_semantic_claim"),
            "unknown",
        ),
        "score": coerce_float(first_present(evaluation.get("score"), alignment_eval.get("score"))),
        "passed": passed if isinstance(passed, bool) else None,
        "required_check_count": coerce_float(metrics.get("alignment_required_check_count")),
        "passed_required_check_count": coerce_float(metrics.get("alignment_passed_required_check_count")),
        "video_artifact_available": coerce_float(metrics.get("video_artifact_available")),
        "alignment_measured": coerce_float(metrics.get("alignment_measured")),
        "reasons": reasons,
    }


def perception_summary(perception_eval: dict[str, Any] | None) -> dict[str, Any]:
    if not perception_eval:
        return {"available": False}

    evaluation = as_dict(perception_eval.get("evaluation"))
    metrics = as_dict(evaluation.get("metrics"))
    diagnosis = as_dict(evaluation.get("diagnosis"))
    interpretation = as_dict(perception_eval.get("interpretation"))

    keys = [
        "perception_measured",
        "perception_frame_count",
        "Q_cov",
        "Q_conf",
        "Q_track",
        "Q_id",
        "Q_box",
        "perception_detection_count",
        "perception_track_count",
        "perception_dominant_track_length",
    ]

    return {
        "available": True,
        "video_semantic_claim": first_present(
            interpretation.get("video_semantic_claim"),
            perception_eval.get("video_semantic_claim"),
        ),
        "score": coerce_float(first_present(evaluation.get("score"), perception_eval.get("score"))),
        "passed": diagnosis.get("passed") if isinstance(diagnosis.get("passed"), bool) else perception_eval.get("passed"),
        "metrics": {key: coerce_float(metrics.get(key)) for key in keys if key in metrics},
    }


def taxonomy_summary(failure_taxonomy: dict[str, Any] | None) -> dict[str, Any]:
    if not failure_taxonomy:
        return {"available": False, "taxonomy_labels": [], "failed_required_checks": []}

    return {
        "available": True,
        "video_semantic_claim": failure_taxonomy.get("video_semantic_claim"),
        "alignment_passed": failure_taxonomy.get("alignment_passed"),
        "taxonomy_labels": [str(label) for label in as_list(failure_taxonomy.get("taxonomy_labels"))],
        "failed_required_checks": as_list(failure_taxonomy.get("failed_required_checks")),
        "intervention_hints": [str(hint) for hint in as_list(failure_taxonomy.get("intervention_hints"))],
    }


def proposal_summary(refinement_proposal: dict[str, Any] | None) -> dict[str, Any]:
    if not refinement_proposal:
        return {"available": False}

    retry_policy = as_dict(refinement_proposal.get("retry_policy"))
    return {
        "available": True,
        "does_not_run_gpu": refinement_proposal.get("does_not_run_gpu"),
        "semantic_success_claim_allowed": refinement_proposal.get("semantic_success_claim_allowed"),
        "source_prompt": refinement_proposal.get("source_prompt"),
        "refined_prompt": refinement_proposal.get("refined_prompt"),
        "explicit_gpu_retry_approval_required": retry_policy.get("explicit_gpu_retry_approval_required"),
        "post_gpu_review_required_after_any_retry": retry_policy.get("post_gpu_review_required_after_any_retry"),
        "proposal_is_not_gpu_approval": retry_policy.get("proposal_is_not_gpu_approval"),
    }


def closed_loop_status(failed: dict[str, Any], retry: dict[str, Any]) -> str:
    if failed.get("video_semantic_claim") == "measured_failed" and retry.get("video_semantic_claim") == "measured_passed":
        return "measured_failed_to_measured_passed"
    return "incomplete_or_not_measured"


def build_case_summary(
    failed_alignment_eval: dict[str, Any],
    retry_alignment_eval: dict[str, Any],
    failure_taxonomy: dict[str, Any] | None = None,
    failed_perception_eval: dict[str, Any] | None = None,
    refinement_proposal: dict[str, Any] | None = None,
    case_id: str = "closed_loop_case",
) -> dict[str, Any]:
    failed = alignment_summary(failed_alignment_eval)
    retry = alignment_summary(retry_alignment_eval)

    return {
        "schema_version": "driveloop_closed_loop_case_summary.v0",
        "case_id": case_id,
        "closed_loop_status": closed_loop_status(failed, retry),
        "attempts": {
            "pre_refinement": failed,
            "post_refinement_retry": retry,
        },
        "failure_diagnosis": taxonomy_summary(failure_taxonomy),
        "failed_attempt_perception": perception_summary(failed_perception_eval),
        "refinement_proposal": proposal_summary(refinement_proposal),
        "evidence_chain": [
            "pre_refinement_generation",
            "external_alignment_review",
            "failure_taxonomy",
            "refinement_proposal",
            "explicit_retry_approval",
            "post_retry_alignment_review",
        ],
        "claim_boundary": {
            "summary_does_not_generate_video": True,
            "summary_does_not_run_gpu": True,
            "video_or_tensor_existence_is_not_semantic_success": True,
            "semantic_success_requires_measured_alignment_review": True,
            "closed_loop_case_is_not_strict_open_loop_baseline_comparison": True,
        },
        "remaining_work": [
            "recover_or_run_strict_open_loop_dd2_baseline",
            "add_perception_or_tracker_eval_for_measured_passed_retry",
            "repeat_closed_loop_protocol_on_more_long_tail_cases",
        ],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    failed = as_dict(as_dict(summary.get("attempts")).get("pre_refinement"))
    retry = as_dict(as_dict(summary.get("attempts")).get("post_refinement_retry"))
    taxonomy = as_dict(summary.get("failure_diagnosis"))
    perception = as_dict(summary.get("failed_attempt_perception"))
    proposal = as_dict(summary.get("refinement_proposal"))

    failed_checks = f"{format_value(failed.get('passed_required_check_count'))}/{format_value(failed.get('required_check_count'))}"
    retry_checks = f"{format_value(retry.get('passed_required_check_count'))}/{format_value(retry.get('required_check_count'))}"

    lines = [
        f"# Closed-loop Case Summary: {summary.get('case_id')}",
        "",
        "## Result",
        "",
        "| Stage | Claim | Score | Required checks | Passed |",
        "|---|---:|---:|---:|---:|",
        f"| Pre-refinement | `{failed.get('video_semantic_claim')}` | {format_value(failed.get('score'))} | {failed_checks} | {format_value(failed.get('passed'))} |",
        f"| Post-refinement retry | `{retry.get('video_semantic_claim')}` | {format_value(retry.get('score'))} | {retry_checks} | {format_value(retry.get('passed'))} |",
        "",
        "## Failure Diagnosis",
        "",
    ]

    labels = as_list(taxonomy.get("taxonomy_labels"))
    lines.extend(f"- `{label}`" for label in labels) if labels else lines.append("- not_available")

    lines.extend(["", "## Failed Attempt Perception", ""])
    metrics = as_dict(perception.get("metrics"))
    if metrics:
        lines.extend(["| Metric | Value |", "|---|---:|"])
        lines.extend(f"| {key} | {format_value(value)} |" for key, value in metrics.items())
    else:
        lines.append("not_available")

    lines.extend(
        [
            "",
            "## Refinement Proposal",
            "",
            f"- Available: `{proposal.get('available')}`",
            f"- Does not run GPU: `{proposal.get('does_not_run_gpu')}`",
            f"- Explicit retry approval required: `{proposal.get('explicit_gpu_retry_approval_required')}`",
            f"- Post-GPU review required: `{proposal.get('post_gpu_review_required_after_any_retry')}`",
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for key, value in as_dict(summary.get("claim_boundary")).items():
        lines.append(f"- `{key}`: `{value}`")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a DriveLoop closed-loop failed-to-passed case summary.")
    parser.add_argument("--case-id", default="closed_loop_case")
    parser.add_argument("--failed-alignment-eval", required=True, type=Path)
    parser.add_argument("--retry-alignment-eval", required=True, type=Path)
    parser.add_argument("--failure-taxonomy", type=Path, default=None)
    parser.add_argument("--failed-perception-eval", type=Path, default=None)
    parser.add_argument("--refinement-proposal", type=Path, default=None)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", type=Path, default=None)
    args = parser.parse_args()

    summary = build_case_summary(
        failed_alignment_eval=load_json(args.failed_alignment_eval),
        retry_alignment_eval=load_json(args.retry_alignment_eval),
        failure_taxonomy=load_json(args.failure_taxonomy) if args.failure_taxonomy else None,
        failed_perception_eval=load_json(args.failed_perception_eval) if args.failed_perception_eval else None,
        refinement_proposal=load_json(args.refinement_proposal) if args.refinement_proposal else None,
        case_id=args.case_id,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(args.output_json)

    if args.output_md is not None:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(summary), encoding="utf-8")
        print(args.output_md)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
