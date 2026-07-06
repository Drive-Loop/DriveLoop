# Composite perception eval: zero-detection root cause and fix

Date: 2026-07-06

## Problem

Previous CPU perception eval on candidate70 reported score 0.0 with zero
detections (all Q metrics 0.0), which contradicted manual review.

## Root causes (both confirmed by measurement)

1. ultralytics API mismatch. The env had ultralytics 8.0.0, whose predict
   returns raw tensors. `perception_video.py` parses new-style `result.boxes`;
   `getattr(result, "boxes", None)` returned None, so every frame silently
   yielded zero detections. No error was raised.
2. Composite debug mosaic. `iteration_00.mp4` (2688x784, 8 frames) is a DD2
   tester debug composite: source row + condition visualization row + generated
   row, with 6 camera views of width 448 tiled horizontally. Whole-frame
   detection downscales each view to ~100x200, destroying small objects, and
   mixes source/condition pixels into the metric.

## Fix

- Env: ultralytics upgraded 8.0.0 -> 8.2.103 with `pip install --no-deps`
  (torch/numpy untouched).
- Code: new `driveloop/composite_perception.py` with `CompositeVideoLayout`
  (crop bottom generated row, split 6 views) and
  `CompositePerceptionVideoEvaluator` (per-view evaluation, best-view
  aggregation, fallback to whole-frame for non-composite videos).
- Script: `scripts/run_composite_perception_eval.py`.
- Tests: `tests/test_composite_perception.py` (3 tests).

## Measured result (candidate70 48f GPU retry video, yolov8m, conf 0.25)

- before: score 0.0, zero detections
- after: score 0.468199, perception_claim measured_failed
- perception_best_view: 0 (front-left, consistent with the left cut-in prompt)
- Q_cov 0.125, Q_conf 0.5285, Q_track 0.125, Q_id 1.0, Q_box 1.0
- Diagnostic signal is now actionable: the motorcycle is detected in 1/8
  frames at conf>=0.25 (max 0.58); low coverage drives the refinement loop.

## Claim boundary

This is perception-evidence repair. It does not claim semantic success. The
measured_failed claim stands but is now based on valid measurements.
