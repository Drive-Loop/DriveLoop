# Candidate70 8-Frame Actor Motion Coverage Fix

Date: 2026-07-04

## Summary

The measured_failed candidate70 GPU smoke showed that the generated video did not expose a clearly visible and trackable motorcycle cut-in. The first concrete engineering failure was incomplete actor motion override coverage: the old actor motion surface generated only 4 relative steps, while the DD2 candidate path uses 8 frames across 6 cameras.

## Fix

Updated the actor motion surface to generate 8 per-frame boxes3d entries for cut-in / lane-change motion instead of 4.

Updated tests:

- tests/test_actor_motion_surface.py

Updated runtime code:

- driveloop/actor_motion.py

## Non-GPU Verification

Audit-only run:

- scenario_id: candidate70_8frame_actor_motion_audit_only
- does_not_generate_video: true
- does_not_claim_semantic_success: true

Coverage result:

- total_rows: 48
- changed_boxes_rows: 48
- changed_image_box_rows: 48
- per_frame_append_rows: 48
- per_frame_append_entries: 48
- cam_front: 8
- cam_front_left: 8
- cam_front_right: 8
- cam_back: 8
- cam_back_left: 8
- cam_back_right: 8
- no_matching_frame_idx: 0

## Claim Boundary

This fixes a structural coverage bug only. It does not prove video semantic success and does not permit setting semantic_success_claim_allowed to true.

Remaining known gap:

- image_hdmap still reports no_verified_hdmap_override_source.
- A future GPU retry still requires explicit approval and post-GPU measured review.
