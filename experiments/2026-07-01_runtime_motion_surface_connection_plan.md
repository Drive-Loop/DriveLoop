# Runtime Motion Surface Connection Plan

Date: 2026-07-01

## Scope

This note records the next non-GPU intervention plan for DriveLoop / DriveDreamer-2 runtime motion control surfaces.

It does not claim lane-change control, prompt-to-video semantic success, or paper-level semantic success.

## Current Evidence

The current runtime surface code audit is:

outputs/driveloop/runtime_surface_code_audit/motorcycle_refined_runtime_surface_code_audit.json

Current status:

- status: not_runtime_connected
- dataset velocity: available_in_converter
- dataset lane/HDMap: rasterized_image_hdmap_from_lane_geometry
- runtime condition inputs: image_hdmap_and_image_box_downsamplers
- direct motion runtime surface: not_observed

The converter writes velocity evidence from nuScenes annotations into label dictionaries, but the current DD2 runtime input path only observes:

- grounding_downsampler_input
- box_downsampler_input
- img_cond or video_cond
- prompt embedding

The runtime audit does not observe a direct trajectory, velocity, displacement, track_id, actor identity, or per-frame actor boxes surface.

## Claim Boundary

Allowed claims:

- Dataset-level velocity exists in converter code.
- Lane and road geometry are rasterized into image_hdmap.
- Static/spatial actor boxes are rasterized into image_box.
- DD2 runtime currently consumes downsampler surfaces, not an observed direct motion tensor.

Disallowed claims:

- Static image_box proves lane-change motion control.
- image_hdmap raster proves lane geometry override.
- Dataset velocity proves runtime velocity control.
- Runtime tensor hashes prove video semantics.
- The current motorcycle video is semantically successful.

The current semantic result remains:

- video_semantic_claim: measured_failed
- semantic_success_claim_allowed: false

## Recommended Non-GPU Connection Sequence

1. Preserve source motion metadata in audit-only paths.
2. Surface motion metadata in tester runtime audit.
3. Audit per-frame continuity.
4. Audit per-frame boxes before motion claims.
5. Only then consider a model-facing intervention.

## Next Implementation Candidate

The safest next implementation is an audit-only metadata extension:

- no GPU
- no training
- no model input change
- no semantic success claim

Target output fields:

- motion_metadata.velocities_available_in_batch: true or false
- motion_metadata.velocities_shape: shape or null
- motion_metadata.actor_labels_available_in_batch: true or false
- motion_metadata.actor_identity_available_in_batch: true or false
- motion_metadata.per_frame_actor_boxes3d_observed: true or false
- motion_metadata.claim: metadata_observed_only_not_runtime_control

Expected interpretation:

- If velocities_available_in_batch is false, the velocity data is lost before runtime.
- If true, velocity metadata is observable but still not consumed by the model.
- If actor identity is absent, lane-change motion cannot be tied to a persistent actor.
- If per-frame boxes are absent or unlinked, temporal motion control remains unverified.

## Required Validation

Before any commit:

- pytest -q tests
- git diff --check

Expected project status after this note:

- trajectory_runtime_surface_status: not_runtime_connected
- runtime_surface_code_audit_status: not_runtime_connected
- semantic_success_claim_allowed: false
