# Tiny Actor Identity Runtime Audit

Date: 2026-07-02

## Scope

This note records a non-GPU DD2 audit-only check for actor identity metadata passthrough.

It does not claim true nuScenes persistent actor identity has been rebuilt in the real mini processed labels.

It does not claim runtime motion control, lane-change control, prompt-to-video semantic success, or paper-level semantic success.

## Setup

A tiny 8-frame CAM_FRONT audit dataset was created at:

`outputs/driveloop/tiny_actor_identity_runtime_dataset/cam_front_8/v0.0.1`

The dataset reuses real mini `images` and `hdmaps`, but patches the first 8 real mini label records with synthetic audit-only fields:

- `sample_annotation_tokens`
- `instance_tokens`

These tokens are synthetic placeholders added to real processed label records for schema/runtime metadata passthrough verification only.

## Artifacts

Actor identity surface audit:

`outputs/driveloop/tiny_actor_identity_runtime_audit/actor_identity_surface_audit.json`

DD2 backend audit-only summary:

`outputs/driveloop/tiny_actor_identity_runtime_audit/tiny_actor_identity_runtime_audit/backend_audit_only_summary.json`

DD2 runtime input audit:

`outputs/driveloop/tiny_actor_identity_runtime_audit/tiny_actor_identity_runtime_audit/dd2_runtime_input_audit_00.json`

Tiny audit config:

`dreamer-train/projects/DriveDreamer2/configs/drivedreamer2_img_cond_tiny_actor_identity_audit_local.py`

## Observed Result

Actor identity surface audit reported:

- `status`: `identity_available_in_processed_labels`
- `actor_identity_available_in_processed_labels`: `true`
- `actor_identity_available_upstream`: `true`
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

This verifies that when processed label records contain actor identity fields, DD2 transform/runtime audit-only evidence can surface those fields in `motion_metadata`.

This closes the narrow audit-only passthrough question for patched labels.

## Claim Boundary

Allowed claims:

- A tiny patched real-label subset can expose `sample_annotation_tokens` and `instance_tokens` to actor identity surface audit.
- DD2 audit-only runtime metadata can observe actor identity field names when those fields exist in processed labels.
- Velocity and boxes3d metadata remain observable in the same audit-only runtime metadata.

Disallowed claims:

- Current real mini processed labels contain true persistent actor identity.
- Synthetic patched tokens are true nuScenes actor identity.
- Runtime motion control is connected.
- Per-frame actor boxes3d are verified.
- Lane-change control is verified.
- Prompt-to-video semantic success is achieved.
- The motorcycle lane-change case is semantically successful.

## Next Non-GPU Work

1. Rebuild or patch a tiny processed label subset using real nuScenes `sample_annotation_tokens` and `instance_tokens`, not synthetic placeholders.
2. Verify that real identity fields appear in actor identity surface audit.
3. Verify that real identity fields appear in DD2 audit-only runtime metadata.
4. Investigate whether per-frame actor boxes3d can be grouped by persistent actor identity.
5. Only after actor identity and per-frame actor boxes are observable should runtime motion intervention be designed.
