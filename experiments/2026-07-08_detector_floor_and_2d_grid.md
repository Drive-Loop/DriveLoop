# 2026-07-08 2D distance grid, detector floor confirmed, yolov8x reopens the loop

## 2D re-calibration sweep (single pass, yolov8m@0.25 scoring)
LEFT S_perc:  lat3.0: 0.375/0.429/0.000 (lon 16/20/24)
              lat3.5: 0.433/0.488/0.418
              lat4.0: 0.410/0.487/0.476
              lat4.5: 0.000/0.000/0.000
RIGHT S_perc: all zero except lat3.5/lon16 0.431, lat4.5/lon16 0.497.

## Right-side zeros are detector-floor artifacts, not render failures
Human review (tangzimo) of geo_right_lat4p0_lon20 (S_perc 0.000):
recognizable motorcycle, render quality better than earlier attempts.
The grid at far range measures detector visibility, not render quality.
Consequence: geometry defaults must not be chosen off this grid as-is,
and the loop's S_perc feedback is blind exactly where rendering is best.

## Detector experiment (same tiles, existing artifacts)
- yolov8m conf 0.10: marginal single-frame hits (motorcycle 0.10-0.26).
- yolov8x conf 0.20: right_far motorcycle 0.36/0.22/0.50;
  retry0704 motorcycle 0.34. Both human-visible motorcycles that
  yolov8m@0.25 missed entirely are now detected with the correct class.

## Decisions
1. Upgrade evaluator detector to yolov8x for calibration and v9, paired
   with the multi-frame support guard (integrity candidate #6) so
   low-confidence noise cannot inflate S_perc.
2. Re-score the existing 24 sweep videos offline with yolov8x (no
   regeneration needed) to obtain a seeing-eye grid; THEN pick
   side-specific defaults and the escalation distance axis.
3. Suspicion to check: the historical right-side near-range high
   (3.2/9, S_perc 0.642) was never human-reviewed; under today's
   lessons it may be a detector-favored blob. Spot-check before it is
   kept as the right default.

## Claim boundaries
Single scene, night, single pass, n=1 per grid point. Human review
covers three cells (left 3.5/20, right 4.0/20, plus 0704 re-review);
all other cells are metric-only. No paper numbers.
