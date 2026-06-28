# Motorcycle Feedback DD2 Audit-Only Run

Date: 2026-06-28

## Purpose

This note records a DD2 backend audit-only run after manual review found that the motorcycle smoke video failed the `spatial_relation.left_lane_change` check.

The goal was to verify that the refined prompt and condition enter DD2 audit-only runtime evidence without running diffusion or claiming video semantic correction.

## Input

Refined prompt:

`daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.`

Scenario:

`motorcycle_manual_feedback_dd2_audit_only`

Summary artifact:

`outputs/driveloop/motorcycle_manual_feedback_dd2_audit_only/motorcycle_manual_feedback_dd2_audit_only/backend_audit_only_summary.json`

## Audit Result

- `dd2_audit_only`: true
- video generated: false
- `dd2_tensor_control_ready`: true

Override changed counts:

- `boxes3d`: 48
- `image_box`: 48
- `scene_description`: 48

Runtime tensor hashes:

- `prompt_embed`: `48abbf428b9e59bc175a28e7fe8d9bac6465cefd4cdfa536aad37a1b02855a41`
- `box_downsampler_input`: `464e16c6a3980b3b8fa73afa3b9ba9bd6d705cd382745b747fd9482ae6194299`
- `grounding_downsampler_input`: `5d867839d26b9f9eab319f5c364569bc05891d4f0a92e95b19c82bca86a9717d`
- `img_cond`: `28858b17d0499c9acc891c9e30e4de59b690202b1e399d206c7f9753171b6642`

## What This Proves

- The refined prompt enters DD2 audit-only runtime.
- The executable condition requests a motorcycle actor.
- DD2 override audit changes `scene_description`, `boxes3d`, and derived `image_box`.
- Runtime audit captures prompt and structural tensor signatures.
- No diffusion/video generation was run.

## What This Does Not Prove

- It does not prove that a generated video would show a lane-change maneuver.
- It does not prove trajectory or temporal motion tensor control.
- It does not prove HDMap override.
- It does not prove prompt-video semantic success.

## Claim Boundary

Allowed wording:

> Manual alignment feedback was propagated into a refined DD2 audit-only condition, and DD2 runtime audit recorded changed text/box structural evidence.

Disallowed wording:

> The lane-change video semantics are fixed.

> DD2 trajectory tensors are controlled.

> The refined prompt has been visually validated.

## Recommended Next Step

Before any new GPU smoke, compare this refined audit-only run against the earlier motorcycle audit-only or smoke evidence to confirm exactly which runtime hashes changed. If GPU is used later, keep it short and treat the output as requiring visual/perception review.
