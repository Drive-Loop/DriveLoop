from __future__ import annotations

from driveloop.longtail_coverage import build_longtail_control_coverage
from driveloop.schema import LongTailConditionPlan, SceneSpecification


def by_tag(coverage, tag):
    return {row["tag"]: row for row in coverage["tags"]}[tag]


def test_weather_tag_can_be_covered_by_prompt_and_visual_effect():
    spec = SceneSpecification(
        prompt="urban road in heavy rain",
        environment={"weather": "rain"},
    )
    plan = LongTailConditionPlan(
        tags=["heavy_rain"],
        prompt_suffixes=["heavy rain with wet road surface and visible rain streaks"],
        postprocess_effects=["rain_overlay"],
        executable_controls={"weather": "heavy_rain"},
    )

    coverage = build_longtail_control_coverage(spec, plan)

    assert coverage["schema_version"] == "driveloop_longtail_control_coverage.v0"
    assert coverage["score"] == 1.0
    assert by_tag(coverage, "heavy_rain")["covered"] is True


def test_motion_tag_is_not_covered_by_prompt_keyword_only():
    spec = SceneSpecification(prompt="a motorcycle cuts in from the left")
    plan = LongTailConditionPlan(
        tags=["motorcycle_cut_in"],
        prompt_suffixes=["motorcycle cut in maneuver"],
    )

    coverage = build_longtail_control_coverage(spec, plan)
    row = by_tag(coverage, "motorcycle_cut_in")

    assert row["covered"] is False
    assert "source_or_structural" in row["missing_channels"]
    assert "evaluation" in row["missing_channels"]
    assert coverage["claim_boundary"]["prompt_keyword_alone_is_not_executable_control_for_object_or_motion"] is True


def test_motion_tag_is_covered_by_structural_runtime_and_evaluation_channels():
    spec = SceneSpecification(prompt="a motorcycle cuts in from the left")
    plan = LongTailConditionPlan(
        tags=["motorcycle_cut_in"],
        executable_controls={
            "objects": ["motorcycle"],
            "motion": ["cut_in"],
            "maneuvers": [{"type": "cut_in", "requires_lane_geometry": True}],
            "target_object_support": {"category": "motorcycle"},
            "perception_requirements": ["target_motorcycle_detectable", "cut_in_motion_measurable"],
        },
    )
    condition_package = {
        "trace_metadata": {"tensor_control_ready": True},
        "actor_controls": [{"category": "motorcycle"}],
        "motion_controls": ["cut_in"],
        "structural_input_plan": {
            "boxes3d": {"override_ready": True},
            "image_box": {"override_ready": True},
        },
        "trajectory_control_contract": {
            "status": "runtime_connected_via_per_frame_actor_boxes3d",
        },
    }

    coverage = build_longtail_control_coverage(spec, plan, condition_package)
    row = by_tag(coverage, "motorcycle_cut_in")

    assert coverage["score"] == 1.0
    assert row["covered"] is True
    assert row["channels"]["source_or_structural"] is True
    assert row["channels"]["evaluation"] is True


def test_nested_executable_condition_package_is_unwrapped():
    spec = SceneSpecification(prompt="low visibility road")
    plan = LongTailConditionPlan(
        tags=["low_visibility"],
        prompt_suffixes=["low visibility conditions with difficult object perception"],
        postprocess_effects=["low_visibility_filter"],
        executable_controls={"visibility": "low", "perception_requirements": ["target_object_visible_across_frames"]},
    )
    condition = {
        "executable_condition": {
            "environment_controls": {"visibility": "low"},
            "risk_controls": {"long_tail_tags": ["low_visibility"]},
        }
    }

    coverage = build_longtail_control_coverage(spec, plan, condition)

    assert coverage["score"] == 1.0
    assert by_tag(coverage, "low_visibility")["covered"] is True
