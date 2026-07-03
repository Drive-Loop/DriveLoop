# Current P0 Status After Local-Map-Vector HDMap Replacement Gate

Date: 2026-07-03

This snapshot is the detailed handoff companion to HANDOFF_DRIVELOOP.md. It records the current candidate70 P0 state after source-bound actor motion and local-map-vector HDMap lane geometry replacement were connected to the DD2 runtime/audit surfaces.

## One-Line Status

Candidate70 structural runtime / input readiness is now addressed, but semantic success is still not claimed. The default readiness gate is blocked only by semantic_success_claim_not_allowed.

## Verified Evidence

Latest non-GPU verification from the server terminal:

- pytest -q tests: 239 passed, 1 warning
- readiness_status: blocked
- gpu_smoke_allowed: false
- blockers: semantic_success_claim_not_allowed
- runtime_motion_control_connected: true
- true_lane_geometry_replacement_available: true
- local_map_vector_hdmap_reaches_grounding_surface: true
- local_map_vector_hdmap_lane_geometry_override_verified: true
- semantic_success_claim_allowed: false

The warning was a TensorFlow / NumPy deprecation warning and was not related to DriveLoop logic.

## Source-Bound Actor Motion Evidence

The actor motion surface is no longer only a relative-frame structural append. It is connected through source-bound sample identity.

Observed evidence:

- source_bound_actor_motion_audit_exists: true
- source_bound_actor_motion_runtime_connected: true
- source_bound_actor_motion_sample_identity_verified: true
- source_bound_actor_motion_boxes3d_changed: true
- source_bound_actor_motion_image_box_changed: true
- applied_per_frame_append_count: 24
- sample_identity_applied_count: 24
- override_changed_counts: boxes3d 24, image_box 24, scene_description 48

Frame mapping:

- mode: source_bound_relative_step_to_sample_identity
- source_identity_count: 48
- input_per_frame_count: 4
- mapped_entry_count: 24
- unmapped_relative_frame_idx: []

Boundary:

- This is structural runtime-conditioning evidence.
- This is not GPU video evidence.
- This is not semantic success evidence.
- Velocity or displacement tensor control is not claimed.

## Local-Map-Vector HDMap Evidence

The HDMap work moved beyond the previous dry-run raster evidence.

Observed evidence:

- local_map_vector_hdmap_audit_exists: true
- status: local_map_vector_lane_geometry_replacement_reaches_grounding_surface
- reaches_grounding_surface: true
- true_lane_geometry_replacement_available: true
- hdmap_lane_geometry_override_verified: true
- schema_version: candidate70_hdmap_lane_geometry_replacement_surface_audit.v1

Candidate operation:

- operation: offset_lane_divider_local_map_vector_before_camera_projection
- target_type_name: lane_divider
- coordinate_frame: ego_aligned_local_map_patch
- local_x_offset_m: 0.0
- local_y_offset_m: -1.5
- projection_stage: before_camera_extrinsic_and_intrinsic_projection
- modified_visible_count: 6 for the recorded frame-0 candidate source
- candidate source sha256: 7afd1307c3a2e9b3912cda5b9c7cb985f3f4dc6abab3143b6d14de1df9030835

Surface changes:

- image_hdmap_override_changed: true
- grounding_downsampler_input_changed: true
- box_downsampler_input_changed: false
- input_image_changed: false

Boundary:

- This is not the old dry-run pixel/raster shift claim.
- This is local-map-vector lane geometry replacement before camera projection.
- This is not GPU approval.
- This is not generated-video semantic evidence.
- This is not proof that the generated video performs a lane change.

## Gate Interpretation

The gate is intentionally still blocked. The remaining blocker is correct and should not be bypassed.

Current interpretation:

- Runtime motion control structural evidence is available.
- True lane-geometry replacement structural evidence is available.
- Semantic success evidence is not available.
- GPU smoke is not allowed by default.

The right next stage is semantic / alignment evaluation design, then explicit user approval before any GPU smoke.

## Current Working Tree Scope

Tracked files intentionally modified in this phase:

- dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_tester.py
- driveloop/backends/drivedreamer2.py
- driveloop/dd2_override.py
- scripts/run_candidate70_gpu_readiness_gate.py
- tests/test_actor_motion_surface.py
- tests/test_candidate70_gpu_readiness_gate.py
- tests/test_dd2_override.py

New files intentionally added in this phase:

- experiments/2026-07-03_p0_candidate70_source_bound_actor_motion_identity_fix.md
- experiments/2026-07-03_p0_candidate70_local_map_vector_hdmap_replacement_gate.md
- scripts/run_candidate70_hdmap_lane_geometry_replacement_builder.py
- scripts/run_candidate70_hdmap_lane_geometry_replacement_surface_audit.py
- tests/test_candidate70_hdmap_lane_geometry_replacement_builder.py
- tests/test_candidate70_hdmap_lane_geometry_replacement_surface_audit.py

This snapshot file is also new:

- experiments/2026-07-03_current_p0_status_after_local_map_vector_hdmap_replacement_gate.md

## Next Step

Do not run GPU automatically. First define the measured semantic / alignment evaluation that would justify changing semantic_success_claim_allowed from false to true.
