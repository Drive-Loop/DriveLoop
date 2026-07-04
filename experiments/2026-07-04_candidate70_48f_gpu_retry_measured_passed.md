# Candidate70 48f GPU retry measured-passed result

## Summary

This note records the first candidate70 48-frame source-bound GPU retry result that reached a measured-passed prompt-video alignment review.

This is a P0 successful candidate artifact, not a complete paper Section 4 experiment suite.

## Scenario

- scenario_id: `candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z`
- date: 2026-07-04
- backend: DriveDreamer-2 frozen runtime via DriveLoop outer-loop interface
- run type: one-shot GPU retry after explicit user approval
- training: not performed
- generation count: one short retry
- semantic success source: explicit manual review report plus prompt-video alignment evaluator

## Key Artifacts

- video: `outputs/driveloop/candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z/artifacts/candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z/iteration_00.mp4`
- manual review report: `outputs/driveloop/post_gpu_review_gate/candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z/manual_review_pack/manual_alignment_report.json`
- prompt-video alignment evaluation: `outputs/driveloop/prompt_video_alignment_eval/candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z/prompt_video_alignment_evaluation.json`
- GPU retry approval: `outputs/driveloop/gpu_retry_approval/candidate70_gpu_retry_approval.json`
- readiness gate: `outputs/driveloop/gpu_smoke_readiness/candidate70_gpu_readiness_gate.json`
- override audit: `outputs/driveloop/candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z/artifacts/candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z/dd2_override_audit_00.jsonl`

## Approval And Gate

- approval_status: `approved_for_one_short_gpu_retry`
- approved_for_candidate70_gpu_retry: `True`
- approved_by: `tangzimo`
- approval_is_not_semantic_success: `True`
- retry_gate_status: `allowed_after_explicit_user_approval`
- retry_gate_allowed: `True`
- retry_gate_requires_post_gpu_review: `True`
- retry_gate_does_not_claim_semantic_success: `True`

## Structural Runtime Evidence

The retry was run after the non-GPU structural gate verified full source-bound actor-motion coverage.

- source-bound actor motion full coverage verified: `True`
- expected coverage rows: `48`
- override entry count: `48`
- boxes3d changed count: `48`
- image_box changed count: `48`
- per-frame append count: `48`
- sample identity applied count: `48`
- no matching frame idx count: `0`

The retry override audit confirms:

- override rows: `48`
- accepted motorcycle entries: `48`
- missing sample identity entries: `0`

## Manual Review Result

The manual report is measured and all required candidate70 checks passed.

- manual report status: `measured`
- reviewer: `tangzimo`
- required checks passed: `9 / 9`

Passed required checks:

- `artifact.video_available_and_decodable`
- `object_presence.motorcycle_or_scooter_visible`
- `object_consistency.target_actor_trackable_across_frames`
- `maneuver.cut_in_from_left_toward_ego_visible`
- `temporal_motion.lateral_displacement_visible`
- `spatial_relation.starts_left_or_adjacent_lane_and_moves_toward_ego_path`
- `road_context.night_urban_multilane_or_lane_markings_visible`
- `hdmap_alignment.lane_geometry_visually_consistent_with_scene`
- `control_binding.structural_evidence_referenced_without_overclaiming`

## Prompt-Video Alignment Evaluation

- video_semantic_claim: `measured_passed`
- score: `0.916667`
- passed: `True`
- alignment_measured: `1.0`
- required check count: `9.0`
- passed required check count: `9.0`

Per-check metrics:

- artifact.video_available_and_decodable: `1.0`
- object_presence.motorcycle_or_scooter_visible: `0.9`
- object_consistency.target_actor_trackable_across_frames: `0.9`
- maneuver.cut_in_from_left_toward_ego_visible: `0.9`
- temporal_motion.lateral_displacement_visible: `0.9`
- spatial_relation.starts_left_or_adjacent_lane_and_moves_toward_ego_path: `0.9`
- road_context.night_urban_multilane_or_lane_markings_visible: `0.9`
- hdmap_alignment.lane_geometry_visually_consistent_with_scene: `0.85`
- control_binding.structural_evidence_referenced_without_overclaiming: `1.0`

## Claim Boundary

This result supports a measured-passed P0 candidate70 prompt-video alignment claim for this specific retry artifact.

It does not by itself complete the paper experiments.

Do not claim:

- full Section 4 completion
- baseline-vs-DriveLoop quantitative comparison
- automatic multi-round Algorithm 1 completion
- YOLO/perception measured_passed
- general source-selection success across the full dataset
- semantic success from tensor/hash/video existence alone

Allowed current wording:

- Candidate70 48f source-bound GPU retry produced a video candidate that passed explicit manual prompt-video alignment review.
- The alignment evaluator recorded `measured_passed` with score `0.916667` and 9/9 required checks passed.
- Structural actor-motion and HDMap evidence are conditioning evidence, while the semantic pass comes from the measured manual review and evaluator.

## Next Work

- Preserve the artifact and report paths.
- Add automatic perception/VLM review if available.
- Build at least one baseline comparison run.
- Repeat on additional long-tail scenes before making broad paper claims.
- Update Section 4 only after baseline and multi-scenario evidence exists.
