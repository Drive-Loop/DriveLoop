from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "driveloop_closed_loop_experiment_registry.v0"


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(value: str | None, manifest_dir: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.exists():
        return path
    candidate = manifest_dir / path
    if candidate.exists():
        return candidate
    return path


def pick(obj: dict[str, Any], dotted: str) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check_count(metrics: dict[str, Any]) -> str | None:
    passed = coerce_float(metrics.get("alignment_passed_required_check_count"))
    total = coerce_float(metrics.get("alignment_required_check_count"))
    if passed is None or total is None:
        return None
    return f"{passed:g}/{total:g}"


def alignment_summary(data: dict[str, Any]) -> dict[str, Any]:
    evaluation = as_dict(data.get("evaluation"))
    metrics = as_dict(evaluation.get("metrics"))
    diagnosis = as_dict(evaluation.get("diagnosis"))
    generation = as_dict(data.get("generation"))
    metadata = as_dict(generation.get("metadata"))
    interpretation = as_dict(data.get("interpretation"))

    review = as_dict(metadata.get("prompt_video_alignment"))
    manual_review_used = bool(
        review.get("source")
        or review.get("reviewer")
        or review.get("review_note")
        or review.get("review_notes")
    )

    return {
        "scenario_id": metadata.get("scenario_id"),
        "prompt": generation.get("prompt"),
        "video_semantic_claim": interpretation.get("video_semantic_claim"),
        "score": coerce_float(evaluation.get("score")),
        "passed": diagnosis.get("passed"),
        "checks": check_count(metrics),
        "manual_review_used": manual_review_used,
        "source": review.get("source"),
    }


def attempt_from_case_summary(case_summary: dict[str, Any], key: str) -> dict[str, Any]:
    attempt = as_dict(as_dict(case_summary.get("attempts")).get(key))
    return {
        "video_semantic_claim": attempt.get("video_semantic_claim"),
        "score": coerce_float(attempt.get("score")),
        "passed": attempt.get("passed"),
        "checks": (
            f"{coerce_float(attempt.get('passed_required_check_count')):g}/"
            f"{coerce_float(attempt.get('required_check_count')):g}"
            if coerce_float(attempt.get("passed_required_check_count")) is not None
            and coerce_float(attempt.get("required_check_count")) is not None
            else None
        ),
    }


def perception_passed_from(data: dict[str, Any]) -> bool:
    if not data:
        return False
    if pick(data, "evaluation.diagnosis.passed") is True:
        return True
    if data.get("passed") is True:
        return True
    if data.get("video_semantic_claim") == "measured_passed":
        return True
    if pick(data, "interpretation.video_semantic_claim") == "measured_passed":
        return True
    return False


def source_entry(path: Path | None) -> dict[str, Any]:
    return {
        "path": str(path) if path is not None else None,
        "exists": bool(path and path.exists()),
    }


def evidence_level(closed_loop_status: str | None, retry_claim: str | None, artifact_manifest: dict[str, Any]) -> str:
    if closed_loop_status == "measured_failed_to_measured_passed" and retry_claim == "measured_passed":
        return "case_study_evidence"
    if retry_claim in {"measured_passed", "measured_failed"}:
        return "measured_retry_evidence"
    if artifact_manifest.get("candidate_status") == "candidate_video_only":
        return "candidate_artifact_only"
    return "metadata_only"


def build_case_record(row: dict[str, Any], manifest_dir: Path) -> dict[str, Any]:
    case_id = str(row.get("case_id") or row.get("name") or "unknown_case")
    task_family = str(row.get("task_family") or "unspecified")

    case_summary_path = resolve_path(row.get("closed_loop_case_summary"), manifest_dir)
    runner_summary_path = resolve_path(row.get("runner_summary"), manifest_dir)
    artifact_manifest_path = resolve_path(row.get("artifact_manifest"), manifest_dir)
    dashboard_path = resolve_path(row.get("dashboard"), manifest_dir)
    failed_alignment_path = resolve_path(row.get("failed_alignment_eval"), manifest_dir)
    retry_alignment_path = resolve_path(row.get("retry_alignment_eval"), manifest_dir)
    perception_eval_path = resolve_path(row.get("perception_eval"), manifest_dir)
    baseline_summary_path = resolve_path(row.get("baseline_summary"), manifest_dir)

    case_summary = load_json(case_summary_path)
    runner_summary = load_json(runner_summary_path)
    artifact_manifest = load_json(artifact_manifest_path)
    dashboard = load_json(dashboard_path)
    failed_alignment = alignment_summary(load_json(failed_alignment_path))
    retry_alignment = alignment_summary(load_json(retry_alignment_path))
    perception_eval = load_json(perception_eval_path)

    pre = attempt_from_case_summary(case_summary, "pre_refinement")
    retry = attempt_from_case_summary(case_summary, "post_refinement_retry")

    pre_claim = pre.get("video_semantic_claim") or failed_alignment.get("video_semantic_claim")
    retry_claim = retry.get("video_semantic_claim") or retry_alignment.get("video_semantic_claim")
    pre_score = pre.get("score") if pre.get("score") is not None else failed_alignment.get("score")
    retry_score = retry.get("score") if retry.get("score") is not None else retry_alignment.get("score")
    pre_checks = pre.get("checks") or failed_alignment.get("checks")
    retry_checks = retry.get("checks") or retry_alignment.get("checks")

    scenario_id = (
        row.get("scenario_id")
        or retry_alignment.get("scenario_id")
        or failed_alignment.get("scenario_id")
        or artifact_manifest.get("scenario_id")
        or dashboard.get("scenario_id")
        or case_id
    )
    prompt = (
        row.get("prompt")
        or retry_alignment.get("prompt")
        or failed_alignment.get("prompt")
        or artifact_manifest.get("prompt")
        or dashboard.get("prompt")
    )

    manual_review_used = bool(
        retry_alignment.get("manual_review_used")
        or failed_alignment.get("manual_review_used")
        or "external_alignment_review" in as_list(case_summary.get("evidence_chain"))
        or "post_retry_alignment_review" in as_list(case_summary.get("evidence_chain"))
    )
    perception_passed = perception_passed_from(perception_eval)

    baseline_available = bool(row.get("baseline_available") or (baseline_summary_path and baseline_summary_path.exists()))
    strict_baseline_comparison_supported = bool(row.get("strict_baseline_comparison_supported"))
    automatic_multiround_supported = bool(row.get("automatic_multiround_supported"))

    status = case_summary.get("closed_loop_status")
    level = evidence_level(status, retry_claim, artifact_manifest)
    paper_claim_allowed = bool(level == "case_study_evidence" and manual_review_used)

    remaining_work = list(as_list(case_summary.get("remaining_work")))
    if not baseline_available:
        remaining_work.append("add_strict_open_loop_dd2_baseline_comparison")
    if not perception_passed:
        remaining_work.append("add_perception_or_tracker_eval_for_measured_passed_retry")
    if not automatic_multiround_supported:
        remaining_work.append("automate_generate_evaluate_diagnose_refine_regenerate_loop")

    return {
        "case_id": case_id,
        "task_family": task_family,
        "scenario_id": scenario_id,
        "prompt": prompt,
        "closed_loop_status": status or "not_available",
        "pre_claim": pre_claim,
        "pre_score": pre_score,
        "pre_checks": pre_checks,
        "retry_claim": retry_claim,
        "retry_score": retry_score,
        "retry_checks": retry_checks,
        "evidence_level": level,
        "manual_review_used": manual_review_used,
        "perception_passed": perception_passed,
        "baseline_available": baseline_available,
        "strict_baseline_comparison_supported": strict_baseline_comparison_supported,
        "automatic_multiround_supported": automatic_multiround_supported,
        "case_study_claim_allowed": paper_claim_allowed,
        "paper_claim_allowed": False,
        "remaining_work": sorted(set(remaining_work)),
        "sources": {
            "closed_loop_case_summary": source_entry(case_summary_path),
            "runner_summary": source_entry(runner_summary_path),
            "artifact_manifest": source_entry(artifact_manifest_path),
            "dashboard": source_entry(dashboard_path),
            "failed_alignment_eval": source_entry(failed_alignment_path),
            "retry_alignment_eval": source_entry(retry_alignment_path),
            "perception_eval": source_entry(perception_eval_path),
            "baseline_summary": source_entry(baseline_summary_path),
        },
        "claim_boundary": {
            "registry_record_is_not_video_semantic_success": True,
            "duplicate_sources_are_not_counted_as_separate_cases": True,
            "auto_matched_alignment_eval_is_metadata_link_not_new_review": True,
            "case_study_claim_allowed_means_single_case_evidence_only": paper_claim_allowed,
            "paper_claim_allowed_is_deprecated_use_case_study_claim_allowed": True,
            "strict_baseline_comparison_supported": strict_baseline_comparison_supported,
            "automatic_multiround_supported": automatic_multiround_supported,
            "semantic_success_requires_measured_review_or_perception": True,
            "runner_summary_semantic_success_claim_allowed": pick(runner_summary, "claim_boundary.semantic_success_claim_allowed"),
        },
    }



def infer_task_family(case_id: str, summary: dict[str, Any]) -> str:
    text = " ".join([
        case_id,
        str(summary.get("closed_loop_status") or ""),
        str(summary.get("refinement_proposal") or ""),
        str(summary.get("failure_diagnosis") or ""),
    ]).lower()

    if "motorcycle" in text and ("cut_in" in text or "cut-in" in text or "cut in" in text):
        return "motorcycle_cut_in"
    if "motorcycle" in text and ("lane_change" in text or "lane change" in text):
        return "motorcycle_lane_change"
    if "motorcycle" in text:
        return "motorcycle"
    if "pedestrian" in text:
        return "pedestrian"
    if "cyclist" in text or "bicycle" in text:
        return "vulnerable_road_user"
    return "unspecified"


def path_string(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)



def metric_signature(claim: Any, score: Any, checks: Any) -> tuple[str, str, str]:
    score_value = coerce_float(score)
    return (
        str(claim or ""),
        f"{score_value:.6f}" if score_value is not None else "",
        str(checks or ""),
    )


def alignment_signature_from_eval(data: dict[str, Any]) -> tuple[str, str, str]:
    summary = alignment_summary(data)
    return metric_signature(
        summary.get("video_semantic_claim"),
        summary.get("score"),
        summary.get("checks"),
    )


def alignment_signature_from_attempt(attempt: dict[str, Any]) -> tuple[str, str, str]:
    passed = coerce_float(attempt.get("passed_required_check_count"))
    total = coerce_float(attempt.get("required_check_count"))
    checks = f"{passed:g}/{total:g}" if passed is not None and total is not None else None
    return metric_signature(
        attempt.get("video_semantic_claim"),
        attempt.get("score"),
        checks,
    )


def index_alignment_evals(scan_root: Path) -> dict[tuple[str, str, str], list[Path]]:
    index: dict[tuple[str, str, str], list[Path]] = {}

    for path in sorted(scan_root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue

        if not isinstance(data, dict):
            continue
        if not {"generation", "evaluation", "interpretation"}.issubset(data.keys()):
            continue

        signature = alignment_signature_from_eval(data)
        if not all(signature):
            continue
        index.setdefault(signature, []).append(path)

    return index


def attach_alignment_eval_paths(row: dict[str, Any], summary: dict[str, Any], alignment_index: dict[tuple[str, str, str], list[Path]]) -> None:
    attempts = as_dict(summary.get("attempts"))

    for role, field in [
        ("pre_refinement", "failed_alignment_eval"),
        ("post_refinement_retry", "retry_alignment_eval"),
    ]:
        if row.get(field):
            continue

        attempt = as_dict(attempts.get(role))
        signature = alignment_signature_from_attempt(attempt)
        matches = alignment_index.get(signature, [])
        if len(matches) == 1:
            row[field] = path_string(matches[0])
        elif len(matches) > 1:
            row[f"{field}_candidates"] = [path_string(path) for path in matches]


def discover_registry_cases(scan_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    alignment_index = index_alignment_evals(scan_root)

    for path in sorted(scan_root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue

        if not isinstance(data, dict):
            continue
        if data.get("schema_version") != "driveloop_closed_loop_case_summary.v0":
            continue

        case_id = str(data.get("case_id") or path.stem)
        key = f"{case_id}:{path.resolve()}"
        if key in seen:
            continue
        seen.add(key)

        row: dict[str, Any] = {
            "case_id": case_id,
            "task_family": infer_task_family(case_id, data),
            "closed_loop_case_summary": path_string(path),
            "registry_source": "auto_discovered_closed_loop_case_summary",
        }

        runner_summary = path.parent / "runner_summary.json"
        if runner_summary.exists():
            row["runner_summary"] = path_string(runner_summary)

        attach_alignment_eval_paths(row, data, alignment_index)

        rows.append(row)

    return rows


def manifest_cases(manifest: Any) -> list[dict[str, Any]]:
    if isinstance(manifest, dict) and isinstance(manifest.get("cases"), list):
        return [as_dict(row) for row in manifest["cases"]]
    if isinstance(manifest, list):
        return [as_dict(row) for row in manifest]
    raise ValueError("registry manifest must be a list or contain a cases list")



def canonical_closed_loop_key(row: dict[str, Any]) -> str:
    task_family = str(row.get("task_family") or "unspecified")
    status = str(row.get("closed_loop_status") or "")
    pre_claim = str(row.get("pre_claim") or "")
    retry_claim = str(row.get("retry_claim") or "")
    pre_score = row.get("pre_score")
    retry_score = row.get("retry_score")

    if "candidate70" in str(row.get("case_id") or "").lower():
        return f"candidate70:{task_family}:{status}:{pre_claim}:{retry_claim}:{pre_score}:{retry_score}"

    return f"{row.get('case_id')}:{task_family}:{status}:{pre_claim}:{retry_claim}:{pre_score}:{retry_score}"


def deduplicate_case_records(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}

    for row in cases:
        key = canonical_closed_loop_key(row)
        existing = by_key.get(key)
        if existing is None:
            row["duplicate_sources"] = []
            by_key[key] = row
            continue

        existing_has_runner = as_dict(existing.get("sources")).get("runner_summary", {}).get("exists") is True
        row_has_runner = as_dict(row.get("sources")).get("runner_summary", {}).get("exists") is True

        if row_has_runner and not existing_has_runner:
            row["duplicate_sources"] = existing.get("duplicate_sources", []) + [
                existing.get("sources", {}).get("closed_loop_case_summary", {})
            ]
            by_key[key] = row
        else:
            existing.setdefault("duplicate_sources", []).append(
                row.get("sources", {}).get("closed_loop_case_summary", {})
            )

    return list(by_key.values())


def build_registry(manifest: dict[str, Any] | list[Any], manifest_dir: Path | None = None) -> dict[str, Any]:
    manifest_dir = manifest_dir or Path.cwd()
    raw_cases = [build_case_record(row, manifest_dir) for row in manifest_cases(manifest)]
    cases = deduplicate_case_records(raw_cases)

    return {
        "raw_case_count": len(raw_cases),
        "deduplicated_case_count": len(cases),
        "schema_version": SCHEMA_VERSION,
        "case_count": len(cases),
        "case_study_evidence_count": sum(1 for row in cases if row["evidence_level"] == "case_study_evidence"),
        "case_study_claim_allowed_count": sum(1 for row in cases if row["case_study_claim_allowed"]),
        "paper_claim_allowed_count": sum(1 for row in cases if row["paper_claim_allowed"]),
        "strict_baseline_comparison_supported_count": sum(
            1 for row in cases if row["strict_baseline_comparison_supported"]
        ),
        "automatic_multiround_supported_count": sum(1 for row in cases if row["automatic_multiround_supported"]),
        "perception_passed_count": sum(1 for row in cases if row["perception_passed"]),
        "cases": cases,
        "claim_boundary": {
            "registry_is_not_video_semantic_success": True,
            "case_study_evidence_is_not_section4_quantitative_comparison": True,
            "strict_baseline_table_requires_baseline_available_and_supported": True,
            "automatic_multiround_claim_requires_automatic_multiround_supported": True,
            "duplicate_closed_loop_summaries_are_collapsed": True,
            "auto_matched_alignment_evals_are_not_new_semantic_evidence": True,
        },
    }


def fmt(value: Any) -> str:
    if value is None:
        return "not_available"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def render_markdown(registry: dict[str, Any]) -> str:
    lines = [
        "# DriveLoop Closed-loop Experiment Registry",
        "",
        f"- schema_version: `{registry.get('schema_version')}`",
        f"- raw_case_count: `{registry.get('raw_case_count', registry.get('case_count'))}`",
        f"- deduplicated_case_count: `{registry.get('deduplicated_case_count', registry.get('case_count'))}`",
        f"- case_count: `{registry.get('case_count')}`",
        f"- case_study_evidence_count: `{registry.get('case_study_evidence_count')}`",
        f"- case_study_claim_allowed_count: `{registry.get('case_study_claim_allowed_count')}`",
        "",
        "| case | family | status | pre | retry | evidence | case-study claim | strict baseline | automatic loop | perception passed |",
        "|---|---|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in as_list(registry.get("cases")):
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt(row.get("case_id")),
                    fmt(row.get("task_family")),
                    fmt(row.get("closed_loop_status")),
                    f"{fmt(row.get('pre_claim'))} / {fmt(row.get('pre_score'))} / {fmt(row.get('pre_checks'))}",
                    f"{fmt(row.get('retry_claim'))} / {fmt(row.get('retry_score'))} / {fmt(row.get('retry_checks'))}",
                    fmt(row.get("evidence_level")),
                    fmt(row.get("case_study_claim_allowed")),
                    fmt(row.get("strict_baseline_comparison_supported")),
                    fmt(row.get("automatic_multiround_supported")),
                    fmt(row.get("perception_passed")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Remaining Work", ""])
    for row in as_list(registry.get("cases")):
        lines.append(f"### {row.get('case_id')}")
        work = as_list(row.get("remaining_work"))
        lines.extend(f"- `{item}`" for item in work) if work else lines.append("- none")

    lines.extend(["", "## Claim Boundary", ""])
    for key, value in as_dict(registry.get("claim_boundary")).items():
        lines.append(f"- `{key}`: `{value}`")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a multi-case DriveLoop closed-loop experiment registry.")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--manifest", type=Path)
    input_group.add_argument("--scan-root", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    if args.manifest is not None:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        manifest_dir = args.manifest.parent
    else:
        manifest = {"cases": discover_registry_cases(args.scan_root)}
        manifest_dir = Path.cwd()

    registry = build_registry(manifest, manifest_dir)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(registry), encoding="utf-8")

    print(args.output_json)
    print(args.output_md)
    print(json.dumps(registry, indent=2))


if __name__ == "__main__":
    main()
