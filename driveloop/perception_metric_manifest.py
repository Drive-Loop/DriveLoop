from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


SCHEMA_VERSION = "driveloop_perception_metric_manifest.v0"
PERCEPTION_VIDEO_EVAL_SCHEMA_VERSION = "driveloop_perception_video_eval.v0"
EQ15_METRIC_KEYS = ("Q_cov", "Q_conf", "Q_track", "Q_id", "Q_box")


def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {}


def coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pick_metric(metrics: dict[str, Any], key: str) -> tuple[float | None, str | None]:
    if key in metrics:
        return coerce_float(metrics.get(key)), key

    suffix = f"_{key}"
    matches = sorted(name for name in metrics if str(name).endswith(suffix))
    if not matches:
        return None, None

    source_key = matches[0]
    return coerce_float(metrics.get(source_key)), source_key


def source_prefix(source_key: str, key: str) -> str | None:
    if source_key == key:
        return None
    suffix = f"_{key}"
    if source_key.endswith(suffix):
        return source_key[: -len(suffix)]
    return None


def unwrap_evaluation(payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    data = as_dict(payload)
    evaluation = as_dict(data.get("evaluation")) or data
    interpretation = as_dict(data.get("interpretation"))
    return evaluation, interpretation


def infer_perception_claim(
    measured: bool,
    passed: bool,
    interpretation: dict[str, Any],
) -> str:
    claim = interpretation.get("perception_claim")
    if claim in {"measured_passed", "measured_failed", "not_measured"}:
        return str(claim)
    if not measured:
        return "not_measured"
    return "measured_passed" if passed else "measured_failed"


def build_perception_metric_manifest(
    payload: Any,
    source: str = "inline",
) -> dict[str, Any]:
    data = as_dict(payload)
    evaluation, interpretation = unwrap_evaluation(data)
    metrics = as_dict(evaluation.get("metrics"))
    diagnosis = as_dict(evaluation.get("diagnosis"))

    if not data and not metrics:
        return {
            "schema_version": SCHEMA_VERSION,
            "available": False,
            "source": source,
            "evaluator": "not_available",
            "perception_claim": "not_available",
            "score": None,
            "measured": False,
            "passed": False,
            "metrics_complete": False,
            "metrics": {key: None for key in EQ15_METRIC_KEYS},
            "metric_source_keys": {},
            "missing_metrics": list(EQ15_METRIC_KEYS),
            "source_metric_prefixes": [],
            "claim_boundary": {
                "perception_metric_manifest_is_not_video_semantic_success": True,
                "perception_metrics_do_not_prove_prompt_video_alignment": True,
            },
        }

    eq15_metrics: dict[str, float | None] = {}
    source_keys: dict[str, str] = {}
    prefixes: set[str] = set()

    for key in EQ15_METRIC_KEYS:
        value, source_key = pick_metric(metrics, key)
        eq15_metrics[key] = value
        if source_key:
            source_keys[key] = source_key
            prefix = source_prefix(source_key, key)
            if prefix:
                prefixes.add(prefix)

    measured_value, measured_key = pick_metric(metrics, "perception_measured")
    if measured_key:
        prefix = source_prefix(measured_key, "perception_measured")
        if prefix:
            prefixes.add(prefix)

    measured = measured_value == 1.0 or interpretation.get("perception_claim") in {"measured_passed", "measured_failed"}
    passed = diagnosis.get("passed") is True
    perception_claim = infer_perception_claim(measured, passed, interpretation)
    missing_metrics = [key for key, value in eq15_metrics.items() if value is None]
    metrics_complete = not missing_metrics

    evaluator = "PerceptionVideoEvaluator"
    if prefixes:
        evaluator = sorted(prefixes)[0].split("_")[-1]
    elif data.get("schema_version") != PERCEPTION_VIDEO_EVAL_SCHEMA_VERSION and not metrics:
        evaluator = "unknown"

    return {
        "schema_version": SCHEMA_VERSION,
        "available": True,
        "source": source,
        "evaluator": evaluator,
        "perception_eval_schema_version": data.get("schema_version"),
        "perception_claim": perception_claim,
        "semantic_success_claim": interpretation.get("semantic_success_claim", "not_proven_by_perception_metrics_alone"),
        "score": coerce_float(evaluation.get("score")),
        "measured": measured,
        "passed": passed,
        "metrics_complete": metrics_complete,
        "metrics": eq15_metrics,
        "metric_source_keys": source_keys,
        "missing_metrics": missing_metrics,
        "source_metric_prefixes": sorted(prefixes),
        "diagnosis_reasons": list(diagnosis.get("reasons") or []),
        "claim_boundary": {
            "perception_metric_manifest_is_not_video_semantic_success": True,
            "perception_metrics_do_not_prove_prompt_video_alignment": True,
            "semantic_success_requires_alignment_or_human_review": True,
            "not_measured_is_valid_negative_evidence": True,
        },
    }
