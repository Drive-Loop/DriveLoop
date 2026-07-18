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
    # Lighting is a requested control that cannot be measured under
    # source-bound generation, so it is reported as unmeasured and never
    # scored -- even with a brightness metric present.
    assert "lighting_night" not in result["channels"]
    assert "lighting.night" in result["unmeasured"]


def test_target_motion_scored_without_a_parsed_motion_primitive():
    # Construction D (block 217): an empty motion_primitives is almost
    # always a parse failure -- the grounder's keyword table missed the
    # motion verb -- not a case declining motion. target_motion is scored
    # from the archived measurement regardless, so such a case is not
    # spared the channel and cannot inflate the lever by owning a single
    # channel to divide by.
    spec, plan = _spec_plan("a motorcycle at an intersection")
    assert spec.motion_primitives == []
    metrics = {
        "perception_measured": 1.0,
        "perception_detection_count": 3.0,
        "perception_dominant_motion_over_width": -1.0,
    }
    result = control_visibility_score(metrics, spec, plan)
    assert result["channels"]["target_motion"] == 0.0
    assert result["channels"]["object_presence"] == 1.0
    assert result["score"] == 0.5


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


def test_object_presence_is_fidelity_weighted_under_v10():
    # Caliber C (block 223): when the super-class evaluator reports class
    # fidelity, object_presence is the share of detections that read as the
    # target class, so pure non-target residue does not count the control as
    # visible.
    spec, plan = _spec_plan(PROMPT)
    base = {"perception_measured": 1.0, "perception_dominant_motion_over_width": -1.0}
    weighted = control_visibility_score(
        {**base, "perception_superclass_detection_count": 3.0, "perception_class_fidelity": 0.4},
        spec, plan,
    )
    assert weighted["channels"]["object_presence"] == 0.4
    residue = control_visibility_score(
        {**base, "perception_superclass_detection_count": 2.0, "perception_class_fidelity": 0.0},
        spec, plan,
    )
    assert residue["channels"]["object_presence"] == 0.0


def test_v9_metrics_keep_binary_object_presence():
    # Backward compatibility: without class fidelity (v9 metrics) object_presence
    # is the binary target-class detection, so the change is inert until the v10
    # protocol is wired in.
    spec, plan = _spec_plan(PROMPT)
    base = {"perception_measured": 1.0, "perception_dominant_motion_over_width": -1.0}
    assert control_visibility_score({**base, "perception_detection_count": 3.0}, spec, plan)[
        "channels"]["object_presence"] == 1.0
    assert control_visibility_score({**base, "perception_detection_count": 0.0}, spec, plan)[
        "channels"]["object_presence"] == 0.0
