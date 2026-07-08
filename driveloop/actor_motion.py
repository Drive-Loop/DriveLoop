from __future__ import annotations

from typing import Any, Iterable
import os


_DEFAULT_BOX_DIMS = {
    "bicycle": {"width": 0.6, "height": 1.6, "depth": 1.8},
    "motorcycle": {"width": 0.8, "height": 1.4, "depth": 2.2},
    "pedestrian": {"width": 0.6, "height": 1.7, "depth": 0.6},
    "car": {"width": 1.8, "height": 1.6, "depth": 4.5},
    "truck": {"width": 2.5, "height": 3.0, "depth": 7.0},
    "bus": {"width": 2.6, "height": 3.2, "depth": 10.0},
}


_ALL_CAM_TYPES = [
    "cam_front_left",
    "cam_front",
    "cam_front_right",
    "cam_back_right",
    "cam_back",
    "cam_back_left",
]


def derive_target_cam_types(relations: Iterable[str]) -> list[str]:
    """Single-view injection: the per-frame boxes3d surface has no
    camera-extrinsic transform, so injecting the same camera-frame box
    into multiple views creates physically inconsistent clones. Until an
    extrinsic-aware projection exists, inject and evaluate cam_front
    only; the signed lateral geometry keeps the actor inside the front
    FOV for the whole trajectory.

    DRIVELOOP_INJECT_ALL_CAM_TYPES=1 restores the pre-17983a4 all-view
    append as a DIAGNOSTIC PROBE ONLY (physically inconsistent clones;
    never a source of paper numbers)."""
    if os.environ.get("DRIVELOOP_INJECT_ALL_CAM_TYPES") == "1":
        return list(_ALL_CAM_TYPES)
    return ["cam_front"]


def derive_lateral_side(relations: Iterable[str]) -> float:
    """Camera-frame x is positive to the RIGHT (verified against
    detected pixel trajectories). left -> -1.0, otherwise +1.0."""
    rels = {str(item).lower() for item in relations}
    return -1.0 if "left" in rels else 1.0


def build_actor_motion_plan(
    actor_controls: list[dict[str, Any]],
    relations: Iterable[str],
    motion_primitives: Iterable[str],
    executable_controls: dict[str, Any] | None = None,
) -> dict[str, Any]:
    requested_motions = list(dict.fromkeys(str(item) for item in motion_primitives))
    requested_relations = list(dict.fromkeys(str(item) for item in relations))
    motion_set = set(requested_motions)

    if "lane_change" not in motion_set and "cut_in" not in motion_set:
        return {
            "schema_version": "driveloop_actor_motion_plan.v0",
            "available": False,
            "status": "not_requested",
            "reason": "no_lane_change_or_cut_in_motion_requested",
            "requested_motions": requested_motions,
            "requested_relations": requested_relations,
        }

    target_actor = _select_target_actor(actor_controls, executable_controls or {})
    if not target_actor:
        return {
            "schema_version": "driveloop_actor_motion_plan.v0",
            "available": False,
            "status": "missing_target_actor",
            "requested_motions": requested_motions,
            "requested_relations": requested_relations,
        }

    maneuver = "cut_in" if "cut_in" in motion_set else "lane_change"
    frames = _build_motion_frames(
        actor_id=str(target_actor["actor_id"]),
        category=str(target_actor["category"]),
        maneuver=maneuver,
        relations=requested_relations,
    )

    return {
        "schema_version": "driveloop_actor_motion_plan.v0",
        "available": True,
        "status": "runtime_connectable",
        "control_level": "per_frame_actor_boxes3d_surface",
        "target_actor": {
            "actor_id": target_actor["actor_id"],
            "category": target_actor["category"],
            "source_category": target_actor.get("source_category"),
        },
        "synthetic_track_id": f"{target_actor['actor_id']}_synthetic_motion_track",
        "requested_motions": requested_motions,
        "requested_relations": requested_relations,
        "target_cam_types": derive_target_cam_types(requested_relations),
        "lateral_side": derive_lateral_side(requested_relations),
        "maneuver": maneuver,
        "escalation": (executable_controls or {}).get("structural_escalation"),
        "runtime_surface": {
            "type": "boxes3d.per_frame_append",
            "frames": frames,
            "frame_count": len(frames),
            "boxes3d_format": "x_y_z_width_height_depth_rotX_rotY_rotZ",
        },
        "claim_boundary": (
            "This plan controls actor motion through per-frame boxes3d structural conditioning. "
            "It is not a velocity tensor, not a displacement tensor, and not proof of generated video semantics."
        ),
    }


def build_actor_motion_surface_plan(actor_motion_plan: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(actor_motion_plan, dict) or actor_motion_plan.get("available") is not True:
        return {
            "available": False,
            "status": "not_available",
            "reason": actor_motion_plan.get("reason", "missing_actor_motion_plan")
            if isinstance(actor_motion_plan, dict)
            else "missing_actor_motion_plan",
        }

    target_actor = actor_motion_plan.get("target_actor", {})
    category = str(target_actor.get("category") or "car")
    dims = _DEFAULT_BOX_DIMS.get(category, _DEFAULT_BOX_DIMS["car"])
    escalation = actor_motion_plan.get("escalation") or {}
    proximity_scale = float(escalation.get("proximity_scale", 1.0))
    size_scale = float(escalation.get("size_scale", 1.0))
    lateral_side = float(actor_motion_plan.get("lateral_side") or 1.0)
    # Side-specific defaults. RIGHT: 3.2/9 (2026-07-07 sweep; near range,
    # pending gated re-audit, no human-verified cell yet). LEFT: 3.5/20
    # from the 2026-07-08 2D distance sweep (human-verified motorcycle,
    # baseline-differential detection; rendering quality rises with
    # injection distance at the mini config). Escalation overrides stay
    # absolute.
    if lateral_side >= 0:
        default_lateral, default_longitudinal = 3.2, 9.0
    else:
        default_lateral, default_longitudinal = 3.5, 20.0
    lateral_base = float(escalation.get("lateral_base_m", default_lateral * proximity_scale))
    longitudinal_base = float(escalation.get("longitudinal_base_m", default_longitudinal * proximity_scale))
    dims = {key: value * size_scale for key, value in dims.items()}
    frames = actor_motion_plan.get("runtime_surface", {}).get("frames", [])
    per_frame_boxes3d = []

    for frame in frames:
        frame_idx = int(frame["frame_idx"])
        lateral_offset = float(frame.get("lateral_offset_m", 0.0))
        longitudinal_offset = float(frame.get("longitudinal_offset_m", 0.0))
        yaw = float(frame.get("yaw_rad", -0.25))
        per_frame_boxes3d.append(
            {
                "frame_idx": frame_idx,
                "actor_id": target_actor.get("actor_id"),
                "synthetic_track_id": actor_motion_plan.get("synthetic_track_id"),
                "category": category,
                "box3d": [
                    round(lateral_side * lateral_base + lateral_offset, 6),
                    1.8,
                    round(longitudinal_base + longitudinal_offset, 6),
                    dims["width"],
                    dims["height"],
                    dims["depth"],
                    0.0,
                    0.0,
                    yaw,
                ],
                "source": "actor_motion_plan.per_frame_actor_boxes3d",
                "provenance": "driveloop_actor_motion_surface",
                "motion_surface": actor_motion_plan.get("runtime_surface", {}).get("type"),
                "maneuver": actor_motion_plan.get("maneuver"),
            }
        )

    return {
        "available": bool(per_frame_boxes3d),
        "status": "runtime_connected_via_per_frame_boxes3d"
        if per_frame_boxes3d
        else "no_per_frame_boxes3d",
        "control_level": "tensor_override_runtime",
        "surface": "boxes3d.per_frame_append",
        "escalation_applied": {
            "proximity_scale": proximity_scale,
            "size_scale": size_scale,
            "lateral_base_m": lateral_base,
            "longitudinal_base_m": longitudinal_base,
        },
        "target_actor": target_actor,
        "synthetic_track_id": actor_motion_plan.get("synthetic_track_id"),
        "target_cam_types": list(actor_motion_plan.get("target_cam_types") or ["cam_front"]),
        "lateral_side": lateral_side,
        "maneuver": actor_motion_plan.get("maneuver"),
        "per_frame_boxes3d": per_frame_boxes3d,
        "claim_boundary": actor_motion_plan.get("claim_boundary"),
        "limitations": [
            "per_frame_boxes3d_controls_structure_not_velocity_tensor",
            "synthetic_track_identity_is_drive_loop_defined",
            "video_semantic_success_requires_separate_review",
            "lane_geometry_reference_not_replaced",
        ],
    }


def _select_target_actor(
    actor_controls: list[dict[str, Any]],
    executable_controls: dict[str, Any],
) -> dict[str, Any] | None:
    target_support = executable_controls.get("target_object_support", {})
    preferred_category = target_support.get("category") if isinstance(target_support, dict) else None

    if preferred_category:
        for actor in actor_controls:
            if actor.get("category") == preferred_category:
                return actor

    for preferred in ("motorcycle", "bicycle", "car", "truck", "bus"):
        for actor in actor_controls:
            if actor.get("category") == preferred:
                return actor

    return actor_controls[0] if actor_controls else None


def _linspace(start: float, end: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    return [start + (end - start) * idx / (count - 1) for idx in range(count)]


def _build_motion_frames(
    actor_id: str,
    category: str,
    maneuver: str,
    relations: list[str],
) -> list[dict[str, Any]]:
    side = -1.0 if "left" in relations else 1.0
    frame_count = 8

    # Offset magnitudes are relative to the (unsigned) lateral base.
    # Both maneuvers APPROACH the ego lane: |x| decreases over time.
    if maneuver == "cut_in":
        magnitudes = _linspace(1.6, -0.8, frame_count)
        longitudinal_offsets = _linspace(2.0, -0.4, frame_count)
    else:
        magnitudes = _linspace(1.6, -1.6, frame_count)
        longitudinal_offsets = _linspace(1.8, 0.0, frame_count)

    return [
        {
            "frame_idx": idx,
            "actor_id": actor_id,
            "category": category,
            "lateral_offset_m": side * magnitudes[idx],
            "longitudinal_offset_m": longitudinal_offsets[idx],
            "yaw_rad": -0.25 * side,
        }
        for idx in range(frame_count)
    ]
