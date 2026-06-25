from __future__ import annotations

from dataclasses import asdict, replace
from typing import Optional

from driveloop.backends.base import GenerationBackend
from driveloop.evaluator import RuleBasedEvaluator
from driveloop.grounding import RuleBasedGrounder
from driveloop.logging import HistoryLogger
from driveloop.longtail import LongTailController
from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import DriveLoopConfig, DriveLoopRequest, DriveLoopResult, Evaluation, Generation


class DriveLoopRunner:
    def __init__(
        self,
        backend: GenerationBackend,
        evaluator: Optional[RuleBasedEvaluator] = None,
        refiner: Optional[RuleBasedRefiner] = None,
        grounder: Optional[RuleBasedGrounder] = None,
        longtail_controller: Optional[LongTailController] = None,
        config: Optional[DriveLoopConfig] = None,
    ) -> None:
        self.backend = backend
        self.evaluator = evaluator or RuleBasedEvaluator()
        self.refiner = refiner or RuleBasedRefiner()
        self.grounder = grounder or RuleBasedGrounder()
        self.longtail_controller = longtail_controller or LongTailController()
        self.config = config or DriveLoopConfig()
        self.history_logger = HistoryLogger(self.config.output_dir)

    def run(self, request: DriveLoopRequest) -> DriveLoopResult:
        current_request = request
        history: list[tuple[Generation, Evaluation]] = []
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
            generation_request = self._with_conditioned_prompt(current_request, condition_plan.prompt_suffixes)
            generation = self.backend.generate(generation_request, iteration)
            generation = replace(
                generation,
                metadata={
                    **generation.metadata,
                    "scene_specification": asdict(scene_spec),
                    "long_tail_condition_plan": asdict(condition_plan),
                },
            )

            evaluation = self.evaluator.evaluate(generation)
            history.append((generation, evaluation))
            self.history_logger.write(generation, evaluation)

            if best_evaluation is None or evaluation.score > best_evaluation.score:
                best_generation = generation
                best_evaluation = evaluation

            if evaluation.score >= self.config.target_score or evaluation.diagnosis.passed:
                break

            refinement = self.refiner.refine(current_request, evaluation)
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
        )

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
