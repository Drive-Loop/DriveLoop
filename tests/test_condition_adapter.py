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

def test_condition_adapter_builds_executable_condition_schema():
    request = DriveLoopRequest(
        prompt="foggy night intersection, a cyclist cuts in from the left while a pedestrian crosses in front"
    )

    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)
    condition = DriveDreamer2ConditionAdapter().build(spec, plan)

    executable = condition.executable_condition

    assert executable["schema_version"] == "dd2_executable_condition.v0"
    assert executable["target_backend"] == "drivedreamer2_mini"
    assert executable["text_control"]["prompt"] == condition.text_prompt

    assert executable["environment_controls"]["weather"] == "fog"
    assert executable["environment_controls"]["lighting"] == "night"
    assert executable["environment_controls"]["visibility"] == "low"

    actor_categories = {actor["category"] for actor in executable["actor_controls"]}
    assert "bicycle" in actor_categories
    assert "pedestrian" in actor_categories

    assert "cut_in" in executable["motion_controls"]
    assert "crossing" in executable["motion_controls"]
    assert "front" in executable["relation_controls"]
    assert "left" in executable["relation_controls"]

    assert "fog" in executable["risk_controls"]["long_tail_tags"]
    assert "low_visibility" in executable["risk_controls"]["long_tail_tags"]

    trace = executable["trace_metadata"]
    assert trace["structural_control_level"] == "schema_only"
    assert trace["tensor_control_ready"] is False
    assert "mini_dataset_structural_inputs_required" in trace["limitations"]

def test_executable_condition_normalizes_cyclist_actor_category():
    request = DriveLoopRequest(
        prompt="urban road with unusual hazard",
        metadata={
            "structured_intent": {
                "weather": "fog",
                "lighting": "night",
                "actors": [
                    {"category": "cyclist", "attributes": {}},
                ],
                "relations": ["left"],
                "motion_primitives": ["cut_in"],
                "risk_factors": ["low_visibility"],
            }
        },
    )

    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)
    condition = DriveDreamer2ConditionAdapter().build(spec, plan)

    actor = condition.executable_condition["actor_controls"][0]
    assert actor["category"] == "bicycle"
    assert actor["source_category"] == "cyclist"

def test_executable_condition_includes_mini_structural_input_plan():
    request = DriveLoopRequest(
        prompt="rainy night intersection, a pedestrian crosses in front while a car cuts in from the right"
    )

    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)
    condition = DriveDreamer2ConditionAdapter().build(spec, plan)

    structural_plan = condition.executable_condition["structural_input_plan"]

    assert structural_plan["target_dataset"] == "drivedreamer2_mini"
    assert structural_plan["control_level"] == "plan_only"

    assert structural_plan["scene_description"]["source"] == "text_control.prompt"
    assert structural_plan["scene_description"]["value"] == condition.text_prompt

    assert structural_plan["labels"]["source"] == "actor_controls.category"
    assert structural_plan["labels"]["values"] == ["car", "pedestrian"]

    assert structural_plan["image_hdmap"]["source"] == "mini_dataset_baseline"
    assert structural_plan["image_box"]["source"] == "mini_dataset_baseline"
    assert structural_plan["boxes3d"]["source"] == "mini_dataset_baseline"

    assert "actor_box_tensor_override_not_implemented" in structural_plan["limitations"]
    assert "trajectory_tensor_override_not_implemented" in structural_plan["limitations"]
    assert "hdmap_tensor_override_not_implemented" in structural_plan["limitations"]

