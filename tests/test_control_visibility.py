from driveloop.control_visibility import control_visibility_score
from driveloop.grounding import RuleBasedGrounder
from driveloop.longtail import LongTailController
from driveloop.schema import DriveLoopRequest


def _spec_plan(prompt):
    spec = RuleBasedGrounder().ground(DriveLoopRequest(prompt=prompt))
    plan = LongTailController().build(spec, requested_tags=[])
    return spec, plan


PROMPT = "at night a motorcycle changes lane from the left"


def test_not_measured_without_perception():
    spec, plan = _spec_plan(PROMPT)
    result = control_visibility_score({}, spec, plan)
    assert result["score"] is None


def test_all_channels_visible():
    spec, plan = _spec_plan(PROMPT)
    metrics = {
        "perception_measured": 1.0,
        "perception_detection_count": 3.0,
        "perception_dominant_motion_over_width": 1.2,
        "perception_best_view_brightness": 60.0,
    }
    result = control_visibility_score(metrics, spec, plan)
    assert result["score"] == 1.0
    assert result["channels"]["object_presence"] == 1.0
    assert result["channels"]["target_motion"] == 1.0
    assert result["channels"]["lighting_night"] == 1.0


def test_static_target_reduces_motion_channel():
    spec, plan = _spec_plan(PROMPT)
    metrics = {
        "perception_measured": 1.0,
        "perception_detection_count": 3.0,
        "perception_dominant_motion_over_width": 0.0,
        "perception_best_view_brightness": 60.0,
    }
    result = control_visibility_score(metrics, spec, plan)
    assert result["channels"]["target_motion"] == 0.0
    assert result["score"] < 1.0


def test_weather_is_unmeasured_not_passed():
    spec, plan = _spec_plan("in heavy rain a motorcycle changes lane at night")
    metrics = {
        "perception_measured": 1.0,
        "perception_detection_count": 1.0,
        "perception_dominant_motion_over_width": 1.0,
        "perception_best_view_brightness": 50.0,
    }
    result = control_visibility_score(metrics, spec, plan)
    assert "weather.rain" in result["unmeasured"]
    assert "weather" not in str(result["channels"])
