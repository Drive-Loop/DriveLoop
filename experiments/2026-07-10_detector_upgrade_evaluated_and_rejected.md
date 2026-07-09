# 2026-07-10 Detector upgrade evaluated and REJECTED; methodology lesson

Hypothesis: yolov8x is night-blind (07-08 floor record); YOLO-World
(yolov8x-worldv2) fixes it. Full-frame probes supported this: on the
07-04 human-passed video, v8x 0 detections vs world 6.

Evaluator-level test (per-view crops, conf 0.20, v9 baseline
differential) REVERSED the conclusion: 07-04 video - v8x support 5/8
frames max 0.576 vs world 2/8 max 0.476; r5 m4 video - tied at
support 1. The full-frame probe was a resolution artifact (2688-wide
composite squashed to 640 leaves ~100 px per view); the evaluator's
per-view cropping already recovers night detections. Decision: KEEP
yolov8x@0.20. Methodology rule recorded: detector claims must be
made at the evaluator level, never from full-frame probes.

## m4 acceptance decomposition (r5 attempt 2, J=0.578)
S_ctrl 1.0, S_intent 1.0, Q_conf 0.467, S_perc 0.156 (support 1
frame, views 0.156/0.137), Q_cov=Q_track 0.125. The tau-0.45
acceptances lean on control/intent/utility terms; perception support
is thin (single frame). Human review confirmed the motorcycle, so the
thin perception support reflects detector difficulty on
 this
rendering, but paper language must not imply strong perception
evidence for these acceptances.
