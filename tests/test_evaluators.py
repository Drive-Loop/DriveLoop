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
