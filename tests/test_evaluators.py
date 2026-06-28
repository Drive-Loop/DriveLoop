from driveloop.evaluators import CompositeEvaluator, PromptVideoAlignmentEvaluator, RuleBasedEvaluator
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

def test_prompt_video_alignment_requires_external_measurement():
    generation = Generation(
        iteration=0,
        prompt="daytime urban road with a motorcycle changing lane from the left",
        artifacts={"video": "iteration_00.mp4"},
    )

    evaluation = PromptVideoAlignmentEvaluator().evaluate(generation)

    assert evaluation.score == 0.0
    assert evaluation.diagnosis.passed is False
    assert "video_alignment_not_measured" in evaluation.diagnosis.reasons
    assert evaluation.metrics["alignment_measured"] == 0.0


def test_prompt_video_alignment_scores_audited_report():
    generation = Generation(
        iteration=0,
        prompt="daytime urban road with a motorcycle changing lane from the left",
        artifacts={"video": "iteration_00.mp4"},
        metadata={
            "prompt_video_alignment": {
                "status": "measured",
                "source": "manual_review_v0",
                "checks": [
                    {"name": "object_presence.motorcycle", "required": True, "passed": True, "score": 0.9},
                    {"name": "spatial_relation.left_lane_change", "required": True, "passed": True, "score": 0.8},
                    {"name": "lighting.daytime", "required": True, "passed": True, "score": 0.85},
                ],
            }
        },
    )

    evaluation = PromptVideoAlignmentEvaluator().evaluate(generation)

    assert evaluation.score == 0.85
    assert evaluation.diagnosis.passed is True
    assert evaluation.metrics["alignment_measured"] == 1.0
    assert evaluation.metrics["alignment_required_check_count"] == 3.0
    assert evaluation.metrics["alignment_passed_required_check_count"] == 3.0


def test_prompt_video_alignment_fails_failed_required_check():
    generation = Generation(
        iteration=0,
        prompt="daytime urban road with a motorcycle changing lane from the left",
        artifacts={"video": "iteration_00.mp4"},
        metadata={
            "prompt_video_alignment": {
                "status": "measured",
                "source": "manual_review_v0",
                "checks": [
                    {"name": "object_presence.motorcycle", "required": True, "passed": False, "score": 0.2},
                    {"name": "lighting.daytime", "required": True, "passed": True, "score": 0.9},
                ],
            }
        },
    )

    evaluation = PromptVideoAlignmentEvaluator().evaluate(generation)

    assert evaluation.diagnosis.passed is False
    assert "alignment_check_failed:object_presence.motorcycle" in evaluation.diagnosis.reasons
