# Synthetic Actor Identity Label Verification

Date: 2026-07-01

## Scope

This note records a non-GPU schema verification for actor identity labels in DriveLoop / DriveDreamer-2.

It does not claim that the existing nuScenes mini processed labels have been rebuilt or fixed.

It does not claim runtime motion control, lane-change control, prompt-to-video semantic success, or paper-level semantic success.

## What Was Verified

A synthetic processed label file was created with:

- sample_annotation_tokens
- instance_tokens
- boxes3d
- velocities
- labels3d
- ori_labels3d
- attributes

The actor identity surface audit was run on that synthetic label file.

Observed result:

- status: identity_available_in_processed_labels
- actor_identity_available_in_processed_labels: true
- actor_identity_available_upstream: true
- processed_identity_fields: sample_annotation_tokens, instance_tokens
- blockers: none
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Interpretation

This verifies that the actor identity audit can detect persistent actor identity fields when they exist in processed label records.

It also verifies that the new converter schema is directionally usable for future converted labels.

## Current Limitation

The existing processed nuScenes mini labels still do not contain persistent actor identity fields.

Current real mini labels still show only scene/sample/camera token surfaces:

- scene_token
- sample_token
- cam_token

They do not yet show:

- sample_annotation_tokens
- instance_tokens
- track_ids

Therefore, the real project status remains:

- actor identity available upstream: true
- actor identity available in current processed labels: false
- runtime motion control connected: false
- semantic success claim allowed: false

## Next Non-GPU Work

1. Rebuild or patch a tiny processed label subset with the updated converter schema.
2. Run actor identity surface audit on that subset.
3. If identity appears in real processed labels, pass it through DD2 transform as audit-only metadata.
4. Only after actor identity and per-frame boxes are observable should runtime motion intervention be considered.

## Validation

Before any commit:

- pytest -q tests
- git diff --check
