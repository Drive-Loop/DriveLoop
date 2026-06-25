from __future__ import annotations

from driveloop.schema import DriveLoopRequest, Evaluation, Refinement


class RuleBasedRefiner:
    """Prompt refiner used before introducing an LLM/VLM refiner."""

    def refine(self, request: DriveLoopRequest, evaluation: Evaluation) -> Refinement:
        prompt = request.prompt.strip()
        additions: list[str] = []

        for action in evaluation.diagnosis.suggested_actions:
            if action == "add realistic autonomous driving scene wording":
                additions.append("realistic autonomous driving scene")
            elif action == "specify weather or lighting":
                additions.append("daytime clear weather")
            elif action == "add explicit traffic actor or maneuver":
                additions.append("surrounded by vehicles with a safe lane-change interaction")

        if "panoramic" not in prompt.lower() and "multi-view" not in prompt.lower():
            additions.append("panoramic multi-view video")

        if additions:
            prompt = prompt.rstrip(".") + ", " + ", ".join(dict.fromkeys(additions)) + "."

        return Refinement(
            prompt=prompt,
            condition=dict(request.condition),
            notes=evaluation.diagnosis.reasons,
        )
