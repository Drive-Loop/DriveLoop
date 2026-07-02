# Candidate70 Runtime Metadata Alignment Audit

Date: 2026-07-02

## Scope

This note records a non-GPU candidate-level runtime metadata alignment audit for candidate70.

It does not claim runtime motion control, trajectory control, lane-change control, prompt-to-video semantic success, or paper-level success.

## Artifact

Audit output:

- outputs/driveloop/candidate_runtime_metadata_audit/candidate70/candidate70_runtime_metadata_alignment_audit.json

## Candidate

- candidate: candidate70
- candidate_id: nuscenes_train_candidate70_cam_front_9935
- split: train
- front_start_index: 9935
- scene: scene-1100
- selected_view: cam_front
- target_raw_instance_token: 21cdc9f24c614a6197fd044379697197

## Observed Result

Summary:

- frame_count: 8
- all_frames_have_processed_target: true
- all_frames_have_single_processed_target: true
- all_frames_have_raw_target: true
- processed_identity_fields_present_any: false
- processed_velocity_available_all: true
- raw_velocity_available_all: true
- processed_delta_x: 9.9201
- processed_delta_z: -15.3396
- raw_global_delta_x: 8.458
- raw_global_delta_y: 13.501
- alignment_status: candidate_level_metadata_aligned_not_runtime_control

## Interpretation

Candidate70 has candidate-level processed motion metadata and raw nuScenes identity alignment across all audited frames.

However, processed train labels still do not carry persistent actor identity fields. The raw identity is recovered by looking back into nuScenes metadata, not by a model-facing runtime input.

Velocity metadata is observable, but this audit does not show velocity being consumed as a DD2 model input.

## Claim Boundary

Allowed claims:

- Candidate70 has candidate-level processed box and velocity metadata across all audited frames.
- Candidate70 raw motorcycle identity can be recovered across all audited frames.
- Candidate70 metadata alignment is stronger than source-only visibility evidence.

Disallowed claims:

- Candidate70 verifies runtime motion control.
- Candidate70 verifies lane-change or cut-in control.
- Candidate70 proves trajectory, displacement, or velocity is consumed by DD2 runtime.
- Candidate70 proves prompt-to-video semantic success.
- Raw identity recovery or processed metadata proves generated video semantics.

## Recommended Status

- candidate70_metadata_alignment_status: candidate_level_metadata_aligned_not_runtime_control
- candidate_level_processed_motion_metadata_observed: true
- candidate_level_raw_identity_recovered: true
- processed_labels_include_persistent_identity: false
- runtime_motion_control_connected: false
- trajectory_tensor_available: false
- velocity_consumed_as_model_input: false
- semantic_success_claim_allowed: false

## Next Step

Do not train and do not run long GPU jobs.

The next non-GPU step is to decide whether to preserve candidate70 identity fields in processed labels or expose a model-facing trajectory / displacement surface with tests. Until then, candidate70 remains a strong source/prompt/metadata candidate but not a verified runtime-control candidate.
