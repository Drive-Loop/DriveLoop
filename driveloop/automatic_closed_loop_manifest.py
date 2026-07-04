from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "driveloop_automatic_closed_loop_manifest.v0"


def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pick(obj: dict[str, Any], dotted: str) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def load_history_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def records_from_result(value: Any) -> list[Any]:
    data = as_dict(value)

    if isinstance(value, list):
        return value

    attempt_history = data.get("attempt_history")
    if isinstance(attempt_history, list):
        return attempt_history

    history = data.get("history")
    if isinstance(history, list):
        return history

    if hasattr(value, "attempt_history"):
        return list(getattr(value, "attempt_history"))

    if hasattr(value, "history"):
        return list(getattr(value, "history"))

    if data:
        return [data]

    return []


def normalize_attempt(record: Any, index: int) -> dict[str, Any]:
    if isinstance(record, tuple) and len(record) >= 2:
        generation = as_dict(record[0])
        evaluation = as_dict(record[1])
        raw = {}
    else:
        raw = as_dict(record)
        attempt = as_dict(raw.get("attempt")) or raw
        generation = as_dict(attempt.get("generation"))
        evaluation = as_dict(attempt.get("evaluation"))
        raw = attempt

    diagnosis = as_dict(evaluation.get("diagnosis"))
    score = coerce_float(evaluation.get("score"))
    passed = diagnosis.get("passed") is True or raw.get("passed") is True
    if score is None:
        score = coerce_float(raw.get("score"))

    refinement = as_dict(raw.get("refinement"))
    prompt = generation.get("prompt") or raw.get("prompt")
    iteration = generation.get("iteration")
    if iteration is None:
        iteration = raw.get("iteration", index)

    claim_boundary = as_dict(raw.get("claim_boundary"))
    metadata = as_dict(generation.get("metadata"))

    return {
        "index": index,
        "iteration": iteration,
        "prompt": prompt,
        "has_generation": bool(generation) or "generation" in raw,
        "has_evaluation": bool(evaluation) or "evaluation" in raw,
        "has_refinement": bool(refinement),
        "refinement": refinement,
        "score": score,
        "passed": passed,
        "diagnosis_reasons": list(as_list(diagnosis.get("reasons"))),
        "suggested_actions": list(as_list(diagnosis.get("suggested_actions"))),
        "claim_boundary": claim_boundary,
        "metadata": metadata,
        "raw_keys": sorted(raw.keys()),
    }


def audit_only_detected(attempts: list[dict[str, Any]], source_payload: Any = None) -> bool:
    source = as_dict(source_payload)
    if pick(source, "claim_boundary.runner_is_audit_only") is True:
        return True
    if pick(source, "claim_boundary.orchestrator_does_not_generate_video") is True:
        return True
    if pick(source, "claim_boundary.summary_does_not_generate_video") is True:
        return True

    for attempt in attempts:
        claim = as_dict(attempt.get("claim_boundary"))
        if claim.get("runner_is_audit_only") is True:
            return True
        if claim.get("summary_does_not_generate_video") is True:
            return True
        if claim.get("orchestrator_does_not_generate_video") is True:
            return True
    return False


def manual_review_dependency_detected(attempts: list[dict[str, Any]], source_payload: Any = None) -> bool:
    text = json.dumps(as_dict(source_payload), sort_keys=True).lower()
    if "manual_review" in text or "external_alignment_review" in text:
        return True

    for attempt in attempts:
        attempt_text = json.dumps(attempt, sort_keys=True).lower()
        if "manual_review" in attempt_text or "external_alignment_review" in attempt_text:
            return True
    return False


def transition_rows(attempts: list[dict[str, Any]], target_score: float) -> list[dict[str, Any]]:
    rows = []
    for current, nxt in zip(attempts, attempts[1:]):
        current_score = coerce_float(current.get("score"))
        current_failed = (
            current.get("passed") is not True
            and (current_score is None or current_score < target_score)
        )
        prompt_changed = bool(current.get("prompt") and nxt.get("prompt") and current.get("prompt") != nxt.get("prompt"))
        has_refinement = bool(current.get("has_refinement") or prompt_changed)
        rows.append(
            {
                "from_iteration": current.get("iteration"),
                "to_iteration": nxt.get("iteration"),
                "evaluate_failed": current_failed,
                "diagnose_available": bool(current.get("diagnosis_reasons") or current.get("suggested_actions") or current_failed),
                "refine_available": has_refinement,
                "regenerate_available": nxt.get("has_generation") is True,
                "prompt_changed": prompt_changed,
                "transition_complete": bool(current_failed and has_refinement and nxt.get("has_generation") is True),
            }
        )
    return rows


def build_automatic_closed_loop_manifest(
    result_or_records: Any,
    *,
    target_score: float = 0.8,
    source: str = "inline",
) -> dict[str, Any]:
    raw_records = records_from_result(result_or_records)
    attempts = [normalize_attempt(record, index) for index, record in enumerate(raw_records)]

    transitions = transition_rows(attempts, target_score)
    final = attempts[-1] if attempts else {}
    final_score = coerce_float(final.get("score"))
    final_accepted = bool(final.get("passed") is True or (final_score is not None and final_score >= target_score))

    audit_only = audit_only_detected(attempts, result_or_records)
    manual_dependency = manual_review_dependency_detected(attempts, result_or_records)
    generated_count = sum(1 for attempt in attempts if attempt.get("has_generation") is True)
    evaluated_count = sum(1 for attempt in attempts if attempt.get("has_evaluation") is True)
    complete_transition_count = sum(1 for row in transitions if row["transition_complete"])

    automatic_loop_supported = bool(
        attempts
        and generated_count == len(attempts)
        and evaluated_count == len(attempts)
        and final_accepted
        and not audit_only
        and not manual_dependency
    )
    automatic_multiround_supported = bool(
        automatic_loop_supported
        and len(attempts) >= 2
        and complete_transition_count == len(transitions)
    )

    blockers = []
    if not attempts:
        blockers.append("no_attempt_records")
    if audit_only:
        blockers.append("audit_only_trace_does_not_execute_generation")
    if manual_dependency:
        blockers.append("manual_review_dependency_detected")
    if generated_count != len(attempts):
        blockers.append("missing_generation_records")
    if evaluated_count != len(attempts):
        blockers.append("missing_evaluation_records")
    if len(attempts) >= 2 and complete_transition_count != len(transitions):
        blockers.append("incomplete_generate_evaluate_refine_regenerate_transition")
    if not final_accepted:
        blockers.append("final_attempt_not_accepted_by_system_evaluator")

    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "target_score": target_score,
        "attempt_count": len(attempts),
        "generated_attempt_count": generated_count,
        "evaluated_attempt_count": evaluated_count,
        "automatic_loop_supported": automatic_loop_supported,
        "automatic_multiround_supported": automatic_multiround_supported,
        "complete_transition_count": complete_transition_count,
        "final_accepted": final_accepted,
        "audit_only_detected": audit_only,
        "manual_review_dependency_detected": manual_dependency,
        "blockers": blockers,
        "transitions": transitions,
        "attempts": attempts,
        "claim_boundary": {
            "automatic_loop_manifest_is_not_video_semantic_success": True,
            "manual_review_evidence_does_not_count_as_automatic_loop": True,
            "audit_only_or_command_plan_does_not_count_as_regeneration": True,
            "automatic_multiround_requires_system_generate_evaluate_refine_regenerate": True,
        },
    }
