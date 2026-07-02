# Candidate70 Source Visibility Audit

Date: 2026-07-02

## Scope

This note records a non-GPU source visibility audit for candidate70.

It does not claim prompt-to-video semantic success, runtime motion control, HDMap lane geometry override, or paper-level success.

## Candidate

- candidate: candidate70
- split: train
- front_start_index: 9935
- scene: scene-1100
- map: singapore-hollandvillage
- scene description: Night, peds in sidewalk, peds cross crosswalk, scooter, PMD, difficult lighting

## Source Visibility Evidence

A source contact sheet was generated at:

- outputs/driveloop/source_visibility_audit/motorcycle_lane_change_train_candidate_70_images/candidate_70_source_cam_front_contact_sheet.jpg

The contact sheet shows a red-projected raw nuScenes 3D box tracking the same visible motorcycle / scooter target across all audited CAM_FRONT frames.

Observed source behavior:

- the target is visible in all audited frames
- the target starts from the left side of the scene
- the target approaches the ego/front camera region
- the target moves laterally toward the center / lower-front area of the image
- the motion is visually stronger than candidate38 for a left-to-front cut-in / crossing-style event

## Identity Evidence

Raw nuScenes recovery found the same target instance across all audited frames:

- instance_token: 21cdc9f24c614a6197fd044379697197
- category: vehicle.motorcycle

Machine summary:

- all_frames_have_processed_target: true
- all_frames_have_raw_target: true
- all_frames_project_raw_box: true

## Motion Evidence

Processed CAM_FRONT target centers showed:

- processed_delta_x: 9.9201
- processed_delta_z: -15.3396

Interpretation:

Candidate70 has strong source-level lateral and approach motion. This is stronger than candidate38, whose lateral motion was weak.

## Claim Boundary

Allowed claims:

- Candidate70 has strong source visibility evidence for a motorcycle / scooter target.
- The same raw nuScenes motorcycle instance is recoverable across all audited frames.
- Candidate70 has stronger source-level left-to-front cut-in / crossing-style motion evidence than candidate38.
- Candidate70 is a stronger candidate for further non-GPU candidate-selection and runtime-surface audits.

Disallowed claims:

- Candidate70 verifies prompt-to-video semantic success.
- Candidate70 verifies runtime motion control.
- Candidate70 verifies HDMap lane geometry override.
- Candidate70 proves lane-change into the ego lane.
- Candidate70 proves trajectory, velocity, or displacement is consumed by DD2 runtime.
- Tensor, metadata, source visibility, or video generation alone proves video semantics.

## Recommended Status

- candidate70_motorcycle_identity_verified: true
- candidate70_source_visibility_verified: true
- candidate70_source_motion_strength: stronger_than_candidate38
- candidate70_lane_change_source_support: partial_visual_support_not_map_verified
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Use candidate70 as the stronger non-GPU audit target.

Before any GPU run, verify whether candidate selection can surface candidate70 from an accepted prompt without hidden defaults, and continue auditing whether any trajectory, velocity, displacement, or HDMap condition is runtime-consumed.
