from driveloop.backends.mock import MockGenerationBackend
from driveloop.evaluators import BaseEvaluator
from driveloop.refiner import RuleBasedRefiner
from driveloop.runner import DriveLoopRunner
from driveloop.schema import Diagnosis, DriveLoopConfig, DriveLoopRequest, Evaluation, Refinement


class AlwaysFailEvaluator(BaseEvaluator):
    def evaluate(self, generation) -> Evaluation:
        return Evaluation(0.1, {}, Diagnosis(False, ["target_object_not_detected"], []))


class DriftingRefiner(RuleBasedRefiner):
    """Rewrites the prompt and drops the original target object."""

    def refine(self, request, evaluation) -> Refinement:
        return Refinement(prompt="a car drives on an empty highway", condition={}, notes=[])


REQUEST = DriveLoopRequest(prompt="at night a motorcycle cuts in from the left lane")


def _config(tmp_path):
    return DriveLoopConfig(max_iterations=2, output_dir=tmp_path, use_task_utility=True)


def test_guard_reverts_intent_dropping_rewrite(tmp_path):
    runner = DriveLoopRunner(
        backend=MockGenerationBackend(output_dir=tmp_path / "mock"),
        evaluator=AlwaysFailEvaluator(),
        refiner=DriftingRefiner(),
        config=_config(tmp_path),
    )
    result = runner.run(REQUEST)
    first = result.attempt_history[0]
    assert first.refinement is not None
    assert any("intent_guard_reverted_prompt" in n for n in first.refinement.notes)
    assert first.refinement.prompt == REQUEST.prompt
    # the second attempt keeps the original prompt
    assert result.attempt_history[1].request.prompt == REQUEST.prompt


def test_guard_allows_additive_refinement(tmp_path):
    runner = DriveLoopRunner(
        backend=MockGenerationBackend(output_dir=tmp_path / "mock"),
        evaluator=AlwaysFailEvaluator(),
        config=_config(tmp_path),
    )
    result = runner.run(REQUEST)
    first = result.attempt_history[0]
    assert first.refinement is not None
    assert not any("intent_guard" in n for n in first.refinement.notes)
    assert first.refinement.prompt != REQUEST.prompt
