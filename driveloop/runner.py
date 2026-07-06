from __future__ import annotations

from dataclasses import asdict, replace
from typing import Optional

from driveloop.backends.base import GenerationBackend
from driveloop.condition_adapter import DriveDreamer2ConditionAdapter
from driveloop.evaluator import BaseEvaluator, RuleBasedEvaluator
from driveloop.grounding import RuleBasedGrounder
from driveloop.logging import HistoryLogger
from driveloop.longtail import LongTailController, control_coverage
from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import (
    DriveLoopAttempt,
    Diagnosis,
    DriveLoopConfig,
    DriveLoopRequest,
    DriveLoopResult,
    Evaluation,
    Generation,
    Refinement,
)
from driveloop.source_selector import BaseSourceSelector, NoOpSourceSelector
from driveloop.utility import UtilityWeights, task_utility


class DriveLoopRunner:
    def __init__(
        self,
        backend: GenerationBackend,
        evaluator: Optional[BaseEvaluator] = None,
        refiner: Optional[RuleBasedRefiner] = None,
        grounder: Optional[RuleBasedGrounder] = None,
        longtail_controller: Optional[LongTailController] = None,
        condition_adapter: Optional[DriveDreamer2ConditionAdapter] = None,
        source_selector: Optional[BaseSourceSelector] = None,
        config: Optional[DriveLoopConfig] = None,
    ) -> None:
        self.backend = backend
        self.evaluator = evaluator or RuleBasedEvaluator()
        self.refiner = refiner or RuleBasedRefiner()
        self.grounder = grounder or RuleBasedGrounder()
        self.longtail_controller = longtail_controller or LongTailController()
        self.condition_adapter = condition_adapter or DriveDreamer2ConditionAdapter()
        self.source_selector = source_selector or NoOpSourceSelector()
        self.config = config or DriveLoopConfig()
        self.history_logger = HistoryLogger(self.config.output_dir)

    def run(self, request: DriveLoopRequest) -> DriveLoopResult:
        current_request = request
        original_spec = self.grounder.ground(request)
        history: list[tuple[Generation, Evaluation]] = []
        attempt_history: list[DriveLoopAttempt] = []
        best_generation: Optional[Generation] = None
        best_evaluation: Optional[Evaluation] = None

        for iteration in range(self.config.max_iterations):
            scene_spec = self.grounder.ground(current_request)
            requested_tags = current_request.condition.get("long_tail_tags", [])
            condition_plan = self.longtail_controller.build(
                scene_spec,
                requested_tags=requested_tags,
                history=history,
            )
            coverage = control_coverage(condition_plan)
            dd2_condition = self.condition_adapter.build(
                scene_spec,
                condition_plan,
                alignment_feedback=current_request.condition.get("alignment_feedback"),
            )
            source_selection = self.source_selector.select(current_request, scene_spec, condition_plan)
            source_selection_dict = asdict(source_selection)
            dd2_condition_dict = asdict(dd2_condition)
            generation_request = self._with_conditioned_prompt(current_request, condition_plan.prompt_suffixes)
            generation_request = replace(
                generation_request,
                condition={
                    **generation_request.condition,
                    "dd2_condition": dd2_condition_dict,
                },
                metadata={
                    **generation_request.metadata,
                    "source_selection": source_selection_dict,
                    **source_selection.backend_hints,
                },
            )
            generation = self.backend.generate(generation_request, iteration)
            perception_metadata = self._perception_metadata_from_request(current_request.metadata)
            generation = replace(
                generation,
                metadata={
                    **generation.metadata,
                    **perception_metadata,
                    "source_selection": source_selection_dict,
                    "scene_specification": asdict(scene_spec),
                    "long_tail_condition_plan": asdict(condition_plan),
                    "control_coverage": coverage,
                    "dd2_condition": dd2_condition_dict,
                },
            )

            evaluation = self.evaluator.evaluate(generation)
            evaluation = self._with_source_selection_diagnosis(evaluation, source_selection_dict)
            if self.config.use_task_utility:
                utility_weights = (
                    UtilityWeights(**self.config.utility_weights)
                    if self.config.utility_weights
                    else None
                )
                utility = task_utility(
                    evaluation.score,
                    condition_plan,
                    original_spec,
                    scene_spec,
                    alignment_score=evaluation.metrics.get("alignment_score"),
                    weights=utility_weights,
                )
                evaluation = replace(
                    evaluation,
                    score=utility["J"],
                    metrics={
                        **evaluation.metrics,
                        "J": utility["J"],
                        "S_perc": utility["S_perc"],
                        "S_ctrl": utility["S_ctrl"],
                        "S_intent": utility["S_intent"],
                    },
                )
            history.append((generation, evaluation))

            if best_evaluation is None or evaluation.score > best_evaluation.score:
                best_generation = generation
                best_evaluation = evaluation

            source_selection_blocks_acceptance = (
                source_selection_dict.get("requested") is True
                and source_selection_dict.get("ready") is not True
            )
            should_stop = (
                not source_selection_blocks_acceptance
                and (evaluation.score >= self.config.target_score or evaluation.diagnosis.passed)
            )
            refinement: Optional[Refinement] = None
            if not should_stop:
                refinement = self.refiner.refine(current_request, evaluation)

            attempt = DriveLoopAttempt(
                iteration=iteration,
                request=current_request,
                scene_specification=scene_spec,
                long_tail_condition_plan=condition_plan,
                dd2_condition=dd2_condition_dict,
                condition_package=self._attempt_condition_package(dd2_condition_dict, generation),
                source_binding=self._source_binding_from_generation(generation),
                generation=generation,
                evaluation=evaluation,
                refinement=refinement,
                status=self._attempt_status(generation, evaluation, source_selection_dict),
                source_selection=source_selection_dict,
                claim_boundary=self._attempt_claim_boundary(generation, evaluation, source_selection_dict),
            )
            attempt_history.append(attempt)
            self.history_logger.write(generation, evaluation, attempt=attempt)

            if should_stop:
                break

            assert refinement is not None
            current_request = replace(
                current_request,
                prompt=refinement.prompt,
                condition=refinement.condition,
            )

        assert best_generation is not None
        assert best_evaluation is not None
        return DriveLoopResult(
            request=request,
            best_generation=best_generation,
            best_evaluation=best_evaluation,
            history=history,
            attempt_history=attempt_history,
        )

    def _with_source_selection_diagnosis(self, evaluation: Evaluation, source_selection: dict) -> Evaluation:
        if source_selection.get("requested") is not True or source_selection.get("ready") is True:
            return evaluation

        diagnosis = source_selection.get("diagnosis", {})
        if not isinstance(diagnosis, dict):
            diagnosis = {}
        binding = source_selection.get("binding", {})
        if not isinstance(binding, dict):
            binding = {}

        reasons = list(evaluation.diagnosis.reasons)
        reasons.append("source_selection_unavailable")
        for reason in (diagnosis.get("reason"), binding.get("reason")):
            if reason:
                reasons.append(str(reason))

        actions = list(evaluation.diagnosis.suggested_actions)
        suggested_actions = diagnosis.get("suggested_actions", [])
        if isinstance(suggested_actions, list):
            actions.extend(str(action) for action in suggested_actions)

        metrics = {
            **evaluation.metrics,
            "source_selection_requested": 1.0,
            "source_selection_ready": 0.0,
        }

        return replace(
            evaluation,
            score=0.0,
            metrics=metrics,
            diagnosis=Diagnosis(
                passed=False,
                reasons=list(dict.fromkeys(reasons)),
                suggested_actions=list(dict.fromkeys(actions)),
            ),
        )

    def _perception_metadata_from_request(self, metadata: dict) -> dict:
        config = metadata.get("perception_evaluation")
        if not isinstance(config, dict) or config.get("enabled") is not True:
            return {}

        payload = {"perception_evaluation": dict(config)}
        for source in (metadata, config):
            if not isinstance(source, dict):
                continue
            for key in (
                "perception_detections",
                "detections_by_frame",
                "video_detections",
                "target_labels",
                "frame_count",
            ):
                if key in source:
                    payload[key] = source[key]

        if "detections" in config and "perception_detections" not in payload:
            payload["perception_detections"] = config["detections"]
        return payload

    def _source_binding_from_generation(self, generation: Generation) -> dict:
        binding = generation.metadata.get("dd2_source_sample_binding", {})
        return dict(binding) if isinstance(binding, dict) else {}

    def _attempt_condition_package(self, dd2_condition: dict, generation: Generation) -> dict:
        executable = dd2_condition.get("executable_condition", {})
        if not isinstance(executable, dict):
            executable = {}
        structural_plan = executable.get("structural_input_plan", {})
        if not isinstance(structural_plan, dict):
            structural_plan = {}
        source_binding = self._source_binding_from_generation(generation)
        baseline_snapshot = generation.metadata.get("dd2_baseline_structural_snapshot", {})
        if not isinstance(baseline_snapshot, dict):
            baseline_snapshot = {}
        long_tail_tags = dd2_condition.get("long_tail_tags", [])
        motion_primitives = dd2_condition.get("motion_primitives", [])
        return {
            "schema_version": "driveloop_attempt_condition_package.v0",
            "target_backend": executable.get("target_backend"),
            "text_prompt": dd2_condition.get("text_prompt"),
            "long_tail_tags": list(long_tail_tags) if isinstance(long_tail_tags, list) else [],
            "motion_primitives": list(motion_primitives) if isinstance(motion_primitives, list) else [],
            "source_binding_requested": source_binding.get("requested"),
            "source_binding_ready": source_binding.get("ready"),
            "dd2_batch_skip": source_binding.get("dd2_batch_skip", generation.metadata.get("dd2_batch_skip")),
            "runtime_dataset_dir": source_binding.get("dataset_dir") or baseline_snapshot.get("dataset_dir"),
            "unsupported_controls": self._unsupported_controls(executable, structural_plan),
        }

    def _unsupported_controls(self, executable: dict, structural_plan: dict) -> list[str]:
        unsupported: list[str] = []
        trajectory = executable.get("trajectory_control_contract", {})
        if isinstance(trajectory, dict) and trajectory.get("status") == "not_runtime_connected":
            unsupported.append("trajectory_control")
        for name in ("boxes3d", "image_box", "image_hdmap"):
            control = structural_plan.get(name, {})
            if isinstance(control, dict) and control.get("override_ready") is False:
                unsupported.append(name)
        return list(dict.fromkeys(unsupported))

    def _attempt_status(self, generation: Generation, evaluation: Evaluation, source_selection: dict) -> str:
        if source_selection.get("requested") is True and source_selection.get("ready") is not True:
            return "source_selection_unavailable"
        source_binding = self._source_binding_from_generation(generation)
        if source_binding.get("requested") is True and source_binding.get("ready") is not True:
            return "source_binding_unavailable"
        if evaluation.score >= self.config.target_score or evaluation.diagnosis.passed:
            return "accepted"
        return "needs_refinement"

    def _attempt_claim_boundary(self, generation: Generation, evaluation: Evaluation, source_selection: dict) -> dict:
        source_binding = self._source_binding_from_generation(generation)
        source_claim = source_binding.get("claim_boundary", {}) if isinstance(source_binding, dict) else {}
        selection_claim = source_selection.get("claim_boundary", {}) if isinstance(source_selection, dict) else {}
        return {
            "attempt_record_is_not_video_semantic_success": True,
            "generation_artifact_is_not_semantic_success": True,
            "runtime_trace_is_not_semantic_success": True,
            "semantic_success_requires_measured_passed_alignment_eval": True,
            "source_binding_is_not_gpu_approval": source_claim.get("source_sample_binding_is_not_gpu_approval"),
            "source_selection_is_not_gpu_approval": selection_claim.get("source_selection_is_not_gpu_approval"),
            "evaluation_passed": evaluation.diagnosis.passed,
        }

    def _with_conditioned_prompt(
        self,
        request: DriveLoopRequest,
        prompt_suffixes: list[str],
    ) -> DriveLoopRequest:
        if not prompt_suffixes:
            return request
        suffix = ", ".join(prompt_suffixes)
        prompt = request.prompt.rstrip(".")
        if suffix.lower() in prompt.lower():
            return request
        return replace(request, prompt=f"{prompt}, {suffix}.")
