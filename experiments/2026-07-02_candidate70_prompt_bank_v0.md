# Candidate70 Prompt Bank v0

Date: 2026-07-02

## Scope

This note records a non-GPU prompt bank and candidate-support audit for candidate70.

It does not run GPU inference, generate video, modify business logic, accept any prompt for Generate, or claim prompt-to-video semantic success.

## Candidate

- candidate: candidate70
- candidate_id: nuscenes_train_candidate70_cam_front_9935
- scene: scene-1100
- map: singapore-hollandvillage
- target raw instance token: 21cdc9f24c614a6197fd044379697197
- category: vehicle.motorcycle

## Prompt Bank Summary

- prompt_count: 8
- accepted_for_generate_count: 0
- candidate70_allowed_count: 4
- candidate70_blocked_count: 4
- sampling_policy: controlled_stratified_prompt_sampling

## Candidate70-Supported Prompts

### c70_pos_001

- split: candidate70_positive
- support_expectation: candidate_supported
- accepted_for_generate: False
- prompt: night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.

### c70_pos_002

- split: candidate70_positive
- support_expectation: candidate_supported
- accepted_for_generate: False
- prompt: dark city intersection with a scooter changing lane from the left into the ego vehicle's path, panoramic multi-view video.

### c70_pos_003

- split: candidate70_positive
- support_expectation: candidate_supported
- accepted_for_generate: False
- prompt: nighttime urban road where a motorcycle or scooter performs a left-side lane-change or cut-in near the ego vehicle, panoramic multi-view video.

### c70_holdout_001

- split: evaluation_holdout
- support_expectation: candidate_supported_but_holdout
- accepted_for_generate: False
- prompt: dark urban intersection where a two-wheeled vehicle moves from the left lane toward the ego vehicle's lane, panoramic multi-view video.

## Candidate70-Blocked Prompts

### c70_neighbor_001

- split: near_neighbor
- support_expectation: partially_supported_or_requires_new_candidate
- blocked_reasons: candidate70_target_is_motorcycle_not_bicycle
- accepted_for_generate: False
- prompt: night urban street with a bicycle cutting in from the left toward the ego vehicle, panoramic multi-view video.

### c70_neighbor_002

- split: near_neighbor
- support_expectation: partially_supported_or_requires_new_candidate
- blocked_reasons: candidate70_target_is_motorcycle_not_car
- accepted_for_generate: False
- prompt: night urban street with a car changing lane from the left in front of the ego vehicle, panoramic multi-view video.

### c70_neg_001

- split: negative_control
- support_expectation: blocked_for_candidate70
- blocked_reasons: candidate70_is_night_not_daytime
- accepted_for_generate: False
- prompt: daytime urban road with a motorcycle performing a visible lane change from the left, panoramic multi-view video.

### c70_neg_002

- split: negative_control
- support_expectation: blocked_for_candidate70
- blocked_reasons: prompt_requests_no_motorcycle_or_scooter
- accepted_for_generate: False
- prompt: night urban street with no motorcycle or scooter, only parked cars beside the ego vehicle, panoramic multi-view video.

## Interpretation

The prompt bank separates candidate70-compatible prompts, nearby category controls, and negative controls.

Candidate70 remains compatible only with prompts matching its night motorcycle/scooter lane-change or cut-in support.

No prompt in this bank is automatically accepted for Generate. A user-confirmed accepted prompt is still required before any generation step.

## Claim Boundary

Allowed claims:

- Candidate70 prompt-bank v0 was generated as a non-GPU artifact.
- Candidate70 prompt-bank support audit allows four prompts and blocks four prompts.
- The blocked prompts are useful controls for category, lighting, and target-presence mismatch.
- The bank supports controlled prompt variation for future training and experiments.

Disallowed claims:

- Prompt-bank generation proves runtime motion control.
- Prompt-bank support audit proves lane-change or cut-in control.
- Prompt-bank support audit proves video semantic success.
- Any prompt has been accepted for Generate.
- Any GPU run is approved by this note.

## Recommended Status

- prompt_bank_created: true
- prompt_bank_candidate70_allowed_count: 4
- prompt_bank_candidate70_blocked_count: 4
- accepted_for_generate_count: 0
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false
- gpu_requires_separate_readiness_gate: true

## Artifacts

- prompt bank: `outputs/driveloop/prompt_bank/candidate70_prompt_bank_v0.json`
- support audit: `outputs/driveloop/prompt_bank/candidate70_prompt_bank_support_audit_v0.json`
