from driveloop.grounding import RuleBasedGrounder
from driveloop.longtail import LongTailController
from driveloop.schema import DriveLoopRequest
from driveloop.utility import UtilityWeights, intent_consistency, task_utility


def _spec(prompt):
    return RuleBasedGrounder().ground(DriveLoopRequest(prompt=prompt))


def _plan(prompt, tags=None):
    spec = _spec(prompt)
    return LongTailController().build(spec, requested_tags=tags or [])


ORIGINAL = "at night a motorcycle cuts in from the left lane"


def test_weights_normalized():
    w = UtilityWeights(1.0, 1.0, 2.0).normalized()
    assert abs(w.perception + w.control + w.intent - 1.0) < 1e-9
    assert w.intent == 0.5


def test_intent_consistency_identity():
    assert intent_consistency(_spec(ORIGINAL), _spec(ORIGINAL)) == 1.0


def test_intent_consistency_penalizes_dropped_object():
    drifted = _spec("at night a car drives straight on the highway")
    assert intent_consistency(_spec(ORIGINAL), drifted) < 1.0


def test_refined_prompt_keeps_intent():
    refined = _spec(ORIGINAL + ", clearly visible, high contrast, the motorcycle remains trackable")
    assert intent_consistency(_spec(ORIGINAL), refined) == 1.0


def test_task_utility_uses_plan_coverage_when_alignment_missing():
    result = task_utility(0.5, _plan(ORIGINAL), _spec(ORIGINAL), _spec(ORIGINAL))
    assert result["S_ctrl_source"] == "control_coverage_plan"
    assert 0.0 <= result["J"] <= 1.0


def test_task_utility_prefers_measured_alignment():
    result = task_utility(0.5, _plan(ORIGINAL), _spec(ORIGINAL), _spec(ORIGINAL), alignment_score=0.361)
    assert result["S_ctrl_source"] == "measured_alignment"
    assert result["S_ctrl"] == 0.361


def test_task_utility_reports_components():
    result = task_utility(0.468199, _plan(ORIGINAL), _spec(ORIGINAL), _spec(ORIGINAL))
    for key in ("J", "S_perc", "S_ctrl", "S_intent", "weights"):
        assert key in result
