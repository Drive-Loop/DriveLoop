# Actor Track Surface Audit

Date: 2026-07-02

## Scope

This note records a non-GPU label-surface audit for per-frame actor identity and boxes3d grouping.

It does not claim runtime motion control, lane-change control, prompt-to-video semantic success, or paper-level semantic success.

## Input

Actor track audit input:

`outputs/driveloop/tiny_real_actor_identity_runtime_dataset/cam_front_8/v0.0.1/labels/data.pkl`

This tiny subset contains real nuScenes `sample_annotation_tokens` and `instance_tokens` patched into processed label records.

## Artifacts

Actor track surface audit:

`outputs/driveloop/actor_track_surface_audit/tiny_real_actor_track_surface_audit.json`

Trajectory runtime surface audit using actor-track evidence:

`outputs/driveloop/trajectory_runtime_surface_audit/tiny_real_actor_track_trajectory_runtime_surface_audit.json`

## Observed Result

Actor track surface audit reported:

- `status`: `per_frame_actor_tracks_observed`
- `actor_identity_available`: `true`
- `boxes_grouped_by_instance_token`: `true`
- `persistent_track_count`: `20`
- `max_track_length`: `8`

Trajectory runtime surface audit now reports:

- `per_frame_actor_identity_observed`: `true`
- `per_frame_actor_boxes3d.verified`: `true`
- `per_frame_actor_boxes3d.current_surface`: `grouped_by_instance_token`
- `status`: `not_runtime_connected`

The previous actor identity / per-frame boxes blockers are cleared, but runtime motion control remains blocked.

Remaining blockers:

- `trajectory_tensor_not_observed_in_runtime_audit`
- `velocity_or_displacement_tensor_not_consumed_by_runtime`
- `hdmap_lane_geometry_override_not_verified`
- `static_box_condition_available_but_not_temporal_motion_control`

## Claim Boundary

Allowed claims:

- The tiny real-token processed label subset can group per-frame boxes3d by persistent `instance_tokens`.
- Actor identity and per-frame actor boxes are observable as label/data surfaces.
- Trajectory runtime surface audit can consume actor-track audit evidence.

Disallowed claims:

- Runtime motion control is connected.
- Lane-change control is verified.
- Static boxes prove temporal motion.
- Grouped actor tracks prove video semantics.
- Prompt-to-video semantic success is achieved.
- The motorcycle lane-change case is semantically successful.

## Next Non-GPU Work

1. Investigate whether velocity or displacement can be surfaced as a runtime-consumed tensor.
2. Investigate whether DD2 exposes or can accept a trajectory/displacement runtime surface.
3. Audit HDMap/lane geometry compatibility before any lane-change intervention.
4. Do not run a new GPU candidate until a target runtime motion surface is auditably changed.
