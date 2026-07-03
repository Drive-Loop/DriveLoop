# P0 Actor Motion Surface Connected

Date: 2026-07-03

## Summary

This record updates the P0 status after connecting DriveLoop actor-level motion intent to a DD2 runtime structural condition surface.

DriveLoop now builds an `actor_motion_plan` for lane-change / cut-in requests and maps it to `boxes3d.per_frame_append`. The DD2 backend carries this into `DRIVELOOP_DD2_OVERRIDE_JSON`, where the DD2 transform hook can apply per-frame boxes3d overrides and derive per-frame `image_box` / `box_downsampler_input` changes.

## Verified Evidence

Full test command passed:

- `PYTHONPATH=.:dreamer-datasets:dreamer-train:dreamer-models pytest -q`
- Result: `231 passed, 1 warning`

The focused backend evidence reported:

- `trajectory_status`: `runtime_connected_via_per_frame_actor_boxes3d`
- `actor_motion_surface_ready`: `true`
- `tensor_control_ready`: `true`
- `actor_motion_surface_available`: `true`
- `actor_motion_surface`: `boxes3d.per_frame_append`
- `override_mode`: `append_and_per_frame_append`
- `per_frame_append_count`: `4`

The override audit limitations include:

- `box_positions_are_draft_until_projection_and_scene_geometry_are_verified`
- `per_frame_actor_boxes3d_runtime_surface_connected`
- `hdmap_kept_baseline_without_explicit_verified_override`

## Runtime Surface Chain

The connected P0 chain is:

1. prompt / structured condition
2. `motion_primitives` such as `cut_in` or `lane_change`
3. `actor_motion_plan`
4. `actor_motion_surface_plan`
5. `boxes3d.per_frame_append`
6. DD2 transform override hook
7. derived `image_box_canvas`
8. derived `box_downsampler_input`

## Claim Boundary

Allowed:

- Claim actor-level per-frame boxes3d structural motion conditioning is connected.
- Claim lane-change / cut-in intent can be represented as a per-frame actor boxes3d runtime surface.
- Claim the runtime override JSON can carry `boxes3d.per_frame_append` into DD2 transform conditioning.
- Claim previous P0 blocker `trajectory_runtime_surface_not_connected` is addressed for this structural motion surface.

Not allowed:

- Do not claim velocity tensor control.
- Do not claim displacement tensor control.
- Do not claim physically verified trajectory dynamics.
- Do not claim true HDMap lane geometry replacement.
- Do not claim GPU video semantic success from this evidence alone.
- Do not claim lane-change success without generated-video review.

## Current P0 Interpretation

P0 is complete for the scoped implementation target:

`actor-level lane-change / cut-in intent -> per-frame boxes3d runtime structural conditioning -> DD2 image_box / box_downsampler_input condition surface`.

P0 remains explicitly limited outside this scope:

- velocity/displacement tensor control is still not connected;
- HDMap lane geometry replacement is still not connected;
- generated video semantic success still requires separate GPU smoke and manual/metric review.
