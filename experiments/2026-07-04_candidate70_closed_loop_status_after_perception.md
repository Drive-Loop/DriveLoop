# Candidate70 Closed-Loop Status After Perception Evidence

Date: 2026-07-04

## Summary

Candidate70 closed-loop status now includes automatic perception-oriented measured_failed evidence from the CPU YOLOv8n evaluation.

This does not claim semantic success and does not approve another GPU run.

## Connected Perception Evidence

Report:

- outputs/driveloop/perception_video_eval/candidate70_night_cut_in_yolov8n_cpu_8f_motorcycle/perception_video_evaluation.json

Observed result:

- perception_claim: measured_failed
- score: 0.0
- target_label: motorcycle
- perception_frame_count: 8.0
- perception_detection_count: 0.0
- perception_track_count: 0.0
- Q_cov: 0.0
- Q_conf: 0.0
- Q_track: 0.0
- Q_id: 0.0
- Q_box: 0.0

## Closed-Loop Update

Updated artifact:

- outputs/driveloop/candidate70_closed_loop_status/candidate70_closed_loop_status.json

The closed-loop status now includes:

- automatic_perception_evaluation: measured_failed
- perception report source path
- detector/tracker metrics
- diagnosis reasons from the perception evaluator

The blocker changed from:

- automatic_perception_evaluator_not_yet_connected

to:

- automatic_perception_evaluator_measured_failed

## Claim Boundary

Allowed claim:

- Automatic perception evidence is now connected to the candidate70 closed-loop status.
- The latest candidate70 GPU smoke remains measured_failed.
- The CPU YOLOv8n evaluator found no motorcycle detections in the sampled 8 frames.

Forbidden claims:

- Do not claim semantic success.
- Do not set semantic_success_claim_allowed to true.
- Do not claim the generated video contains a visible motorcycle cut-in.
- Do not treat perception metrics as full semantic proof.
- Do not run another GPU smoke without explicit approval and post-GPU review.

## Next Technical Direction

Use the perception measured_failed report as another feedback source for the refinement/gating layer. The next non-GPU step is to make retry gating require:

1. measured_failed review is present
2. taxonomy/refiner feedback is available
3. source/runtime readiness remains available
4. perception evaluation is attached
5. explicit approval exists before any GPU retry
