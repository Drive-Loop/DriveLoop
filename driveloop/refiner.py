from __future__ import annotations

import os

from driveloop.schema import DriveLoopRequest, Evaluation, Refinement


class RuleBasedRefiner:
    """Diagnosis-driven refiner used before introducing an LLM/VLM refiner."""

    ALIGNMENT_REASON_PREFIX = "alignment_check_failed:"

    PERCEPTION_REASONS = {
        "target_object_not_detected",
        "low_detection_coverage",
        "low_detector_confidence",
        "unstable_track_coverage",
        "identity_inconsistent",
        "unstable_bounding_boxes",
        "target_appears_static",
    }
    STRUCTURAL_ESCALATION_ENABLED = True

    PERCEPTION_ESCALATION = [
        "the {category} travels in the left adjacent lane very close to the ego vehicle, large in the frame",
        "close range view of the {category}, occupying a prominent part of the front-left camera view",
        "the {category} is centered, sharp and high contrast against the road at close distance",
    ]

    SMALL_ACTOR_CATEGORIES = {"motorcycle", "bicycle", "pedestrian"}
    SYNTHETIC_CLOSE_RANGE_M = 9.0

    KNOWN_CATEGORIES = [
        "motorcycle",
        "pedestrian",
        "bicycle",
        "truck",
        "bus",
        "car",
    ]

    def _requested_category(self, prompt: str) -> str:
        """First known category mentioned in the prompt; the escalation
        templates must never change the requested object class (the
        2026-07-21 motorcycle-template leak hijacked the target actor
        and silently disabled real-track injection)."""
        text = prompt.lower()
        found = [(text.find(cat), cat) for cat in self.KNOWN_CATEGORIES if cat in text]
        return min(found)[1] if found else "target vehicle"

    SOURCE_REASONS = {
        "source_selection_unavailable",
        "source_binding_unavailable",
        "no_dd2_candidate_contains_requested_source_tokens",
        "dd2_labels_data_missing",
    }
    RUNTIME_REASONS = {
        "dd2_tensor_control_not_ready",
        "dd2_structural_control_plan_only",
        "trajectory_tensor_control_not_connected",
        "trajectory_control",
        "boxes3d",
        "image_box",
        "image_hdmap",
    }

    def refine(self, request: DriveLoopRequest, evaluation: Evaluation) -> Refinement:
        prompt = request.prompt.strip()
        category = self._requested_category(prompt)
        additions: list[str] = []
        notes = list(evaluation.diagnosis.reasons)

        for action in evaluation.diagnosis.suggested_actions:
            if action == "add realistic autonomous driving scene wording":
                additions.append("realistic autonomous driving scene")
            elif action == "specify weather or lighting":
                additions.append("daytime clear weather")
            elif action == "add explicit traffic actor or maneuver":
                additions.append("surrounded by vehicles with a safe lane-change interaction")

        alignment_additions = self._alignment_prompt_additions(evaluation, category)
        perception_additions = self._perception_prompt_additions(evaluation, category)
        additions.extend(alignment_additions)
        additions.extend(perception_additions)

        if (
            "video_alignment_not_measured" not in evaluation.diagnosis.reasons
            and "panoramic" not in prompt.lower()
            and "multi-view" not in prompt.lower()
        ):
            additions.append("panoramic multi-view video")

        if "video_alignment_not_measured" in evaluation.diagnosis.reasons:
            notes.append("run prompt-video alignment review before claiming semantic success")
        if self._source_reasons(evaluation):
            notes.append("select or rebuild a source candidate before retrying generation")
        if self._runtime_reasons(evaluation):
            notes.append("runtime controls are unavailable; do not treat another retry as semantic success")

        additions = [a for a in dict.fromkeys(additions) if a.lower() not in prompt.lower()]
        if not additions and (self.PERCEPTION_REASONS & set(evaluation.diagnosis.reasons)):
            for template in self.PERCEPTION_ESCALATION:
                escalation = template.format(category=category)
                if escalation.lower() not in prompt.lower():
                    additions.append(escalation)
                    notes.append("perception_escalation_applied")
                    break
        if additions:
            prompt = prompt.rstrip(".") + ", " + ", ".join(additions) + "."

        condition = dict(request.condition)
        condition.setdefault("driveloop_original_prompt", request.prompt.strip())

        alignment_feedback = self._alignment_feedback(evaluation, alignment_additions)
        if alignment_feedback:
            condition["alignment_feedback"] = alignment_feedback

        perception_feedback = self._perception_feedback(evaluation, perception_additions)
        if perception_feedback:
            condition["perception_feedback"] = perception_feedback

        source_feedback = self._source_selection_feedback(evaluation)
        if source_feedback:
            condition["source_selection_feedback"] = source_feedback

        runtime_feedback = self._runtime_control_feedback(evaluation)
        if runtime_feedback:
            condition["runtime_control_feedback"] = runtime_feedback

        if (self.STRUCTURAL_ESCALATION_ENABLED
                and os.environ.get("DRIVELOOP_TEXT_ONLY_REFINER") != "1") and (
            {"target_object_not_detected", "low_detection_coverage", "target_appears_static"}
            & set(evaluation.diagnosis.reasons)
        ):
            prior = request.condition.get("structural_escalation")
            level = int(prior.get("level", 0)) + 1 if isinstance(prior, dict) else 1
            condition["structural_escalation"] = {
                "level": level,
                # Position is side-calibrated (geometry sweeps 2026-07-07):
                # do not move the actor. Escalate rendering strength to the
                # measured sweet spot (size 1.5; both 1.25 and 1.75 gave
                # Q_cov 0.125 vs 0.375 at 1.5 in the left-side size probe).
                "proximity_scale": 1.0,
                "size_scale": 1.5,
                "reason": "perception_target_failure",
                "claim_boundary": "structured-condition escalation; not proof of visual realization",
            }
            notes.append("structural_escalation_level_%d" % level)
            # Generation-parameter escalation: the only refiner lever
            # measured to reach the conditioning under real-track ego
            # injection (v9 2026-07-09: prompt additions collapse to
            # canned strings; synthetic geometry is superseded).
            # Rung 2 (max_guidance_scale 7.0) was removed: at matched
            # seeds it regressed both cases that reached it (m3, m5
            # attempt 3 back to the 0.2 floor, 2026-07-09 seed-only
            # attribution). All levels use the measured-positive
            # steps-50 setting; per-attempt reseeding supplies the
            # remaining variation.
            generation_ladder = [
                {"num_inf_steps": 50},
            ]
            condition["generation_escalation"] = {
                **generation_ladder[min(level, len(generation_ladder)) - 1],
                "level": level,
                "claim_boundary": "generation-parameter escalation; not proof of visual realization",
            }
            notes.append("generation_escalation_level_%d" % level)
            if (level >= 2 and os.environ.get(
                    "DRIVELOOP_DISABLE_SYNTHETIC_RUNG") != "1"):
                condition["synthetic_trajectory_escalation"] = {
                    "level": level,
                    "reason": "real_track_reinforcement_undetected",
                    "claim_boundary": "deliberate synthetic close-range trajectory"
                    " conditioning for the requested category;"
                    " not proof of visual realization",
                }
                notes.append("synthetic_trajectory_escalation_level_%d" % level)
                # cr9 ablation 2026-07-21 (night motorcycle, 9 m synthetic):
                # the bare prompt recovers at 4/4 seeds
                # (0.650/0.395/0.332/0.143) while the additions-refined
                # prompt scores 0.000. Text amplification suppresses the
                # synthetic actor, so the synthetic rung reverts to the
                # original user prompt and relies on the structural
                # condition alone.
                prompt = condition.get("driveloop_original_prompt", prompt)
                notes.append("synthetic_rung_reverts_to_original_prompt")
                if category in self.SMALL_ACTOR_CATEGORIES:
                    # Distance sweep 2026-07-21: small actors under
                    # degraded conditions become detectable only at
                    # close range (night motorcycle 0 -> 0.650 at 9 m,
                    # dead at 15/20 m); large actors keep the side
                    # defaults (rain truck recovers at the default
                    # 20 m and dies at 9-15 m).
                    condition["structural_escalation"]["longitudinal_base_m"] = (
                        self.SYNTHETIC_CLOSE_RANGE_M
                    )
                    notes.append("synthetic_close_range_small_actor")

        return Refinement(
            prompt=prompt,
            condition=condition,
            notes=list(dict.fromkeys(notes)),
        )

    def _alignment_prompt_additions(
        self, evaluation: Evaluation, category: str = "target vehicle"
    ) -> list[str]:
        additions: list[str] = []
        for check_name in self._failed_alignment_checks(evaluation):
            normalized = check_name.lower()
            if check_name == "object_presence.motorcycle":
                additions.append("a motorcycle must be visibly present")
            elif (
                "object_presence" in normalized
                and ("motorcycle" in normalized or "scooter" in normalized)
            ):
                additions.append("a clearly visible motorcycle or scooter target remains large and unoccluded")
            elif "object_consistency" in normalized or "trackable" in normalized:
                additions.append("the same target %s remains trackable across frames" % category)
            elif "cut_in" in normalized or "cut-in" in normalized:
                additions.append("the %s visibly cuts in from the left toward the ego path" % category)
            elif check_name == "spatial_relation.left_lane_change":
                additions.append("the %s performs a visible lane change from the left" % category)
            elif "spatial_relation" in normalized:
                additions.append("the target starts in the left or adjacent lane and moves toward the ego path")
            elif "lateral_displacement" in normalized:
                additions.append("the target %s shows measurable lateral displacement over time" % category)
            elif "hdmap_alignment" in normalized:
                additions.append("visible lane geometry stays consistent with the intended cut-in path")
            elif check_name == "lighting.daytime":
                additions.append("clear daytime lighting")
            elif check_name == "scene_type.urban_road":
                additions.append("urban road scene")

        return additions

    def _perception_prompt_additions(
        self, evaluation: Evaluation, category: str = "target vehicle"
    ) -> list[str]:
        reasons = set(evaluation.diagnosis.reasons)
        additions: list[str] = []
        if {"target_object_not_detected", "low_detection_coverage"} & reasons:
            additions.append("the target actor remains large, visible, and unoccluded across the sequence")
        if "low_detector_confidence" in reasons:
            additions.append("clear lighting and high contrast around the target actor")
        if "unstable_track_coverage" in reasons:
            additions.append("the target actor maintains continuous motion without occlusion across frames")
        if "identity_inconsistent" in reasons:
            additions.append("the same target actor identity is preserved throughout the video")
        if "unstable_bounding_boxes" in reasons:
            additions.append("the target actor has stable scale and position changes across frames")
        if "target_appears_static" in reasons:
            additions.append(
                "the target %s is clearly moving, with visible lateral"
                " displacement across the frames, not parked and not"
                " stationary" % category
            )
        return additions

    def _alignment_feedback(
        self,
        evaluation: Evaluation,
        requested_visual_constraints: list[str],
    ) -> dict[str, object]:
        failed_checks = self._failed_alignment_checks(evaluation)
        not_measured = "video_alignment_not_measured" in evaluation.diagnosis.reasons

        if not failed_checks and not not_measured:
            return {}

        return {
            "schema_version": "driveloop_alignment_feedback.v0",
            "status": "not_measured" if not_measured else "measured_failed",
            "control_level": "text_feedback_only",
            "failed_checks": failed_checks,
            "requested_visual_constraints": list(dict.fromkeys(requested_visual_constraints)),
            "diagnosis_reasons": list(evaluation.diagnosis.reasons),
            "claim_boundary": (
                "Alignment feedback can refine prompt text, but it is not verified "
                "tensor-level DD2 control and does not prove video semantic correction."
            ),
        }

    def _perception_feedback(
        self,
        evaluation: Evaluation,
        requested_visual_constraints: list[str],
    ) -> dict[str, object]:
        failed_reasons = self._perception_reasons(evaluation)
        if not failed_reasons:
            return {}

        return {
            "schema_version": "driveloop_perception_feedback.v0",
            "status": "measured_failed",
            "control_level": "text_and_condition_feedback",
            "failed_checks": failed_reasons,
            "requested_visual_constraints": list(dict.fromkeys(requested_visual_constraints)),
            "diagnosis_reasons": list(evaluation.diagnosis.reasons),
            "suggested_actions": list(dict.fromkeys(evaluation.diagnosis.suggested_actions)),
            "claim_boundary": (
                "Perception feedback can guide the next attempt, but detector/tracker "
                "metrics alone do not prove full prompt-video semantic success."
            ),
        }

    def _source_selection_feedback(self, evaluation: Evaluation) -> dict[str, object]:
        failed_reasons = self._source_reasons(evaluation)
        if not failed_reasons:
            return {}

        return {
            "schema_version": "driveloop_source_selection_feedback.v0",
            "status": "source_unavailable",
            "control_level": "source_selector_feedback_only",
            "failed_reasons": failed_reasons,
            "suggested_actions": list(dict.fromkeys(evaluation.diagnosis.suggested_actions)),
            "policy": "select_alternate_source_or_rebuild_runtime_dataset_before_generation_retry",
            "claim_boundary": (
                "Source selection feedback is not GPU approval and does not prove video semantic success."
            ),
        }

    def _runtime_control_feedback(self, evaluation: Evaluation) -> dict[str, object]:
        failed_reasons = self._runtime_reasons(evaluation)
        if not failed_reasons:
            return {}

        return {
            "schema_version": "driveloop_runtime_control_feedback.v0",
            "status": "runtime_control_unavailable",
            "control_level": "unsupported_runtime_surface_feedback",
            "failed_reasons": failed_reasons,
            "suggested_actions": list(dict.fromkeys(evaluation.diagnosis.suggested_actions)),
            "claim_boundary": (
                "Runtime control feedback records unsupported DD2 control surfaces; "
                "it must not be treated as verified trajectory or semantic control."
            ),
        }

    def _failed_alignment_checks(self, evaluation: Evaluation) -> list[str]:
        checks: list[str] = []
        for reason in evaluation.diagnosis.reasons:
            if reason.startswith(self.ALIGNMENT_REASON_PREFIX):
                checks.append(reason[len(self.ALIGNMENT_REASON_PREFIX):])
        return checks

    def _perception_reasons(self, evaluation: Evaluation) -> list[str]:
        return [
            reason
            for reason in evaluation.diagnosis.reasons
            if reason in self.PERCEPTION_REASONS
        ]

    def _source_reasons(self, evaluation: Evaluation) -> list[str]:
        return [
            reason
            for reason in evaluation.diagnosis.reasons
            if reason in self.SOURCE_REASONS
        ]

    def _runtime_reasons(self, evaluation: Evaluation) -> list[str]:
        return [
            reason
            for reason in evaluation.diagnosis.reasons
            if reason in self.RUNTIME_REASONS or reason.startswith("unsupported_control:")
        ]
