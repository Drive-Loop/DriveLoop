from driveloop.evaluators import PerceptionRuleEvaluator
from driveloop.schema import Generation


def test_perception_rule_evaluator_reads_artifact_and_condition_metadata():
    generation = Generation(
        iteration=0,
        prompt="rainy night scene",
        artifacts={"video": "outputs/example.mp4"},
        metadata={
            "dd2_condition": {
                "actors": [{"category": "car", "attributes": {}}],
                "motion_primitives": ["cut_in"],
                "long_tail_tags": ["heavy_rain"],
            }
        },
    )

    evaluation = PerceptionRuleEvaluator().evaluate(generation)

    assert evaluation.score == 1.0
    assert evaluation.diagnosis.passed is True
    assert evaluation.metrics["artifact_available"] == 1.0
    assert evaluation.metrics["condition_actor_count"] == 1.0
    assert evaluation.metrics["condition_motion_count"] == 1.0
    assert evaluation.metrics["condition_long_tail_count"] == 1.0


def test_perception_rule_evaluator_fails_without_artifact():
    generation = Generation(iteration=0, prompt="rainy night scene")

    evaluation = PerceptionRuleEvaluator().evaluate(generation)

    assert evaluation.score == 0.0
    assert evaluation.diagnosis.passed is False
    assert "missing_generation_artifact" in evaluation.diagnosis.reasons
    assert "rerun generation backend" in evaluation.diagnosis.suggested_actions
