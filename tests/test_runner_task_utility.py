from driveloop.backends.mock import MockGenerationBackend
from driveloop.evaluators import BaseEvaluator
from driveloop.runner import DriveLoopRunner
from driveloop.schema import Diagnosis, DriveLoopConfig, DriveLoopRequest, Evaluation


class FixedScoreEvaluator(BaseEvaluator):
    def __init__(self, score: float) -> None:
        self.score = score

    def evaluate(self, generation) -> Evaluation:
        return Evaluation(self.score, {}, Diagnosis(False, ["low_detection_coverage"], []))


REQUEST = DriveLoopRequest(prompt="at night a motorcycle cuts in from the left lane")


def _runner(tmp_path, **config_kwargs):
    config = DriveLoopConfig(max_iterations=2, output_dir=tmp_path, **config_kwargs)
    return DriveLoopRunner(
        backend=MockGenerationBackend(output_dir=tmp_path / "mock"),
        evaluator=FixedScoreEvaluator(0.468199),
        config=config,
    )


def test_utility_disabled_by_default(tmp_path):
    result = _runner(tmp_path).run(REQUEST)
    assert result.best_evaluation.score == 0.468199
    assert "J" not in result.best_evaluation.metrics


def test_utility_enabled_replaces_acceptance_score(tmp_path):
    result = _runner(tmp_path, use_task_utility=True).run(REQUEST)
    metrics = result.best_evaluation.metrics
    for key in ("J", "S_perc", "S_ctrl", "S_intent"):
        assert key in metrics
    assert metrics["S_perc"] == 0.468199
    assert result.best_evaluation.score == metrics["J"]


def test_utility_weights_override(tmp_path):
    result = _runner(
        tmp_path,
        use_task_utility=True,
        utility_weights={"perception": 1.0, "control": 0.0, "intent": 0.0},
    ).run(REQUEST)
    metrics = result.best_evaluation.metrics
    assert abs(metrics["J"] - metrics["S_perc"]) < 1e-9


def test_utility_acceptance_can_stop_loop(tmp_path):
    config = DriveLoopConfig(
        max_iterations=3, output_dir=tmp_path, target_score=0.1, use_task_utility=True
    )
    runner = DriveLoopRunner(
        backend=MockGenerationBackend(output_dir=tmp_path / "mock"),
        evaluator=FixedScoreEvaluator(0.9),
        config=config,
    )
    result = runner.run(REQUEST)
    assert len(result.attempt_history) == 1
