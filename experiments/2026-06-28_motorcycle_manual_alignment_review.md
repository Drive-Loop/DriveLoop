# Motorcycle Manual Alignment Review

Date: 2026-06-28

## Reviewed Artifact

Video:

`outputs/driveloop/motorcycle_fix_gpu_smoke/20260628T035627Z_motorcycle_fix_gpu_smoke/motorcycle_day_left_lane_change/iteration_00.mp4`

Prompt:

`daytime urban road with a motorcycle changing lane from the left`

Review source:

- Human review of the generated video.
- Contact sheet was also available, but it was too blurry for reliable semantic judgment.
- Review protocol: `experiments/2026-06-28_manual_alignment_review_protocol.md`

Evaluator output:

`outputs/driveloop/prompt_video_alignment_eval/motorcycle_manual_review_v0/prompt_video_alignment_evaluation.json`

## Evaluation Result

Overall result:

- `video_semantic_claim`: `measured_failed`
- score: `0.65`
- required checks: `4`
- passed required checks: `3`

## Check Results

### object_presence.motorcycle

Result: passed with moderate confidence.

Score: `0.6`

Evidence summary:

The reviewer observed a bicycle and another actor that appears motorcycle-like, but the video is blurry and the actor is not fully certain.

Claim boundary:

This supports possible motorcycle presence, not a high-confidence motorcycle detection.

### spatial_relation.left_lane_change

Result: failed.

Score: `0.0`

Evidence summary:

The reviewer observed straight driving and did not observe a lane-change maneuver.

Claim boundary:

The prompt asks for a motorcycle changing lane from the left. This temporal relation is not supported by the reviewed video.

### lighting.daytime

Result: passed.

Score: `1.0`

Evidence summary:

The scene is visibly lit as daytime.

### scene_type.urban_road

Result: passed.

Score: `1.0`

Evidence summary:

The reviewer observed an urban road with pedestrians, parked cars, street lights, buildings, mailbox-like street fixtures, and other roadside facilities.

## Interpretation

This is a partial alignment and negative result.

The video should not be claimed as prompt-semantically successful because the required lane-change relation is not visible. The result is useful because it demonstrates that the alignment evaluator can record a semantic failure even when tensor overrides and video generation succeeded.

## Relation To Tensor Audit

This manual review does not invalidate the DD2 tensor audit.

The tensor audit showed that DriveLoop can change DD2 `boxes3d` and derived `image_box` structural conditions. The manual review shows that changing those tensors and generating a video does not by itself prove prompt-video semantic success.

## Recommended Next Step

Use this failed check as feedback:

- failed check: `spatial_relation.left_lane_change`
- feedback control level: `text_feedback_only`
- next action: run audit-only or short controlled generation only after confirming that the refined prompt and DD2 condition trace include the lane-change feedback.

Do not run a long GPU job solely to chase this result.
