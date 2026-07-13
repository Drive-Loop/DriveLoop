# 2026-07-13 Bank1 seed replication: direction holds, magnitude collapses

Setup: DRIVELOOP_DD2_SEED_BANK=1 (seed offset 100), same corrected
candidate70 protocol as the v9c matrix; fresh per-weight per-seed
no-injection baselines; two arms, open loop, 1 attempt, 5 cases:
official anchor and ft6322+dims1.5 stacked. Gates verified in the
artifacts: binding ready in all cases, real-track engaged with
dims_scale 1.5 in the frame-mapping audit (exception m4, finding 3),
perception_baseline_available 1.0 everywhere. Runs:
exp_v9r1_official_open_anchor, exp_v9r1_ft6322_dims1p5_open;
baselines v9r1_no_injection_baseline_{official,ft6322}_c70sub.

## Results (support frames / J), bank0 values in parentheses
case | anchor_b1      | ftdims_b1
m1   | 0 / 0.200 (0 / 0.200) | 1 / 0.435 (1 / 0.432)
m2   | 0 / 0.200 (2 / 0.546) | 1 / 0.431 (1 / 0.413)
m3   | 0 / 0.200 (1 / 0.407) | 0 / 0.200 (2 / 0.531)
m4   | 0 / 0.200 (0 / 0.200) | 0 / 0.200 (1 / 0.566)
m5   | 0 / 0.200 (0 / 0.200) | 0 / 0.200 (1 / 0.452)
Detectability: anchor 0/5 (bank0 2/5); stacked 2/5 (bank0 5/5).
Mean J: anchor 0.200 (0.311); stacked 0.293 (0.479).

## Findings
1. Direction replicates: the stacked arm is at or above the anchor on
   every case at bank1 and beats it on detectability at both seeds
   (2/5 vs 0/5 at bank1; 5/5 vs 2/5 at bank0). Across the two seeds
   the stacked arm detects every case at least once; the anchor never
   detects m1, m4 or m5 on either seed. The only anchor-above-stacked
   cell anywhere is bank0 m2, already dissected as single-detection
   variance.
2. Magnitude does not replicate: absolute detectability is strongly
   seed-dependent (stacked 5/5 -> 2/5, anchor 2/5 -> 0/5), and bank1
   baseline subtraction is heavier (77-86 matches vs 65-76). The
   bank0 mean uplift (+54 percent) must not be quoted as an effect
   size; the supported claim is a consistent ordering with large seed
   variance. bank1 m2 (anchor 0 detections) confirms the dissection
   verdict on the bank0 m2 anchor advantage.
3. m4 runs with an empty real-track frame mapping in both arms at
   both banks (0 real-track audit entries; synthetic fallback
   engaged silently). This retroactively explains the bank0 m4
   anomalies (dims lever no-op; ft and ft+dims identical to three
   decimals): every m4 result so far is a synthetic-path result. The
   unbound-window hard fail (98ac48b) does not cover this case - the
   window binds, but the actor has no visible mapped frames. Action
   item: audit marker or hard fail when EGO_INJECTION=1 and the
   real-track mapping is empty.
4. Promotion gate consequence: single-seed J comparisons on this
   window are not evidence; lever claims need per-seed sign
   consistency (met here for ft+dims vs anchor) and, for any effect
   size, more seeds or more windows.

## Claim boundary
Two seeds, n=5 cases, one attempt per case, one window; detector-level
binary detectability only; no perception or semantic claims. m4 is a
synthetic-path case at both banks and carries no real-track evidence.
