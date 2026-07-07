from __future__ import annotations

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
        "the motorcycle rides in the left adjacent lane very close to the ego vehicle, large in the frame",
        "close range view of the motorcycle with its headlight on, occupying a prominent part of the front-left camera view",
        "the motorcycle is centered, sharp and high contrast against the road at close distance",
    ]

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
        perception_additions = self._perception_prompt_additions(evaluation)
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
            for escalation in self.PERCEPTION_ESCALATION:
                if escalation.lower() not in prompt.lower():
                    additions.append(escalation)
                    notes.append("perception_escalation_applied")
                    break
        if additions:
            prompt = prompt.rstrip(".") + ", " + ", ".join(additions) + "."

        condition = dict(request.condition)

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

        if self.STRUCTURAL_ESCALATION_ENABLED and (
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
            if level >= 2:
                condition["source_rebinding"] = {
                    "candidate_offset": level - 1,
                    "reason": "structural_escalation_insufficient",
                    "claim_boundary": "source window shifted; token match refers to offset-zero window",
                }
                notes.append("source_rebinding_offset_%d" % (level - 1))

        return Refinement(
            prompt=prompt,
            condition=condition,
            notes=list(dict.fromkeys(notes)),
        )

    def _alignment_prompt_additions(self, evaluation: Evaluation) -> list[str]:
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
                additions.append("the same target motorcycle remains trackable across frames")
            elif "cut_in" in normalized or "cut-in" in normalized:
                additions.append("the motorcycle visibly cuts in from the left toward the ego path")
            elif check_name == "spatial_relation.left_lane_change":
                additions.append("the motorcycle performs a visible lane change from the left")
            elif "spatial_relation" in normalized:
                additions.append("the target starts in the left or adjacent lane and moves toward the ego path")
            elif "lateral_displacement" in normalized:
                additions.append("the target motorcycle shows measurable lateral displacement over time")
            elif "hdmap_alignment" in normalized:
                additions.append("visible lane geometry stays consistent with the intended cut-in path")
            elif check_name == "lighting.daytime":
                additions.append("clear daytime lighting")
            elif check_name == "scene_type.urban_road":
                additions.append("urban road scene")

        return additions

    def _perception_prompt_additions(self, evaluation: Evaluation) -> list[str]:
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
                "the target motorcycle is clearly moving, with visible lateral displacement across the frames, not parked and not stationary"
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
