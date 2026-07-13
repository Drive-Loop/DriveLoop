# 2026-07-13 Corrected v9-protocol matrix: FT and dims-scale both lift J

Corrected setup (after dataset errata 6d95524): candidate70
source-bound subset via --baseline-dataset-dir; binding ready=true and
the real-track marker verified in every arm (preflight gates);
per-weight no-injection baselines; perception_baseline_available
verified 1.0 in all reported arms. Open arms: 1 attempt, seed 6666.
Evaluator: yolov8x@0.20, per-window no-injection baseline
differential, task utility on, tau 0.45 at the record level.

## Best J per case
case | official open | ft6322 open | official dims1.5 | v9 archive
m1   | 0.200 | 0.534 | 0.537 | 0.200
m2   | 0.546 | 0.424 | 0.423 | 0.546
m3   | 0.407 | 0.421 | 0.422 | 0.407
m4   | 0.200 | 0.566 | 0.200 | 0.200
m5   | 0.200 | 0.200 | 0.415 | 0.200
mean | 0.311 | 0.429 | 0.399 | 0.310
Runs: exp_v9c_official_open_anchor, exp_v9c_ft6322_open_loop_bank0_v2,
exp_v9c_official_open_dims1p5; FT baseline
v9_no_injection_baseline_ft6322_c70sub.

## Findings
1. Reproducibility restored: the same-day official anchor reproduces
   the v9 archive to three decimals on all five cases. The archive
   break was entirely the missing dataset flag (errata 6d95524); no
   code drift.
2. Trainval FT step_6322 lifts J on the corrected benchmark: mean
   0.311 -> 0.429 (+38 percent); m1 +0.334, m4 +0.366, m3 +0.014,
   m2 -0.122 (the rainy case regresses), m5 unchanged. This
   supersedes the wrong-dataset null result and is the first
   evaluator-level positive FT signal. The far-entry human-review
   verdict (no class-fidelity fix) is unaffected: that experiment was
   correctly bound (mini val, sample-token selector).
3. The real-track dims scale 1.5 (commit 6efcb35) also lifts J under
   official weights: mean 0.311 -> 0.399; m1 +0.337, m5 +0.215,
   m3 +0.015, m2 -0.123, m4 unchanged. FT and dims have overlapping
   but distinct case profiles (FT lifts m4, dims lifts m5, both
   regress m2): complementary levers. A stacked FT+dims arm is the
   next probe (5 generations).
4. FT closed and no-escalation arms (3 attempts) equal FT open per
   case: best-of-3 never beat attempt 0 on this window, replicating
   the v9 arm-identity finding under FT. (Those arms were scored
   before the baseline fix; the baseline fix shifted open m2 by
   +0.008 only.)
5. Second silent-degradation gap of the day: with a missing
   --perception-baseline-video file the evaluator scores with
   perception_baseline_available=0.0 and no hard failure; the FT arms
   were first scored that way and had to be rerun. Action item: hard
   fail on a missing baseline video, alongside the ego-injection
   mapping gate.

## Claim boundary
Single window (candidate70), bank0 seed, n=5 cases, one attempt in
the open arms; detector-level uplift only, no perception or semantic
success claims. The m2 regressions are unexplained and need per-case
review before either lever is promoted to a default.

## Resolution addendum
See 2026-07-13_m2_dissection_and_support_table.md: every per-case J
delta in this matrix rides on 0/1/2 surviving detection frames (max
support 2/8 anywhere). The mean-J direction stands; per-case
magnitudes and the m2 regression are below evaluator resolution.
Binary detectability: anchor 2/5, ft 4/5, dims1.5 4/5.
