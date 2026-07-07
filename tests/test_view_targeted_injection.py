from driveloop.actor_motion import (
    build_actor_motion_plan,
    build_actor_motion_surface_plan,
    derive_target_cam_types,
)
from driveloop.backends.drivedreamer2 import DriveDreamer2Backend
from driveloop.composite_perception import (
    CompositePerceptionVideoEvaluator,
    CompositeVideoLayout,
)

ACTORS = [{"actor_id": "actor_01", "category": "motorcycle", "source_category": "motorcycle"}]


def test_derive_target_cam_types_left():
    assert derive_target_cam_types(["left"]) == ["cam_front_left", "cam_front"]


def test_derive_target_cam_types_default_front():
    assert derive_target_cam_types([]) == ["cam_front"]


def test_surface_plan_carries_target_cam_types():
    plan = build_actor_motion_plan(
        actor_controls=ACTORS,
        relations=["left"],
        motion_primitives=["lane_change"],
        executable_controls={},
    )
    assert plan["target_cam_types"] == ["cam_front_left", "cam_front"]
    surface = build_actor_motion_surface_plan(plan)
    assert surface["target_cam_types"] == ["cam_front_left", "cam_front"]


def _identities(cam_types):
    return [
        {
            "available": True,
            "relative_step": 0,
            "frame_idx": 100,
            "cam_type": cam,
            "sample_token": "tok",
            "scene_token": "scene",
            "record_index": idx,
        }
        for idx, cam in enumerate(cam_types)
    ]


def test_mapping_filters_non_target_views(monkeypatch):
    backend = object.__new__(DriveDreamer2Backend)
    cams = [
        "cam_front_left", "cam_front", "cam_front_right",
        "cam_back_right", "cam_back", "cam_back_left",
    ]
    monkeypatch.setattr(
        backend,
        "_build_source_bound_sample_identities",
        lambda binding: _identities(cams),
        raising=False,
    )
    boxes = [{"frame_idx": 0, "actor_id": "actor_01", "category": "motorcycle", "box3d": [1] * 9}]
    mapped, mapping = backend._map_per_frame_actor_boxes_to_source_bound_samples(
        boxes, {}, ["cam_front_left", "cam_front"]
    )
    assert len(mapped) == 2
    assert {m["sample_identity"]["cam_type"] for m in mapped} == {"cam_front_left", "cam_front"}
    assert mapping["view_filter"]["filtered_out_count"] == 4
    assert mapping["view_filter"]["all_entries_filtered"] is False


def test_mapping_without_targets_keeps_legacy_behavior(monkeypatch):
    backend = object.__new__(DriveDreamer2Backend)
    cams = ["cam_front_left", "cam_front"]
    monkeypatch.setattr(
        backend,
        "_build_source_bound_sample_identities",
        lambda binding: _identities(cams),
        raising=False,
    )
    boxes = [{"frame_idx": 0, "actor_id": "actor_01", "category": "motorcycle", "box3d": [1] * 9}]
    mapped, mapping = backend._map_per_frame_actor_boxes_to_source_bound_samples(boxes, {}, None)
    assert len(mapped) == 2
    assert mapping["view_filter"]["filtered_out_count"] == 0


def test_target_view_indices_resolution():
    evaluator = object.__new__(CompositePerceptionVideoEvaluator)
    evaluator.layout = CompositeVideoLayout()
    metadata = {
        "dd2_override_candidate_plan": {
            "actor_motion_surface_plan": {
                "target_cam_types": ["cam_front_left", "cam_front"],
            }
        }
    }
    assert evaluator._target_view_indices(metadata) == [0, 1]
    assert evaluator._target_view_indices({}) == []
    assert evaluator._target_view_indices({"dd2_override_candidate_plan": None}) == []
