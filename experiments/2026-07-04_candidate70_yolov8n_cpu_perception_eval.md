# Candidate70 YOLOv8n CPU Perception Evaluation

Date: 2026-07-04

## Summary

Candidate70 now has an automatic perception-oriented evaluation result for the latest measured_failed GPU smoke video.

This was a CPU-only detector/tracker evaluation. It did not run GPU generation and does not approve a new GPU run.

## Environment Decision

Ultralytics was not upgraded.

The installed ultralytics 8.0.0 runtime did not accept in-memory OpenCV frames reliably, so the detector adapter now materializes each frame to a temporary jpg path before calling YOLO. This keeps the existing environment stable and avoids dependency churn.

## Input

Video:

- outputs/driveloop/candidate70_night_cut_in_gpu_smoke/artifacts/candidate70_night_cut_in_gpu_smoke/iteration_00.mp4

Detector:

- YOLOv8n local weights
- target_label: motorcycle
- max_frames: 8
- confidence_threshold: 0.25
- CPU-only execution

Report:

- outputs/driveloop/perception_video_eval/candidate70_night_cut_in_yolov8n_cpu_8f_motorcycle/perception_video_evaluation.json

## Observed Result

The perception report produced:

- perception_claim: measured_failed
- score: 0.0
- perception_frame_count: 8.0
- perception_detection_count: 0.0
- perception_track_count: 0.0
- Q_cov: 0.0
- Q_conf: 0.0
- Q_track: 0.0
- Q_id: 0.0
- Q_box: 0.0

Diagnosis reasons:

- target_object_not_detected
- low_detection_coverage
- low_detector_confidence
- unstable_track_coverage
- identity_inconsistent
- unstable_bounding_boxes

## Interpretation

This automatic perception result supports the existing manual measured_failed conclusion for candidate70: the generated video does not provide detector/tracker evidence for a visible motorcycle target across the sampled frames.

This is detector/tracker evidence, not full semantic proof. It should be used as measured failure evidence and as feedback for refinement, not as a claim that the full paper loop is complete.

## Claim Boundary

Allowed claim:

- Candidate70 has an automatic perception-oriented measured_failed report for the latest GPU smoke video.
- The CPU YOLOv8n check found no motorcycle detections across the sampled 8 frames.
- The automatic perception evidence is consistent with the manual review failure.

Forbidden claims:

- Do not claim semantic success.
- Do not set semantic_success_claim_allowed to true.
- Do not claim the generated video contains a visible motorcycle cut-in.
- Do not treat detector failure as a complete replacement for human semantic review.
- Do not run another GPU smoke without explicit approval and a post-GPU review path.

## Next Technical Direction

Connect this perception report into the candidate70 closed-loop status artifact so the loop contains:

1. measured_failed manual alignment review
2. failure taxonomy
3. refinement proposal
4. source/runtime readiness
5. automatic perception measured_failed evidence
6. explicit approval gate before any GPU retry
