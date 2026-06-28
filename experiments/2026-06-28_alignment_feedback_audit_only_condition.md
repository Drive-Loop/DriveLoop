# Alignment Feedback Audit-Only Condition

Date: 2026-06-28

## Purpose

This note records an audit-only preparation step after manual review found that the motorcycle smoke video failed the left-lane-change prompt relation.

The goal is to verify that the failed manual-review check can be converted into a refined prompt and DD2 condition trace without running DD2 diffusion or claiming video semantic correction.

## Input Evidence

Manual review result:

`outputs/driveloop/prompt_video_alignment_eval/motorcycle_manual_review_v0/prompt_video_alignment_evaluation.json`

Manual review conclusion:

- `video_semantic_claim`: `measured_failed`
- score: `0.65`
- failed required check: `spatial_relation.left_lane_change`

## Audit-Only Preparation

Script:

`scripts/prepare_alignment_feedback_audit_only.py`

Command output:

`outputs/driveloop/alignment_feedback_audit_only/motorcycle_manual_review_feedback_audit_only/alignment_feedback_audit_only_summary.json`

The script reads the failed check from the manual review report and prepares a refined DriveLoop/DD2 condition.

## Observed Refined Condition

Source prompt:

`daytime urban road with a motorcycle`

Refined prompt:

`daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.`

Scene specification includes:

- object: `motorcycle`
- relation: `left`
- motion primitive: `lane_change`
- lighting: `daytime`

DD2 executable condition includes:

- actor control: `motorcycle`
- relation control: `left`
- motion control: `lane_change`
- trace metadata with `alignment_feedback`

Alignment feedback trace:

- status: `measured_failed`
- control level: `text_feedback_only`
- failed check: `spatial_relation.left_lane_change`

## What This Proves

- The real manual-review failure can be converted into structured DriveLoop feedback.
- The feedback can refine the prompt.
- The refined prompt can be grounded into scene specification fields.
- The refined DD2 condition can carry the alignment feedback in `trace_metadata`.

## What This Does Not Prove

- It does not run DD2 diffusion.
- It does not inspect new video pixels.
- It does not prove that a new generated video would show lane change.
- It does not prove trajectory tensor control.
- It does not upgrade `alignment_feedback` beyond `text_feedback_only`.

## Claim Boundary

Allowed wording:

> Manual review feedback was converted into an audit-only refined DD2 condition containing a lane-change motion primitive and an alignment feedback trace.

Disallowed wording:

> The lane-change failure has been fixed in generated video.

> Alignment feedback controls DD2 trajectory tensors.

> The refined condition proves semantic correction.

## Recommended Next Step

Before any new GPU generation, run a DD2 backend audit-only check with this refined condition and confirm the runtime audit still clearly separates:

- text prompt changes
- structural tensor changes
- fixed mini dataset image/HDMap conditioning
- unverified trajectory or temporal motion control
