from driveloop.evaluators import CompositeEvaluator, RuleBasedEvaluator
from driveloop.schema import Generation


def test_composite_evaluator_combines_rule_based_metrics():
    generation = Generation(
        iteration=0,
        prompt="realistic rainy scene with a car, panoramic multi-view video",
    )

    evaluation = CompositeEvaluator([RuleBasedEvaluator(), RuleBasedEvaluator()]).evaluate(generation)

    assert evaluation.score == 0.95
    assert evaluation.metrics["composite_score"] == 0.95
    assert evaluation.diagnosis.passed is True


def test_rule_based_evaluator_rejects_dd2_when_tensor_control_is_not_ready():
    generation = Generation(
        iteration=0,
        prompt="realistic snowy scene with vehicles, panoramic multi-view video",
        artifacts={"video": "dummy.mp4"},
        metadata={
            "backend": "drivedreamer2",
            "dd2_tensor_control_ready": False,
            "dd2_structural_control_level": "plan_only",
        },
    )

    evaluation = RuleBasedEvaluator().evaluate(generation)

    assert evaluation.score < 0.8
    assert evaluation.diagnosis.passed is False
    assert "dd2_tensor_control_not_ready" in evaluation.diagnosis.reasons
    assert "dd2_structural_control_plan_only" in evaluation.diagnosis.reasons
