# 2026-07-13 FT + dims-scale stacking probe (candidate70, bank0)

Same corrected setup as the 2026-07-13 v9c matrix record. Stacked arm:
DRIVELOOP_DD2_WEIGHT_PATH=checkpoint_epoch_1_step_6322 plus
DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE=1.5, open loop, 1 attempt, seed
6666, scored against the FT no-injection subset baseline.
perception_baseline_available 1.0 and dims_scale 1.5 verified in the
artifacts. Run: exp_v9c_ft6322_dims1p5_open.

## Best J per case (earlier arms for reference)
case | anchor | ft | dims1.5 | ft+dims1.5
m1   | 0.200 | 0.534 | 0.537 | 0.432
m2   | 0.546 | 0.424 | 0.423 | 0.413
m3   | 0.407 | 0.421 | 0.422 | 0.531
m4   | 0.200 | 0.566 | 0.200 | 0.566
m5   | 0.200 | 0.200 | 0.415 | 0.452
mean | 0.311 | 0.429 | 0.399 | 0.479

## Findings
1. Stacking is net additive: mean 0.479 is the best arm so far (+54
   percent over the anchor, +12 percent over FT alone). tau-0.45
   acceptances reach 3/5 (m3, m4, m5) versus 1/5 in the v9 archive.
2. Case-level interactions are real: m3 and m5 are superadditive
   (0.531 and 0.452, above either single lever), m4 keeps the FT
   lift, m1 is sub-additive (0.432, below either single lever but
   far above the anchor), and the m2 regression persists (0.413 vs
   anchor 0.546) across every lever combination.
3. Next gates before promoting any lever: per-case m2 review across
   all four arms, and human review of the stacked videos for
   dims-scale visual artifacts (oversized actor).

Claim boundary: single window (candidate70), bank0 seed, one attempt,
n=5 cases; detector-level uplift only; no perception or semantic
claims; the dims scale stays env-gated and default-off pending human
review.

## Human-review addendum
Stacked-arm videos (m3, m5) reviewed frame-stepped: the motorcycle is
clearly rendered and notably better than the earlier arms; a slight
widening of the actor appears in the final frame, judged minor by the
reviewer. Dims scale 1.5 passes visual review with that caveat; it
stays env-gated and default-off, and last-frame widening is the first
artifact to watch at higher scales.

## Resolution addendum
See 2026-07-13_m2_dissection_and_support_table.md: the interaction
reads (m3/m5 superadditive, m1 sub-additive, m2 regression) are below
evaluator resolution (+-1 surviving detection). The robust stacked
claim is binary detectability 5/5 versus anchor 2/5.
