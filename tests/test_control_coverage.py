from driveloop.grounding import RuleBasedGrounder
from driveloop.longtail import LongTailController, control_coverage
from driveloop.schema import DriveLoopRequest, LongTailConditionPlan


def _plan_for(prompt: str, tags=None) -> LongTailConditionPlan:
    request = DriveLoopRequest(prompt=prompt)
    spec = RuleBasedGrounder().ground(request)
    return LongTailController().build(spec, requested_tags=tags or [])


def test_no_tags_gives_full_coverage():
    plan = _plan_for("a car driving on a sunny road")
    result = control_coverage(plan)
    assert result["score"] == 1.0
    assert result["tag_count"] == 0
    assert result["unsupported_tags"] == []


def test_fog_tag_is_supported_by_executable_channels():
    plan = _plan_for("driving in dense fog")
    result = control_coverage(plan)
    assert result["tag_support"].get("fog") is True
    assert "fog" not in result["unsupported_tags"]


def test_motorcycle_lane_change_supported():
    plan = _plan_for("a motorcycle performs a lane change from the left")
    result = control_coverage(plan)
    assert result["tag_support"].get("motorcycle_lane_change") is True
    assert result["tag_support"].get("left_lane_relation") is True
    assert result["score"] == 1.0


def test_keyword_only_plan_is_not_counted_as_supported():
    # Build a plan whose tag has no executable channels behind it.
    plan = LongTailConditionPlan(
        tags=["fog"],
        prompt_suffixes=["dense fog"],
        postprocess_effects=[],
        executable_controls={},
    )
    result = control_coverage(plan)
    assert result["tag_support"]["fog"] is False
    assert result["unsupported_tags"] == ["fog"]
    assert result["score"] == 0.0


def test_tag_weights_change_score():
    plan = LongTailConditionPlan(
        tags=["fog", "road_obstacle"],
        prompt_suffixes=["dense fog"],
        postprocess_effects=["fog_overlay"],
        executable_controls={"visibility": "low"},  # fog supported, obstacle not
    )
    equal = control_coverage(plan)
    weighted = control_coverage(plan, tag_weights={"fog": 3.0, "road_obstacle": 1.0})
    assert equal["score"] == 0.5
    assert weighted["score"] == 0.75


def test_unknown_tag_is_unsupported():
    plan = LongTailConditionPlan(
        tags=["mystery_tag"],
        prompt_suffixes=["something"],
        postprocess_effects=[],
        executable_controls={"objects": ["car"]},
    )
    result = control_coverage(plan)
    assert result["unsupported_tags"] == ["mystery_tag"]
