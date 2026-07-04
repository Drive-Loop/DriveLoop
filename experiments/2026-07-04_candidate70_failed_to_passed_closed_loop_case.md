# Candidate70 Closed-Loop Failed-to-Passed Case

Date: 2026-07-04

## Scope

This record supports a DriveLoop closed-loop case study for candidate70. It should be described as a pre-refinement failed attempt followed by a diagnosis/refinement-driven retry, not as a full open-loop DD2 baseline comparison.

## Artifact Identity

| Artifact | Path | SHA256 |
|---|---|---|
| Failed attempt video | `outputs/driveloop/candidate70_night_cut_in_gpu_smoke/artifacts/candidate70_night_cut_in_gpu_smoke/iteration_00.mp4` | `a0a6667eb7bde0deadeacfaad5a785dff432a3be740a639399fb37cab4b63f7f` |
| Retry video | `outputs/driveloop/candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z/artifacts/candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z/iteration_00.mp4` | `decfd1b37c33234af15dff97a83c13e72cf7c3d1f59174b18f559332460f3a86` |

## Result Summary

| Attempt | Claim | Alignment Score | Required Checks Passed | Notes |
|---|---:|---:|---:|---|
| candidate70_night_cut_in_gpu_smoke | `measured_failed` | 0.361111 | 3/9 | Target motorcycle/cut-in semantics failed under manual review and perception evidence. |
| candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z | `measured_passed` | 0.916667 | 9/9 | Human-reviewed prompt-video alignment passed all required checks. |

## Failed Attempt Evidence

Manual alignment failed required checks:

- `alignment_check_failed:object_presence.motorcycle_or_scooter_visible`
- `alignment_check_failed:object_consistency.target_actor_trackable_across_frames`
- `alignment_check_failed:maneuver.cut_in_from_left_toward_ego_visible`
- `alignment_check_failed:temporal_motion.lateral_displacement_visible`
- `alignment_check_failed:spatial_relation.starts_left_or_adjacent_lane_and_moves_toward_ego_path`
- `alignment_check_failed:hdmap_alignment.lane_geometry_visually_consistent_with_scene`

YOLOv8n CPU perception metrics on the failed attempt:

| Metric | Value |
|---|---:|
| Q_cov | 0.0 |
| Q_conf | 0.0 |
| Q_track | 0.0 |
| Q_id | 0.0 |
| Q_box | 0.0 |
| detection_count | 0.0 |
| track_count | 0.0 |

Failure taxonomy labels:

- `object_identity_failed`
- `motorcycle_identity_failed`
- `tracking_identity_failed`
- `low_visual_confidence`
- `cut_in_motion_failed`
- `lane_change_motion_failed`
- `lateral_motion_failed`
- `spatial_relation_failed`
- `hdmap_alignment_failed`

## Refinement Link

The retry was derived from a refinement proposal rather than treated as an automatic semantic success.

- Proposal path: `outputs/driveloop/candidate70_retry_refinement_proposal/candidate70_retry_refinement_proposal.json`
- Proposal does not run GPU: `True`
- Explicit GPU retry approval required: `True`
- Post-GPU review required: `True`

## Claim Boundary

- The failed attempt is measured failed.
- The retry is measured passed by human-review-backed prompt-video alignment.
- `semantic_success_claim_allowed` remains false inside the manual reports by design: video existence and tensor/runtime evidence alone are not treated as semantic success.
- This case supports Algorithm 1-style closed-loop diagnosis and refinement.
- This case does not yet replace a true DD2 open-loop baseline comparison for Section 4.

## Remaining Work

1. Run or recover a strict open-loop DD2 baseline under matched prompt/source conditions.
2. Add perception-oriented evaluation for the measured-passed retry if weights/tooling are available.
3. Repeat the failed-to-passed protocol on additional long-tail scenarios.
