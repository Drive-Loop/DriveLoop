from __future__ import annotations

from driveloop.schema import DriveLoopRequest, Evaluation, Refinement


class RuleBasedRefiner:
    """Prompt refiner used before introducing an LLM/VLM refiner."""

    ALIGNMENT_REASON_PREFIX = "alignment_check_failed:"

    def refine(self, request: DriveLoopRequest, evaluation: Evaluation) -> Refinement:
        prompt = request.prompt.strip()
        additions: list[str] = []
        notes = list(evaluation.diagnosis.reasons)

        for action in evaluation.diagnosis.suggested_actions:
            if action == "add realistic autonomous driving scene wording":
                additions.append("realistic autonomous driving scene")
            elif action == "specify weather or lighting":
                additions.append("daytime clear weather")
            elif action == "add explicit traffic actor or maneuver":
                additions.append("surrounded by vehicles with a safe lane-change interaction")

        alignment_additions = self._alignment_prompt_additions(evaluation)
        additions.extend(alignment_additions)

        if (
            "video_alignment_not_measured" not in evaluation.diagnosis.reasons
            and "panoramic" not in prompt.lower()
            and "multi-view" not in prompt.lower()
        ):
            additions.append("panoramic multi-view video")

        if "video_alignment_not_measured" in evaluation.diagnosis.reasons:
            notes.append("run prompt-video alignment review before claiming semantic success")

        if additions:
            prompt = prompt.rstrip(".") + ", " + ", ".join(dict.fromkeys(additions)) + "."

        return Refinement(
            prompt=prompt,
            condition=dict(request.condition),
            notes=list(dict.fromkeys(notes)),
        )

    def _alignment_prompt_additions(self, evaluation: Evaluation) -> list[str]:
        additions: list[str] = []
        for reason in evaluation.diagnosis.reasons:
            if not reason.startswith(self.ALIGNMENT_REASON_PREFIX):
                continue

            check_name = reason[len(self.ALIGNMENT_REASON_PREFIX):]
            if check_name == "object_presence.motorcycle":
                additions.append("a motorcycle must be visibly present")
            elif check_name == "spatial_relation.left_lane_change":
                additions.append("the motorcycle performs a visible lane change from the left")
            elif check_name == "lighting.daytime":
                additions.append("clear daytime lighting")
            elif check_name == "scene_type.urban_road":
                additions.append("urban road scene")

        return additions
