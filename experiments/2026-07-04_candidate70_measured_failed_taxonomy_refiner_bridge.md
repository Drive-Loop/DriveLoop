# Candidate70 Measured-Failed Taxonomy / Refiner Bridge

Date: 2026-07-04

## Summary

The candidate70 night motorcycle cut-in GPU smoke remains a measured semantic failure, but the failure is now connected to DriveLoop's diagnostic/refinement layer instead of remaining only in a manual review report.

This step does not claim semantic success and does not approve a new GPU run.

## Input Evidence

Prompt-video alignment evaluation:

- scenario_id: candidate70_night_cut_in_gpu_smoke
- video_semantic_claim: measured_failed
- alignment_passed: false

Manual review failed required checks include:

- object_presence.motorcycle_or_scooter_visible
- object_consistency.target_actor_trackable_across_frames
- maneuver.cut_in_from_left_toward_ego_visible
- temporal_motion.lateral_displacement_visible
- spatial_relation.starts_left_or_adjacent_lane_and_moves_toward_ego_path
- hdmap_alignment.lane_geometry_visually_consistent_with_scene

Candidate support was rechecked with the prompt-compatible candidate70 audit:

- candidate_support_allowed: true
- candidate_support_status: allowed

Therefore source candidate support is not treated as the primary blocker for this failure.

## Code Change

Updated the failure taxonomy script so the default candidate70 inputs target the latest measured-failed GPU smoke and the prompt-compatible candidate70 source audit.

Expanded taxonomy labels for candidate70 semantic failures:

- object_identity_failed
- motorcycle_identity_failed
- tracking_identity_failed
- low_visual_confidence
- cut_in_motion_failed
- lane_change_motion_failed
- lateral_motion_failed
- spatial_relation_failed
- hdmap_alignment_failed

Expanded refiner prompt/condition feedback for the candidate70 semantic protocol checks while preserving the legacy motorcycle alignment behavior.

## Non-GPU Verification

Focused test set:

- tests/test_alignment_failure_taxonomy.py
- tests/test_refiner.py
- tests/test_prompt_video_alignment_eval_script.py
- tests/test_evaluators.py
- tests/test_manual_alignment_review_pack.py
- tests/test_candidate70_semantic_alignment_protocol.py
- tests/test_candidate70_gpu_readiness_gate.py
- tests/test_post_gpu_review_gate.py

Observed result:

- 40 passed

Diff check:

- git diff --check passed

## Claim Boundary

Allowed claim:

- Candidate70 measured_failed review can now drive taxonomy labels and rule-based refinement feedback.
- Candidate support is not the primary blocker for the latest candidate70 failure.

Forbidden claims:

- Do not claim semantic success.
- Do not set semantic_success_claim_allowed to true.
- Do not claim the generated video contains a visible motorcycle cut-in.
- Do not treat source support, tensor evidence, HDMap evidence, or taxonomy output as video semantic proof.
- Do not run another GPU smoke without explicit approval and a post-GPU review path.

## Next Technical Direction

The next non-GPU step should connect this taxonomy/refiner bridge into a repeatable closed-loop artifact:

1. measured_failed alignment evaluation
2. failure taxonomy
3. refinement proposal
4. audit-only runtime/source/condition check
5. explicit approval before any GPU retry

The most important missing paper-level pieces remain automatic perception evaluation and a true multi-round regenerate loop.
