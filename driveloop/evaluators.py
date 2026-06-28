from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from driveloop.schema import Diagnosis, Evaluation, Generation


class BaseEvaluator(ABC):
    """Interface for generation evaluators.

    Future implementations can use perception models, tracking, VLM checks,
    rule-based safety constraints, or combinations of these signals.
    """

    @abstractmethod
    def evaluate(self, generation: Generation) -> Evaluation:
        raise NotImplementedError


class RuleBasedEvaluator(BaseEvaluator):
    """Simple first-pass evaluator.

    This is intentionally lightweight: it lets DriveLoop run end-to-end before
    plugging in YOLO, tracker, CLIP, VLM, or other perception evaluators.
    """

    def evaluate(self, generation: Generation) -> Evaluation:
        prompt = generation.prompt.lower()
        metrics: Dict[str, float] = {}

        coverage = 0.45
        if "realistic" in prompt:
            coverage += 0.15
        if any(word in prompt for word in ("rain", "rainy", "night", "fog", "snow", "daytime", "clear")):
            coverage += 0.1
        if any(word in prompt for word in ("pedestrian", "bus", "truck", "car", "vehicle", "vehicles", "cut in", "lane change", "lane-change")):
            coverage += 0.15
        if any(word in prompt for word in ("multi-view", "panoramic", "six camera")):
            coverage += 0.1

        score = min(1.0, coverage)
        metrics["prompt_coverage"] = score

        reasons: List[str] = []
        actions: List[str] = []
        if "realistic" not in prompt:
            reasons.append("prompt_missing_realism")
            actions.append("add realistic autonomous driving scene wording")
        if not any(word in prompt for word in ("rain", "rainy", "night", "fog", "snow", "daytime")):
            reasons.append("weather_or_lighting_unspecified")
            actions.append("specify weather or lighting")
        if not any(word in prompt for word in ("pedestrian", "bus", "truck", "car", "vehicle", "cut in", "lane change")):
            reasons.append("traffic_actor_unspecified")
            actions.append("add explicit traffic actor or maneuver")

        if generation.metadata.get("backend") == "drivedreamer2":
            tensor_ready = generation.metadata.get("dd2_tensor_control_ready")
            structural_level = generation.metadata.get("dd2_structural_control_level")
            metrics["dd2_tensor_control_ready"] = 1.0 if tensor_ready is True else 0.0
            if tensor_ready is not True:
                score = min(score, 0.79)
                reasons.append("dd2_tensor_control_not_ready")
                actions.append("connect actor, trajectory, and HDMap tensor-level structural overrides")
            if structural_level in (None, "plan_only", "schema_only"):
                reasons.append("dd2_structural_control_plan_only")
                actions.append("do not treat DD2 mini baseline structural inputs as prompt-aligned generation")

        passed = score >= 0.8
        return Evaluation(
            score=score,
            metrics=metrics,
            diagnosis=Diagnosis(
                passed=passed,
                reasons=reasons,
                suggested_actions=actions,
            ),
        )


class CompositeEvaluator(BaseEvaluator):
    """Combine multiple evaluators into one DriveLoop score."""

    def __init__(self, evaluators: List[BaseEvaluator]) -> None:
        if not evaluators:
            raise ValueError("CompositeEvaluator requires at least one evaluator")
        self.evaluators = evaluators

    def evaluate(self, generation: Generation) -> Evaluation:
        evaluations = [evaluator.evaluate(generation) for evaluator in self.evaluators]
        score = sum(evaluation.score for evaluation in evaluations) / len(evaluations)

        metrics: Dict[str, float] = {}
        reasons: List[str] = []
        actions: List[str] = []
        passed = True

        for idx, evaluation in enumerate(evaluations):
            prefix = evaluation.__class__.__name__
            for key, value in evaluation.metrics.items():
                metrics[f"{idx}_{prefix}_{key}"] = value
            reasons.extend(evaluation.diagnosis.reasons)
            actions.extend(evaluation.diagnosis.suggested_actions)
            passed = passed and evaluation.diagnosis.passed

        metrics["composite_score"] = score

        return Evaluation(
            score=score,
            metrics=metrics,
            diagnosis=Diagnosis(
                passed=passed,
                reasons=list(dict.fromkeys(reasons)),
                suggested_actions=list(dict.fromkeys(actions)),
            ),
        )


class PerceptionRuleEvaluator(BaseEvaluator):
    """Placeholder evaluator for future perception and rule checks.

    It reads DriveLoop metadata and artifact availability now. Later this class
    can run object detection, tracking, collision checks, weather/visibility
    checks, and temporal consistency metrics on generated videos.
    """

    def evaluate(self, generation: Generation) -> Evaluation:
        metrics: Dict[str, float] = {}
        reasons: List[str] = []
        actions: List[str] = []

        has_video = "video" in generation.artifacts or "mock_video" in generation.artifacts
        metrics["artifact_available"] = 1.0 if has_video else 0.0

        dd2_condition = generation.metadata.get("dd2_condition", {})
        actors = dd2_condition.get("actors", []) if isinstance(dd2_condition, dict) else []
        motion_primitives = dd2_condition.get("motion_primitives", []) if isinstance(dd2_condition, dict) else []
        long_tail_tags = dd2_condition.get("long_tail_tags", []) if isinstance(dd2_condition, dict) else []

        metrics["condition_actor_count"] = float(len(actors))
        metrics["condition_motion_count"] = float(len(motion_primitives))
        metrics["condition_long_tail_count"] = float(len(long_tail_tags))

        if not has_video:
            reasons.append("missing_generation_artifact")
            actions.append("rerun generation backend")

        score = metrics["artifact_available"]
        passed = has_video

        return Evaluation(
            score=score,
            metrics=metrics,
            diagnosis=Diagnosis(
                passed=passed,
                reasons=reasons,
                suggested_actions=actions,
            ),
        )
