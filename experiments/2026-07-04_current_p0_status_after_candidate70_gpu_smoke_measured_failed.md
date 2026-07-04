# Current P0 Status After Candidate70 GPU Smoke Measured Review

Date: 2026-07-04

## One-Line Status

Candidate70 P0 engineering/evaluation loop is now closed end-to-end: structural readiness, GPU candidate generation, post-GPU review pack, manual measured review, and prompt-video alignment evaluation all ran. The measured semantic result is failed, not passed. P0 semantic success is not claimed.

## Latest Candidate70 GPU / Review Evidence

Scenario:

- candidate70_night_cut_in_gpu_smoke

Prompt:

- night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.

Generated candidate video:

- outputs/driveloop/candidate70_night_cut_in_gpu_smoke/artifacts/candidate70_night_cut_in_gpu_smoke/iteration_00.mp4
- candidate video exists and was decodable into 8 sampled review frames

Post-GPU review gate:

- outputs/driveloop/post_gpu_review_gate/candidate70_night_cut_in_gpu_smoke/post_gpu_review_gate.json
- candidate_video_available: true
- initial video_semantic_claim: not_measured
- review_status: requires_manual_or_perception_review

Manual review output:

- outputs/driveloop/post_gpu_review_gate/candidate70_night_cut_in_gpu_smoke/manual_review_pack/manual_alignment_report.json
- status: measured
- source: manual_contact_sheet_review_v0
- semantic_success_claim_allowed: false

Prompt-video alignment evaluation:

- outputs/driveloop/prompt_video_alignment_eval/candidate70_night_cut_in_gpu_smoke/prompt_video_alignment_evaluation.json
- score: 0.361111
- passed: false
- video_semantic_claim: measured_failed

The outputs directory is intentionally git-ignored, so this markdown file records the tracked evidence summary.

## Manual Review Findings

Passed checks:

- artifact.video_available_and_decodable
- road_context.night_urban_multilane_or_lane_markings_visible
- control_binding.structural_evidence_referenced_without_overclaiming

Failed checks:

- object_presence.motorcycle_or_scooter_visible
- object_consistency.target_actor_trackable_across_frames
- maneuver.cut_in_from_left_toward_ego_visible
- temporal_motion.lateral_displacement_visible
- spatial_relation.starts_left_or_adjacent_lane_and_moves_toward_ego_path
- hdmap_alignment.lane_geometry_visually_consistent_with_scene

Interpretation:

The video candidate exists and shows a night urban road context, but the requested motorcycle/scooter target is not clearly visible and the requested left-to-ego cut-in maneuver is not visually measurable. Therefore the correct measured result is measured_failed.

## Code Fix In This Step

The manual review pack generator was updated so candidate70 night motorcycle cut-in prompts use the candidate70 semantic alignment protocol's 9 required checks instead of the older generic 4-check template. This fixes the incorrect lighting.daytime check for the night prompt.

Updated files:

- scripts/run_manual_alignment_review_pack.py
- tests/test_manual_alignment_review_pack.py

## Claim Boundary

Allowed claim:

- Candidate70 P0 evaluation loop ran end-to-end and produced a measured_failed semantic review.

Forbidden claims:

- Do not claim P0 semantic success.
- Do not set semantic_success_claim_allowed to true.
- Do not claim the generated video proves motorcycle cut-in / lane-change behavior.
- Do not treat tensor/runtime conditioning evidence as video semantic proof.

## Next Technical Direction

The next P0-success attempt should not merely re-run the same prompt. It should first diagnose why the generated video failed to expose a visible, trackable two-wheeler cut-in, then choose a stronger candidate/source condition or improve the target actor/box/HDMap conditioning path before another gated GPU smoke.
