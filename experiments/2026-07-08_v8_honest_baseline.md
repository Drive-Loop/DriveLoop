# 2026-07-08 v8 three arms: honest capability baseline

Setup: side-calibrated defaults (right 3.2/9, left 2.0/9), sweet-spot
escalation ladder (position fixed, size 1.5), clean target-view metrics
with category-filtered direction check. tau 0.7, max 3 attempts.

Result: 0/5 accepted in ALL arms. closed r2 best J:
m1 0.581, m2 0.623, m3 0.516, m4 0.200, m5 0.532.
m2/m5 reach direction consistency 1.0 with Q_cov 0.375; m1/m3 Q_cov
0.125. Arm-to-arm and run-to-run J differences (~0.05) are within
sampling noise.

## Reading
- v5-era acceptance (4/5, J 0.75-0.85) is confirmed metric inflation
  (clones + mirrored geometry + all-view max). This v8 result is the
  honest baseline of candidate70 + drivedreamer2_img_cond_mini + 8
  frames: S_perc ceiling ~0.46, J ceiling ~0.63.
- tau 0.7 was chosen under inflated metrics; the clean J distribution
  shifted down ~0.15-0.2. Re-anchor tau from arm distributions before
  the next comparison (transparent recalibration, next session).
- Remaining gap is generation capability, not loop mechanics:
  stronger checkpoint / longer frame_num / left-friendly source scenes /
  intersection primitive for m4.

## Claim boundaries
- 0/5 at tau 0.7 is a capability boundary measurement, not a negative
  mechanism result; v7 escalation recovery (m1 J 0.2 -> 0.6, direction
  consistent) remains valid feedback-content evidence.
- No semantic success claims; no paper Section 4 numbers from v8.
