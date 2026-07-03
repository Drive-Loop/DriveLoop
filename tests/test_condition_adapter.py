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
    assert executable["target_backend"] == "drivedreamer2_runtime"
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
    assert trace["structural_control_level"] == "runtime_surface_contract"
    assert trace["tensor_control_ready"] is False
    assert "runtime_structural_surfaces_observed_not_overridden" in trace["limitations"]

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

    assert structural_plan["target_dataset"] == "drivedreamer2_runtime"
    assert structural_plan["control_level"] == "runtime_surface_contract"

    assert structural_plan["scene_description"]["source"] == "text_control.prompt"
    assert structural_plan["scene_description"]["value"] == condition.text_prompt

    assert structural_plan["labels"]["source"] == "actor_controls.category"
    assert structural_plan["labels"]["values"] == ["car", "pedestrian"]

    assert structural_plan["image_hdmap"]["source"] == "runtime_dataset_baseline"
    assert structural_plan["image_box"]["source"] == "derived_from_runtime_boxes3d_canvas"
    assert structural_plan["image_box"]["override_ready"] is False
    assert structural_plan["boxes3d"]["source"] == "runtime_dataset_baseline"
    assert structural_plan["boxes3d"]["override_ready"] is False

    assert "trajectory_tensor_override_not_implemented" in structural_plan["limitations"]
    assert "hdmap_tensor_override_requires_explicit_verified_source" in structural_plan["limitations"]

def test_executable_condition_carries_alignment_feedback_as_audit_trace_only():
    request = DriveLoopRequest(prompt="daytime urban road with a motorcycle changing lane from the left")
    alignment_feedback = {
        "schema_version": "driveloop_alignment_feedback.v0",
        "status": "measured_failed",
        "control_level": "text_feedback_only",
        "failed_checks": ["object_presence.motorcycle"],
        "requested_visual_constraints": ["a motorcycle must be visibly present"],
    }

    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)
    condition = DriveDreamer2ConditionAdapter().build(
        spec,
        plan,
        alignment_feedback=alignment_feedback,
    )

    trace = condition.executable_condition["trace_metadata"]
    feedback = trace["alignment_feedback"]

    assert trace["tensor_control_ready"] is False
    assert trace["structural_control_level"] == "runtime_surface_contract"
    assert feedback["schema_version"] == "driveloop_alignment_feedback.v0"
    assert feedback["status"] == "measured_failed"
    assert feedback["control_level"] == "text_feedback_only"
    assert feedback["failed_checks"] == ["object_presence.motorcycle"]
    assert "not verified tensor-level DD2 control" in feedback["claim_boundary"]


def test_executable_condition_includes_trajectory_control_contract_for_lane_change():
    request = DriveLoopRequest(prompt="daytime urban road with a motorcycle changing lane from the left")

    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)
    condition = DriveDreamer2ConditionAdapter().build(spec, plan)

    contract = condition.executable_condition["trajectory_control_contract"]

    assert contract["schema_version"] == "driveloop_trajectory_control_contract.v0"
    assert contract["status"] == "not_runtime_connected"
    assert contract["control_level"] == "contract_only"
    assert "lane_change" in contract["requested_motions"]
    assert contract["requested_maneuvers"][0]["type"] == "lane_change_or_cut_in"
    assert "per_frame_actor_boxes3d" in contract["required_runtime_surfaces"]
    assert contract["current_runtime_surfaces"]["velocities"] == "dataset_surface_observed_not_dd2_condition_tensor"
    assert "cannot prove lane-change video semantics" in contract["claim_boundary"]


def test_executable_condition_carries_structured_motorcycle_longtail_controls():
    request = DriveLoopRequest(
        prompt="foggy night road where a motorcycle changes lane from the right adjacent lane"
    )

    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)
    condition = DriveDreamer2ConditionAdapter().build(spec, plan)

    controls = condition.executable_condition["risk_controls"]["executable_controls"]

    assert "motorcycle_lane_change" in condition.long_tail_tags
    assert "right_lane_relation" in condition.long_tail_tags
    assert "motorcycle" in controls["objects"]
    assert "lane_change" in controls["motion"]
    assert controls["target_object_support"]["category"] == "motorcycle"
    assert controls["maneuvers"][0]["type"] == "lane_change"
    assert controls["lane_relations"][0]["from"] == "right_adjacent_lane"

    trajectory = condition.executable_condition["trajectory_control_contract"]
    assert "lane_change" in trajectory["requested_motions"]
    assert trajectory["requested_maneuvers"][0]["type"] == "lane_change_or_cut_in"
    assert trajectory["status"] == "not_runtime_connected"
