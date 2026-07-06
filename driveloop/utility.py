"""Task-aware utility (paper Eq. 5).

J_t = w_p * S_perc + w_c * S_ctrl + w_i * S_intent

S_perc comes from the perception evaluator. S_ctrl uses a measured
prompt-video alignment score when available, otherwise it falls back to the
plan-level control coverage score (Eq. 10). S_intent measures how much of the
original user intent is retained by the current scene specification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from driveloop.longtail import control_coverage
from driveloop.schema import LongTailConditionPlan, SceneSpecification


@dataclass(frozen=True)
class UtilityWeights:
    perception: float = 0.5
    control: float = 0.3
    intent: float = 0.2

    def normalized(self) -> "UtilityWeights":
        total = self.perception + self.control + self.intent
        if total <= 0:
            return self
        return UtilityWeights(self.perception / total, self.control / total, self.intent / total)


def _retention(original: Iterable[str], current: Iterable[str]) -> Optional[float]:
    original_set, current_set = set(original), set(current)
    if not original_set:
        return None
    return len(original_set & current_set) / len(original_set)


def _informative_environment(environment: Dict[str, Any]) -> Iterable[str]:
    skip = {None, "", "unspecified", "unknown", "normal"}
    return ["%s=%s" % (k, v) for k, v in environment.items() if v not in skip]


def intent_consistency(original: SceneSpecification, current: SceneSpecification) -> float:
    """Recall-oriented: fraction of the original intent elements retained."""
    components = []
    for r in (
        _retention([o.category for o in original.objects], [o.category for o in current.objects]),
        _retention(original.motion_primitives, current.motion_primitives),
        _retention(original.relations, current.relations),
        _retention(_informative_environment(original.environment), _informative_environment(current.environment)),
    ):
        if r is not None:
            components.append(r)
    if not components:
        return 1.0
    return round(sum(components) / len(components), 6)


def task_utility(
    perception_score: float,
    condition_plan: LongTailConditionPlan,
    original_spec: SceneSpecification,
    current_spec: SceneSpecification,
    alignment_score: Optional[float] = None,
    weights: Optional[UtilityWeights] = None,
) -> Dict[str, Any]:
    w = (weights or UtilityWeights()).normalized()
    if alignment_score is not None:
        s_ctrl, s_ctrl_source = float(alignment_score), "measured_alignment"
    else:
        s_ctrl, s_ctrl_source = float(control_coverage(condition_plan)["score"]), "control_coverage_plan"
    s_intent = intent_consistency(original_spec, current_spec)
    s_perc = float(perception_score)
    j = w.perception * s_perc + w.control * s_ctrl + w.intent * s_intent
    return {
        "schema_version": "driveloop_task_utility.v0",
        "J": round(j, 6),
        "S_perc": round(s_perc, 6),
        "S_ctrl": round(s_ctrl, 6),
        "S_intent": round(s_intent, 6),
        "S_ctrl_source": s_ctrl_source,
        "weights": {"perception": w.perception, "control": w.control, "intent": w.intent},
        "claim_boundary": "Eq.(5) acceptance utility; defines loop acceptance only, not a semantic-success proof.",
    }
