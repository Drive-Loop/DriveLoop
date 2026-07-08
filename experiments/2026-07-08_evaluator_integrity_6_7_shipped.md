# 2026-07-08 Evaluator integrity guards shipped: min support (#6) + baseline differential (#7)

## What shipped
- #6: PerceptionVideoEvaluator.min_target_support_frames (default 2).
  Single-frame target support zeroes the degenerate Q_id/Q_box credit
  and adds reason insufficient_target_support_frames. New metric:
  perception_target_support_frames.
- #7: CompositePerceptionVideoEvaluator baseline-differential
  subtraction (class-agnostic IoU >= 0.5 against the no-injection
  baseline video of the same source window; determinism makes the
  baseline exact). New metrics: perception_baseline_available,
  perception_baseline_subtracted_count. Plumbed as
  --perception-baseline-video (experiment CLI) and --baseline-video
  (composite eval script). Trajectory gating deferred to the
  injection-surface uplift (needs true projections).
- Tests: 6 new (fixtures use the measured m5/m4 coordinates); suite 401.

## Acceptance on real artifacts (yolov8x@0.20, baseline = m4 no-injection video)
- left 3.5/20 without baseline: view1 0.176796, support_frames 1.
- left 3.5/20 with baseline: view1 UNCHANGED 0.176796 with 68
  detections subtracted: target credit is exclusively non-baseline
  content; attribution clean.
- right 3.0/20 with baseline: view1 0.213818 (was 0.514 pre-guard),
  74 subtracted, support_frames 1.

## Reading and claim boundaries
- Prior grid highs (0.477/0.514) were mostly single-frame degenerate
  credit; the honest ceiling of current synthetic injection is ~0.2
  at x@0.20 with 1-frame support, while humans see the motorcycle
  across frames (detector night floor persists; do not chase it with
  threshold hacks).
- Metric version note: all S_perc/J values recorded before this change
  (v7/v8/v9 arms, both grids) are NOT comparable to post-guard scores.
  tau_v9 must be derived from arms scored with the new evaluator.
- Multi-frame target support is now the primary quantity the loop
  must improve.
