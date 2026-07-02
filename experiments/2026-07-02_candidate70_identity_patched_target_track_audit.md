# Candidate70 Identity-Patched Target Track Audit

Date: 2026-07-02

## Scope

This note records a non-GPU, audit-only target-track check for candidate70 after patching raw nuScenes identity into a derived label dataset.

It does not modify the original processed labels, does not change DD2 model inputs, and does not claim runtime motion control, lane-change control, prompt-to-video semantic success, or paper-level success.

## Artifacts

Audit-only patched labels:

- outputs/driveloop/candidate70_identity_patched_runtime_dataset/cam_front_8/v0.0.1/labels/data.pkl
- outputs/driveloop/candidate70_identity_patched_runtime_dataset/cam_front_8/v0.0.1/labels/summary.json

Actor-track audit:

- outputs/driveloop/actor_track_surface_audit/candidate70_identity_patched_actor_track_surface_audit.json

Filtered target-track summary:

- outputs/driveloop/actor_track_surface_audit/candidate70_identity_patched_target_track_summary.json

## Candidate

- candidate: candidate70
- candidate_id: nuscenes_train_candidate70_cam_front_9935
- scene: scene-1100
- selected_view: cam_front
- target_raw_instance_token: 21cdc9f24c614a6197fd044379697197
- category: vehicle.motorcycle

## Identity-Patch Result

The derived audit-only label dataset patched raw nuScenes identity into the target motorcycle box for the 8 candidate70 CAM_FRONT frames.

Summary:

- identity_patch_dataset_created: true
- all_frames_have_raw_target: true
- all_frames_have_patched_identity: true
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Target-Track Result

Filtered target-track summary:

- status: target_track_observed
- non_null_track_count: 1
- null_identity_track_present: true
- observation_count: 8
- unique_frame_count: 8
- frame_indices: 144, 147, 150, 153, 156, 159, 162, 165
- category: vehicle.motorcycle
- first_center_xyz: [-10.8272, 0.1872, 24.4066]
- last_center_xyz: [-0.9071, 0.5459, 9.067]
- first_velocity_xy: [5.584, -8.2843]
- last_velocity_xy: [5.6932, -9.6478]
- processed_delta_x: 9.9201
- processed_delta_z: -15.3396

The actor-track audit also surfaced a null identity track from unpatched boxes. That null track is not a valid actor identity and must not be counted as target actor evidence.

## Interpretation

Candidate70 can form a stable 8-frame target motorcycle track when raw nuScenes identity is preserved in an audit-only derived label dataset.

This strengthens the evidence that identity preservation is feasible for candidate-level audit and future converter work.

It still does not prove runtime motion control. The identity-patched track is metadata evidence only, not a model-facing trajectory, displacement, velocity, or HDMap lane geometry control surface.

## Claim Boundary

Allowed claims:

- Candidate70 target motorcycle identity can be patched audit-only into derived labels.
- Candidate70 has one valid non-null target track across all 8 audited frames.
- Candidate70 target track has consistent processed box and velocity metadata.
- Null identity tracks are present and must be excluded from valid actor identity claims.

Disallowed claims:

- Candidate70 verifies runtime motion control.
- Candidate70 verifies lane-change or cut-in control.
- Candidate70 proves trajectory, velocity, or displacement is consumed by DD2 runtime.
- Candidate70 proves HDMap lane geometry override.
- Candidate70 proves prompt-to-video semantic success.
- Audit-only identity-patched labels prove generated video semantics.

## Recommended Status

- candidate70_identity_patch_dataset_created: true
- candidate70_target_track_status: target_track_observed
- candidate70_target_track_covers_all_8_frames: true
- candidate70_non_null_track_count: 1
- null_identity_track_present: true
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Do not train and do not run long GPU jobs.

A safe next implementation step is to preserve raw nuScenes instance and annotation tokens in converter output labels, with tests proving that null identity tracks are filtered out and target actor tracks can be reconstructed without raw metadata lookup.

A higher-risk next step is to design a model-facing trajectory / displacement surface, but that should happen only after the identity-preservation path is tested and documented.
