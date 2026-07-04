from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_ALIGNMENT_EVAL = Path(
    "outputs/driveloop/prompt_video_alignment_eval/"
    "candidate70_night_cut_in_gpu_smoke/"
    "prompt_video_alignment_evaluation.json"
)
DEFAULT_CANDIDATE_AUDIT = Path(
    "outputs/driveloop/prompt_conditional_candidate_audit/"
    "motorcycle_source_candidate70_against_night_lane_change_cut_in_prompt_audit.json"
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def checks_from_alignment_eval(alignment_eval: dict[str, Any]) -> list[dict[str, Any]]:
    generation = alignment_eval.get("generation", {})
    metadata = generation.get("metadata", {}) if isinstance(generation, dict) else {}
    alignment = metadata.get("prompt_video_alignment", {}) if isinstance(metadata, dict) else {}
    checks = alignment.get("checks", []) if isinstance(alignment, dict) else []
    return [check for check in checks if isinstance(check, dict)]


def classify_failed_check(check: dict[str, Any]) -> list[str]:
    name = str(check.get("name", "")).lower()
    evidence = str(check.get("evidence", "")).lower()
    labels: list[str] = []

    if "object_presence" in name:
        labels.append("object_identity_failed")
    if "motorcycle" in name or "motorcycle" in evidence or "scooter" in name or "scooter" in evidence or "two-wheeler" in evidence:
        labels.append("motorcycle_identity_failed")
    if "object_consistency" in name or "trackable" in name or "track" in evidence:
        labels.append("tracking_identity_failed")
    if "cut_in" in name or "cut-in" in name or "cut in" in evidence or "cut-in" in evidence:
        labels.append("cut_in_motion_failed")
        labels.append("lane_change_motion_failed")
    if "lane_change" in name or "lane change" in evidence or "lane-change" in evidence:
        labels.append("lane_change_motion_failed")
    if "lateral_displacement" in name or "lateral displacement" in evidence:
        labels.append("lateral_motion_failed")
    if "spatial_relation" in name:
        labels.append("spatial_relation_failed")
    if "hdmap_alignment" in name:
        labels.append("hdmap_alignment_failed")
    if "double solid" in evidence or "solid lines" in evidence:
        labels.append("road_marking_conflict")
    if "not confident" in evidence or "uncertain" in evidence or "not clearly visible" in evidence:
        labels.append("low_visual_confidence")

    return labels


def unique_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def intervention_hints(labels: list[str], candidate_allowed: bool) -> list[str]:
    hints: list[str] = []

    if candidate_allowed:
        hints.append("candidate_support_is_not_the_primary_blocker")
    else:
        hints.append("fix_or_replace_prompt_conditioned_source_candidate_before_gpu")

    if "object_identity_failed" in labels or "motorcycle_identity_failed" in labels:
        hints.extend(
            [
                "audit candidate-to-DD2 object class transfer",
                "inspect whether motorcycle boxes/class labels enter DD2 runtime inputs",
                "consider stronger object identity conditioning before another GPU run",
            ]
        )

    if "tracking_identity_failed" in labels:
        hints.extend(
            [
                "require the same target actor to remain trackable across sampled frames",
                "consider detector/tracker or VLM-assisted identity review before another GPU run",
            ]
        )

    if "cut_in_motion_failed" in labels or "lane_change_motion_failed" in labels or "spatial_relation_failed" in labels:
        hints.extend(
            [
                "audit trajectory/temporal motion runtime surfaces before another GPU run",
                "do not rely on static boxes3d alone for lane-change claims",
                "check whether per-frame actor displacement or lane geometry can be connected",
                "make the target two-wheeler larger, visible, and laterally displaced toward the ego path",
            ]
        )

    if "lateral_motion_failed" in labels:
        hints.append("require measurable lateral displacement across the reviewed frames")

    if "road_marking_conflict" in labels or "hdmap_alignment_failed" in labels:
        hints.append("audit HDMap/lane geometry compatibility with requested lane change")

    if "low_visual_confidence" in labels:
        hints.append("preserve contact sheet evidence and consider perception/VLM-assisted object review")

    hints.append("run audit-only/runtime tensor checks before any new GPU candidate")
    hints.append("record negative results if the next candidate still fails")

    return unique_preserve_order(hints)


def build_taxonomy(
    alignment_eval: dict[str, Any],
    candidate_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_audit = candidate_audit or {}
    checks = checks_from_alignment_eval(alignment_eval)
    failed_checks = [check for check in checks if check.get("required") is True and check.get("passed") is False]

    labels: list[str] = []
    failed_check_summaries: list[dict[str, Any]] = []
    for check in failed_checks:
        check_labels = classify_failed_check(check)
        labels.extend(check_labels)
        failed_check_summaries.append(
            {
                "name": check.get("name"),
                "score": check.get("score"),
                "evidence": check.get("evidence"),
                "labels": check_labels,
            }
        )

    labels = unique_preserve_order(labels)

    interpretation = alignment_eval.get("interpretation", {})
    evaluation = alignment_eval.get("evaluation", {})
    diagnosis = evaluation.get("diagnosis", {}) if isinstance(evaluation, dict) else {}

    candidate_allowed = candidate_audit.get("allowed") is True

    return {
        "schema_version": "driveloop_alignment_failure_taxonomy.v0",
        "video_semantic_claim": interpretation.get("video_semantic_claim", "unknown"),
        "alignment_passed": diagnosis.get("passed") is True,
        "candidate_support_allowed": candidate_allowed,
        "candidate_support_status": candidate_audit.get("status", "unknown"),
        "taxonomy_labels": labels,
        "failed_required_checks": failed_check_summaries,
        "intervention_hints": intervention_hints(labels, candidate_allowed),
        "claim_boundary": {
            "taxonomy_is_diagnostic_not_success_claim": True,
            "candidate_support_is_not_generation_success": True,
            "new_gpu_run_requires_prior_runtime_audit": True,
            "semantic_success_requires_measured_passed_review": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify prompt-video alignment failures into intervention-oriented labels.")
    parser.add_argument("--alignment-eval", type=Path, default=DEFAULT_ALIGNMENT_EVAL)
    parser.add_argument("--candidate-audit", type=Path, default=DEFAULT_CANDIDATE_AUDIT)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    taxonomy = build_taxonomy(
        alignment_eval=load_json(args.alignment_eval),
        candidate_audit=load_json(args.candidate_audit),
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(taxonomy, indent=2), encoding="utf-8")
    print(args.output)
    print(json.dumps(taxonomy, indent=2))


if __name__ == "__main__":
    main()
