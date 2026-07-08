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


def test_derive_target_cam_types_single_view():
    assert derive_target_cam_types(["left"]) == ["cam_front"]
    assert derive_target_cam_types([]) == ["cam_front"]


def test_surface_plan_carries_target_cam_types():
    plan = build_actor_motion_plan(
        actor_controls=ACTORS,
        relations=["left"],
        motion_primitives=["lane_change"],
        executable_controls={},
    )
    assert plan["target_cam_types"] == ["cam_front"]
    assert plan["lateral_side"] == -1.0
    surface = build_actor_motion_surface_plan(plan)
    assert surface["target_cam_types"] == ["cam_front"]
    assert surface["lateral_side"] == -1.0


def test_left_lane_change_renders_on_left_and_approaches_ego():
    plan = build_actor_motion_plan(
        actor_controls=ACTORS,
        relations=["left"],
        motion_primitives=["lane_change"],
        executable_controls={},
    )
    surface = build_actor_motion_surface_plan(plan)
    xs = [entry["box3d"][0] for entry in surface["per_frame_boxes3d"]]
    assert all(x < 0 for x in xs), "left request must render on camera-left (negative x)"
    assert abs(xs[0]) > abs(xs[-1]), "|x| must decrease: approach the ego lane"
    # Left default base 3.5/20 (2026-07-08 distance sweep record).
    assert abs(xs[0] + 5.1) < 1e-6 and abs(xs[-1] + 1.9) < 1e-6


def test_left_cut_in_approaches_ego():
    plan = build_actor_motion_plan(
        actor_controls=ACTORS,
        relations=["left"],
        motion_primitives=["cut_in"],
        executable_controls={},
    )
    surface = build_actor_motion_surface_plan(plan)
    xs = [entry["box3d"][0] for entry in surface["per_frame_boxes3d"]]
    assert all(x < 0 for x in xs)
    # Left default base 3.5/20 (2026-07-08 distance sweep record).
    assert abs(xs[0] + 5.1) < 1e-6 and abs(xs[-1] + 2.7) < 1e-6


def test_right_side_keeps_calibrated_default():
    plan = build_actor_motion_plan(
        actor_controls=ACTORS,
        relations=["right"],
        motion_primitives=["lane_change"],
        executable_controls={},
    )
    surface = build_actor_motion_surface_plan(plan)
    assert surface["escalation_applied"]["lateral_base_m"] == 3.2
    xs = [entry["box3d"][0] for entry in surface["per_frame_boxes3d"]]
    assert all(x > 0 for x in xs)
    assert abs(xs[0] - 4.8) < 1e-6 and abs(xs[-1] - 1.6) < 1e-6


def test_maneuver_direction_check():
    evaluator = object.__new__(CompositePerceptionVideoEvaluator)
    evaluator.layout = CompositeVideoLayout()
    metadata = {
        "dd2_override_candidate_plan": {
            "actor_motion_surface_plan": {
                "maneuver": "lane_change",
                "lateral_side": -1.0,
                "target_cam_types": ["cam_front"],
                "target_actor": {"category": "motorcycle"},
            }
        }
    }
    moto = lambda x: [("motorcycle", x)]
    # left actor approaching ego: pixel x should increase
    ok = evaluator._maneuver_direction_check(
        metadata, [moto(100.0), None, moto(140.0), moto(180.0)]
    )
    assert ok is not None and ok[2] is True
    bad = evaluator._maneuver_direction_check(
        metadata, [moto(180.0), moto(140.0), moto(100.0)]
    )
    assert bad is not None and bad[2] is False
    assert evaluator._maneuver_direction_check(metadata, [moto(100.0), None]) is None
    # distractor-only detections must not produce a verdict
    cars = [[("car", 100.0)], [("car", 140.0)], [("car", 180.0)]]
    assert evaluator._maneuver_direction_check(metadata, cars) is None
    assert evaluator._maneuver_direction_check({}, [moto(1.0), moto(2.0), moto(3.0)]) is None


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
