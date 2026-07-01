# Tiny Real Actor Identity Runtime Audit

Date: 2026-07-02

## Scope

This note records a non-GPU DD2 audit-only check for real nuScenes actor identity metadata passthrough.

It does not claim runtime motion control, lane-change control, prompt-to-video semantic success, or paper-level semantic success.

## Setup

A tiny 8-frame CAM_FRONT audit dataset was created at:

`outputs/driveloop/tiny_real_actor_identity_runtime_dataset/cam_front_8/v0.0.1`

The dataset reuses real mini `images` and `hdmaps`.

The first 8 real mini label records were patched with real nuScenes identity fields recovered from:

- `nusc.get_sample_data(cam_token)`
- `cam_box.token`
- `sample_annotation.instance_token`

Before patching, the first 8 records were checked and all processed `boxes3d` counts matched the nuScenes API camera-visible box counts.

## Artifacts

Actor identity surface audit:

`outputs/driveloop/tiny_real_actor_identity_runtime_audit/actor_identity_surface_audit.json`

DD2 backend audit-only summary:

`outputs/driveloop/tiny_real_actor_identity_runtime_audit/tiny_real_actor_identity_runtime_audit/backend_audit_only_summary.json`

DD2 runtime input audit:

`outputs/driveloop/tiny_real_actor_identity_runtime_audit/tiny_real_actor_identity_runtime_audit/dd2_runtime_input_audit_00.json`

Tiny real-token audit config:

`dreamer-train/projects/DriveDreamer2/configs/drivedreamer2_img_cond_tiny_real_actor_identity_audit_local.py`

## Observed Result

The tiny real-token label subset includes:

- `sample_annotation_tokens`
- `instance_tokens`
- `actor_identity_categories`

Actor identity surface audit reported:

- `status`: `identity_available_in_processed_labels`
- `actor_identity_available_in_processed_labels`: `true`
- processed identity fields: `instance_tokens`, `sample_annotation_tokens`

DD2 runtime metadata audit reported:

- `motion_metadata.available`: `true`
- `velocities_available_in_batch_any`: `true`
- `boxes3d_available_in_batch_any`: `true`
- `actor_identity_available_in_batch_any`: `true`
- `actor_identity_fields_preview`: `instance_tokens`, `sample_annotation_tokens`
- `per_frame_actor_boxes3d_observed_any`: `false`
- `claim`: `metadata_observed_only_not_runtime_control`

## Interpretation

This verifies that real nuScenes `sample_annotation_tokens` and `instance_tokens`, when present in processed label records, can be surfaced through DD2 transform/runtime audit-only metadata.

This is stronger than the synthetic-token audit because the identity tokens are recovered from raw nuScenes metadata using the camera sample token.

## Claim Boundary

Allowed claims:

- Real nuScenes actor identity tokens can be patched into a tiny processed real-label subset.
- DD2 audit-only runtime metadata can observe actor identity field names when those fields exist in processed labels.
- Velocity and boxes3d metadata remain observable in the same audit-only path.

Disallowed claims:

- Full real mini processed labels have been rebuilt.
- Runtime motion control is connected.
- Per-frame actor boxes3d are verified.
- Lane-change control is verified.
- Prompt-to-video semantic success is achieved.
- The motorcycle lane-change case is semantically successful.

## Next Non-GPU Work

1. Generalize the real-token patch into a small reproducible helper or converter-side validation path.
2. Audit whether per-frame boxes3d can be grouped by persistent `instance_tokens`.
3. Add an explicit per-frame actor-track audit before any runtime motion intervention.
4. Only after actor identity and per-frame actor boxes are observable should runtime motion intervention be designed.
