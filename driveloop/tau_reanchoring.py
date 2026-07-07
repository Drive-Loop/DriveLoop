"""Transparent acceptance-threshold (tau) re-anchoring from experiment arms.

tau=0.7 was chosen under inflated metrics (clones, mirrored geometry,
all-view max S_perc); the clean J distribution shifted down ~0.15-0.2.
This module derives tau candidates from the OPEN-LOOP arm of a given
capability configuration using fixed transparent rules (mean + k * std,
percentiles of the per-case best-J distribution).

Protocol: anchor on the open-loop arm only; freeze the RULE, not the
value (re-derive from the new open-loop arm when checkpoint / frame_num
/ source scene changes); never re-use the anchoring runs as comparison
evidence (circular). Acceptance in the runner is best-J >= tau, so
candidates and acceptance counts are computed on per-case best J;
attempt-level J is context only.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "driveloop_tau_reanchoring.v0"

DEFAULT_STD_MULTIPLIERS = (0.5, 1.0)
DEFAULT_PERCENTILES = (75.0, 90.0)


@dataclass
class ArmDistribution:
    name: str
    directory: str
    case_names: List[str] = field(default_factory=list)
    best_j: List[float] = field(default_factory=list)
    attempt_j: List[float] = field(default_factory=list)
    accepted_count_recorded: Optional[int] = None


def _as_float(value: Any) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result):
        return None
    return result


def percentile(values: List[float], q: float) -> float:
    """Linear-interpolation percentile (numpy default convention)."""
    if not values:
        raise ValueError("percentile of empty list")
    if not 0.0 <= q <= 100.0:
        raise ValueError(f"percentile out of range: {q}")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (q / 100.0)
    low = int(math.floor(rank))
    high = int(math.ceil(rank))
    if low == high:
        return ordered[low]
    fraction = rank - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


def summarize(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {
            "count": 0, "mean": None, "std": None, "min": None,
            "max": None, "median": None, "p75": None, "p90": None,
        }
    count = len(values)
    mean = sum(values) / count
    if count >= 2:
        variance = sum((v - mean) ** 2 for v in values) / (count - 1)
        std = math.sqrt(variance)
    else:
        std = None
    return {
        "count": count,
        "mean": round(mean, 6),
        "std": round(std, 6) if std is not None else None,
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "median": round(percentile(values, 50.0), 6),
        "p75": round(percentile(values, 75.0), 6),
        "p90": round(percentile(values, 90.0), 6),
    }


def _case_best_j(case: Dict[str, Any]) -> Optional[float]:
    metrics = case.get("best_metrics")
    if isinstance(metrics, dict):
        j = _as_float(metrics.get("J"))
        if j is not None:
            return j
    return _as_float(case.get("best_score"))


def _attempt_j(row: Dict[str, Any]) -> Optional[float]:
    evaluation = row.get("evaluation")
    if not isinstance(evaluation, dict):
        return None
    metrics = evaluation.get("metrics")
    if isinstance(metrics, dict):
        j = _as_float(metrics.get("J"))
        if j is not None:
            return j
    return _as_float(evaluation.get("score"))


def load_arm(name: str, directory: Path | str) -> ArmDistribution:
    """Load one arm dir in the ExperimentPipeline layout:
    <dir>/summary.json plus <dir>/<case-slug>/attempts.jsonl per case."""
    arm_dir = Path(directory)
    summary_path = arm_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"arm '{name}': missing {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    arm = ArmDistribution(name=name, directory=str(arm_dir))
    arm.accepted_count_recorded = (
        int(summary["accepted_count"]) if "accepted_count" in summary else None
    )
    for case in summary.get("cases", []):
        if not isinstance(case, dict):
            continue
        best = _case_best_j(case)
        if best is None:
            continue
        arm.case_names.append(str(case.get("name")))
        arm.best_j.append(best)
    for attempts_path in sorted(arm_dir.glob("*/attempts.jsonl")):
        for line in attempts_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            j = _attempt_j(json.loads(line))
            if j is not None:
                arm.attempt_j.append(j)
    if not arm.best_j:
        raise ValueError(f"arm '{name}': no case-level J values in {summary_path}")
    return arm


def candidate_taus(
    anchor_best_j: List[float],
    std_multipliers=DEFAULT_STD_MULTIPLIERS,
    percentiles=DEFAULT_PERCENTILES,
) -> Dict[str, Optional[float]]:
    stats = summarize(anchor_best_j)
    candidates: Dict[str, Optional[float]] = {}
    for k in std_multipliers:
        key = f"anchor_mean_plus_{k:g}_std".replace(".", "p")
        if stats["mean"] is not None and stats["std"] is not None:
            candidates[key] = round(stats["mean"] + k * stats["std"], 6)
        else:
            candidates[key] = None
    for q in percentiles:
        candidates[f"anchor_p{q:g}"] = round(percentile(anchor_best_j, q), 6)
    return candidates


def acceptance_at(arm: ArmDistribution, tau: float) -> Dict[str, Any]:
    accepted = [name for name, j in zip(arm.case_names, arm.best_j) if j >= tau]
    return {
        "accepted_count": len(accepted),
        "case_count": len(arm.best_j),
        "accepted_cases": accepted,
    }


def build_tau_reanchoring(
    arm_dirs: Dict[str, Path | str],
    anchor_arm: str,
    current_tau: float,
    primary_rule: str = "anchor_mean_plus_1_std",
    capability_configuration: Optional[str] = None,
) -> Dict[str, Any]:
    if anchor_arm not in arm_dirs:
        raise ValueError(f"anchor arm '{anchor_arm}' not among arms: {sorted(arm_dirs)}")
    arms = {name: load_arm(name, directory) for name, directory in arm_dirs.items()}
    anchor = arms[anchor_arm]

    candidates = candidate_taus(anchor.best_j)
    if primary_rule not in candidates:
        raise ValueError(
            f"primary rule '{primary_rule}' not among candidates: {sorted(candidates)}"
        )
    proposed = candidates[primary_rule]
    proposed_grid = (
        round(round(proposed / 0.05) * 0.05, 2) if proposed is not None else None
    )

    evaluated_taus: Dict[str, Optional[float]] = {"current_tau": current_tau, **candidates}
    acceptance: Dict[str, Dict[str, Any]] = {}
    for label, tau in evaluated_taus.items():
        if tau is None:
            continue
        acceptance[label] = {
            "tau": round(float(tau), 6),
            "per_arm": {name: acceptance_at(arm, float(tau)) for name, arm in arms.items()},
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "capability_configuration": capability_configuration,
        "anchor_arm": anchor_arm,
        "current_tau": current_tau,
        "primary_rule": primary_rule,
        "proposed_tau": proposed,
        "proposed_tau_grid_0p05": proposed_grid,
        "candidates": candidates,
        "arms": {
            name: {
                "directory": arm.directory,
                "case_names": arm.case_names,
                "best_j": [round(v, 6) for v in arm.best_j],
                "best_j_stats": summarize(arm.best_j),
                "attempt_j_stats": summarize(arm.attempt_j),
                "accepted_count_recorded": arm.accepted_count_recorded,
            }
            for name, arm in arms.items()
        },
        "acceptance_table": acceptance,
        "claim_boundary": {
            "tau_reanchoring_is_not_video_semantic_success": True,
            "anchored_on_single_arm_distribution": True,
            "anchor_arm_is_open_loop_baseline": anchor_arm == "open_loop",
            "comparison_requires_fresh_runs_at_frozen_tau": True,
            "reusing_anchoring_runs_for_comparison_is_circular": True,
            "rule_must_be_rederived_per_capability_configuration": True,
            "small_anchor_sample_caveat": len(anchor.best_j) < 10,
            "anchor_case_count": len(anchor.best_j),
            "paper_claims_require_manual_spot_check": True,
        },
    }


def render_markdown(manifest: Dict[str, Any]) -> str:
    lines = [
        "# Tau re-anchoring analysis",
        "",
        f"- schema_version: `{manifest['schema_version']}`",
        f"- capability_configuration: `{manifest.get('capability_configuration')}`",
        f"- anchor_arm: `{manifest['anchor_arm']}`",
        f"- current_tau: `{manifest['current_tau']}`",
        f"- primary_rule: `{manifest['primary_rule']}`",
        f"- proposed_tau: `{manifest['proposed_tau']}`"
        f" (0.05 grid: `{manifest['proposed_tau_grid_0p05']}`)",
        "",
        "## Arm best-J distributions",
        "",
        "| arm | n | mean | std | min | median | max |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, arm in manifest["arms"].items():
        s = arm["best_j_stats"]
        lines.append(
            f"| {name} | {s['count']} | {s['mean']} | {s['std']} | "
            f"{s['min']} | {s['median']} | {s['max']} |"
        )
    lines.extend(["", "## Acceptance counts per candidate tau", ""])
    arm_names = list(manifest["arms"])
    header = "| rule | tau | " + " | ".join(arm_names) + " |"
    sep = "| --- | ---: | " + " | ".join("---:" for _ in arm_names) + " |"
    lines.extend([header, sep])
    for label, row in manifest["acceptance_table"].items():
        cells = [
            f"{row['per_arm'][name]['accepted_count']}/{row['per_arm'][name]['case_count']}"
            for name in arm_names
        ]
        lines.append(f"| {label} | {row['tau']} | " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "Claim boundary: threshold anchoring only; not video semantic-success "
            "evidence. Comparisons require fresh runs at the frozen tau.",
            "",
        ]
    )
    return "\n".join(lines)
