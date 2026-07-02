# Candidate70 Runtime Motion Surface Audit

Date: 2026-07-02

## Scope

This note records a non-GPU runtime motion surface audit for candidate70.

It does not claim prompt-to-video semantic success, runtime motion control, HDMap lane geometry override, lane-change semantic success, or paper-level success.

## Candidate Context

Candidate70 has improved source and prompt-conditioning evidence:

- source visibility: verified
- raw motorcycle identity: verified
- prompt-conditional support: allowed for the explicit night lane-change / cut-in suggested prompt
- old daytime prompt compatibility: blocked

Suggested prompt used for this audit:

- night urban street with a motorcycle or scooter making a visible lane-change / cut-in from the left toward the ego vehicle, panoramic multi-view video.

## Runtime Audit Artifacts

Runtime/code audit outputs:

- outputs/driveloop/runtime_surface_code_audit/candidate70_runtime_surface_code_audit.json
- outputs/driveloop/dd2_velocity_surface_audit/train_velocity_surface_candidate70_context.json
- outputs/driveloop/trajectory_runtime_surface_audit/candidate70_night_cut_in_trajectory_runtime_surface_audit.json

## Observed Runtime Code Surface

The code audit status remained:

- status: not_runtime_connected

Observed model-facing runtime condition surfaces:

- image_hdmap / grounding_downsampler_input
- image_box / box_downsampler_input
- img_cond
- prompt_embed

The code audit found dataset-level velocity and lane/HDMap source data, but DD2 runtime consumption is still downsampler-based.

## Velocity / Trajectory Clarification

The train labels contain velocity metadata:

- velocities present in train labels: true
- train label rows available: 11188

However, exact code-context inspection showed that velocity mentions are limited to audit-only metadata in transform/tester paths:

- motion_metadata.velocities_available_in_batch
- motion_metadata.velocities_shape
- actor label / identity audit fields

No velocity, trajectory, displacement, track_id, or actor trajectory surface was observed in the model-facing pipeline or UNet paths.

Therefore:

- velocity metadata observed: true
- velocity consumed as DD2 model input: false
- trajectory tensor observed: false
- displacement tensor observed: false

## Trajectory Runtime Surface Audit Result

The candidate70 trajectory audit returned:

- status: not_runtime_connected
- requested_motions: lane_change, cut_in

Observed surfaces:

- box_condition.available: true
- grounding_condition.available: true
- trajectory_tensor.available: false
- velocity_tensor.available_in_runtime_audit: false
- actor_track_identity.per_frame_actor_identity_observed: true
- per_frame_actor_boxes3d.verified: true
- hdmap_lane_geometry.override_verified: false

Blockers:

- trajectory_tensor_not_observed_in_runtime_audit
- hdmap_lane_geometry_override_not_verified
- static_box_condition_available_but_not_temporal_motion_control

## Interpretation

Candidate70 improves the source candidate and prompt-conditioning side of the loop, but it does not connect runtime motion control.

Static/spatial conditions are available, including image_box and image_hdmap downsampler inputs. These surfaces do not prove temporal lane-change or cut-in control.

Actor identity and per-frame boxes are useful audit evidence, but current DD2 runtime still does not consume a verified trajectory, velocity, displacement, or lane geometry override tensor.

## Claim Boundary

Allowed claims:

- Candidate70 is source-visible and prompt-conditional for the explicit night lane-change / cut-in suggested prompt.
- Candidate70 runtime audit still reports not_runtime_connected for requested motion.
- Velocity metadata exists in labels and can be surfaced in audit-only metadata.
- Actor identity and per-frame boxes are observed in audit evidence.
- HDMap raster and image_box conditions are model-facing spatial surfaces.

Disallowed claims:

- Candidate70 verifies runtime motion control.
- Candidate70 verifies lane-change / cut-in control.
- Candidate70 verifies HDMap lane geometry override.
- Candidate70 proves velocity, trajectory, or displacement is consumed by DD2 runtime.
- Candidate70 proves prompt-to-video semantic success.
- Static boxes, HDMap raster mutation, metadata, or tensor hashes prove video semantics.
- A GPU run is justified as paper-level semantic validation before runtime motion surfaces are connected.

## Recommended Status

- candidate70_source_prompt_status: improved_partial
- candidate70_runtime_motion_surface_status: not_runtime_connected
- velocity_metadata_status: metadata_observed_not_runtime_control
- trajectory_tensor_available: false
- velocity_runtime_consumption: false
- hdmap_lane_geometry_override_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Do not train and do not run long GPU jobs.

The next non-GPU step should be either:

1. implement an audit-only candidate-specific runtime metadata check for candidate70, or
2. design a minimal model-facing trajectory / displacement / lane geometry surface with tests before any generation claim.

Any future GPU candidate should remain short and explicitly framed as exploratory until runtime motion control is connected and semantic review passes.
