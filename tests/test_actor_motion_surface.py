from driveloop import DriveLoopRequest
from driveloop.actor_motion import build_actor_motion_plan, build_actor_motion_surface_plan
from driveloop.backends.drivedreamer2 import DriveDreamer2Backend
from driveloop.condition_adapter import DriveDreamer2ConditionAdapter
from driveloop.grounding import RuleBasedGrounder
from driveloop.longtail import LongTailController


def test_condition_adapter_exposes_actor_motion_plan_for_cut_in():
    request = DriveLoopRequest(prompt="urban road, a motorcycle cuts in from the left")
    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)
    condition = DriveDreamer2ConditionAdapter().build(spec, plan)

    executable = condition.executable_condition
    actor_motion_plan = executable["actor_motion_plan"]
    trajectory_contract = executable["trajectory_control_contract"]

    assert actor_motion_plan["available"] is True
    assert actor_motion_plan["runtime_surface"]["type"] == "boxes3d.per_frame_append"
    assert actor_motion_plan["target_actor"]["category"] == "motorcycle"
    assert len(actor_motion_plan["runtime_surface"]["frames"]) == 4
    assert trajectory_contract["status"] == "runtime_connected_via_per_frame_actor_boxes3d"
    assert trajectory_contract["current_runtime_surfaces"]["per_frame_actor_boxes3d"] == "boxes3d.per_frame_append"
    assert executable["trace_metadata"]["actor_motion_surface_ready"] is True


def test_actor_motion_surface_plan_builds_per_frame_boxes3d_entries():
    actor_motion_plan = build_actor_motion_plan(
        actor_controls=[
            {
                "actor_id": "actor_00",
                "category": "motorcycle",
                "source_category": "motorcycle",
            }
        ],
        relations=["left"],
        motion_primitives=["cut_in"],
        executable_controls={"target_object_support": {"category": "motorcycle"}},
    )

    surface_plan = build_actor_motion_surface_plan(actor_motion_plan)

    assert surface_plan["available"] is True
    assert surface_plan["status"] == "runtime_connected_via_per_frame_boxes3d"
    assert surface_plan["surface"] == "boxes3d.per_frame_append"
    assert len(surface_plan["per_frame_boxes3d"]) == 4
    assert {entry["frame_idx"] for entry in surface_plan["per_frame_boxes3d"]} == {0, 1, 2, 3}
    assert all(len(entry["box3d"]) == 9 for entry in surface_plan["per_frame_boxes3d"])


def test_backend_override_json_carries_actor_motion_surface_to_per_frame_append():
    backend = DriveDreamer2Backend()
    actor_motion_plan = build_actor_motion_plan(
        actor_controls=[
            {
                "actor_id": "actor_00",
                "category": "motorcycle",
                "source_category": "motorcycle",
            }
        ],
        relations=["left"],
        motion_primitives=["cut_in"],
        executable_controls={"target_object_support": {"category": "motorcycle"}},
    )
    structural_input_plan = {
        "scene_description": {
            "source": "text_control.prompt",
            "value": "urban road, a motorcycle cuts in from the left.",
        },
        "image_hdmap": {
            "source": "runtime_dataset_baseline",
            "reason": "no_verified_hdmap_override_source",
        },
        "image_box": {
            "source": "derived_from_boxes3d_override",
        },
        "boxes3d": {
            "source": "executable_condition_tensor_override",
        },
    }
    structural_request_diff = {
        "available": True,
        "missing_requested_labels": [],
        "extra_baseline_labels": [],
        "baseline_scene_description": "baseline",
        "requested_scene_description": "urban road, a motorcycle cuts in from the left.",
        "scene_description_changed": True,
    }

    candidate_plan = backend._build_override_candidate_plan(
        structural_input_plan=structural_input_plan,
        structural_request_diff=structural_request_diff,
        baseline_structural_snapshot={},
        actor_motion_plan=actor_motion_plan,
    )
    override_json = backend._build_override_json(
        dd2_prompt="urban road, a motorcycle cuts in from the left.",
        structural_input_plan=structural_input_plan,
        override_candidate_plan=candidate_plan,
    )

    assert candidate_plan["actor_motion_surface_plan"]["available"] is True
    assert candidate_plan["actor_motion_surface_plan"]["surface"] == "boxes3d.per_frame_append"
    assert override_json["boxes3d"]["mode"] == "append_and_per_frame_append"
    assert len(override_json["boxes3d"]["per_frame_append"]) == 4
    assert override_json["audit"]["control_level"] == "tensor_override_runtime"
    assert "per_frame_actor_boxes3d_runtime_surface_connected" in override_json["audit"]["limitations"]
