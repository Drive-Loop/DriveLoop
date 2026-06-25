from __future__ import annotations

from driveloop.schema import Diagnosis, Evaluation, Generation


class RuleBasedEvaluator:
    """Simple first-pass evaluator.

    This is intentionally lightweight: it lets DriveLoop run end-to-end before
    plugging in YOLO, tracker, CLIP, VLM, or other perception evaluators.
    """

    def evaluate(self, generation: Generation) -> Evaluation:
        prompt = generation.prompt.lower()
        metrics: dict[str, float] = {}

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

        reasons = []
        actions = []
        if "realistic" not in prompt:
            reasons.append("prompt_missing_realism")
            actions.append("add realistic autonomous driving scene wording")
        if not any(word in prompt for word in ("rain", "rainy", "night", "fog", "snow", "daytime")):
            reasons.append("weather_or_lighting_unspecified")
            actions.append("specify weather or lighting")
        if not any(word in prompt for word in ("pedestrian", "bus", "truck", "car", "vehicle", "cut in", "lane change")):
            reasons.append("traffic_actor_unspecified")
            actions.append("add explicit traffic actor or maneuver")

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
