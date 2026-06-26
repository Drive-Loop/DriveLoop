from driveloop import DriveLoopRequest
from driveloop.condition_adapter import DriveDreamer2ConditionAdapter
from driveloop.grounding import RuleBasedGrounder
from driveloop.longtail import LongTailController


def test_condition_adapter_builds_dd2_intermediate_condition():
    request = DriveLoopRequest(
        prompt="rainy night intersection, a pedestrian crosses in front while a car cuts in from the right"
    )

    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)
    condition = DriveDreamer2ConditionAdapter().build(spec, plan)

    assert condition.environment["weather"] == "rain"
    assert condition.environment["lighting"] == "night"
    assert {"category": "pedestrian", "attributes": {}} in condition.actors
    assert {"category": "car", "attributes": {}} in condition.actors
    assert "crossing" in condition.motion_primitives
    assert "cut_in" in condition.motion_primitives
    assert "heavy_rain" in condition.long_tail_tags
    assert "animal_crossing" not in condition.long_tail_tags
    assert "heavy rain with wet road surface" in condition.text_prompt
