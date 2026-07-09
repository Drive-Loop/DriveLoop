# 2026-07-09 v9 three arms: ego injection + new evaluator

Setup: DRIVELOOP_EGO_INJECTION=1 (real-track mode active for the
candidate70 window), evaluator yolov8x@0.20 with per-window
no-injection baseline differential (v9_no_injection_baseline), task
utility on, tau_v9 frozen at 0.45 (open-arm anchor_mean_plus_1_std
0.4696 -> 0.05 grid). Arms: open (1 iter), closed (3 iters),
no-escalation (3 iters). OOM fix (evaluator releases GPU after each
evaluation, lazy YOLO reload) landed mid-v9 after two closed-arm
crashes; r3 is the clean closed run.

## Results (best J per case; identical across ALL arms)
m1 night cut-in left 0.2; m2 rainy night cut-in 0.546 (sole
acceptance at tau 0.45); m3 lane change left 0.407; m4 intersection
0.2; m5 low visibility 0.2. Arm mean 0.310, std 0.159 (n=5).

## Core finding: the closed loop currently has NO effective lever
Attempt-level probe (closed m1): three attempts, J = 0.2, 0.2, 0.2 -
bit-identical scoring. Explanation, all three parts measured:
1. generation is seeded (tester manual_seed);
2. real-track ego injection ignores the synthetic plan geometry that
   refiner escalation modifies (proximity/size scales are its levers);
3. the DD2 transform collapses any refined prompt to one of three
   canned strings (rain/night/default), so prompt refinement cannot
   reach the conditioning either.
Consequence: closed-loop == open-loop replicates under this
configuration. The one high scorer (m2) is driven by the only prompt
token that DOES reach conditioning ("rain" -> rainy canned prompt).

## Reading
- This is a mechanism finding about lever wiring, not a negative
  capability result: v7-era escalation recovery remains valid for the
  synthetic path, which real-track mode supersedes on this window.
- Next levers that DO reach conditioning under real-track mode:
  generation parameters (DRIVELOOP_DD2_NUM_INF_STEPS /
  MIN_GUIDANCE / MAX_GUIDANCE, already exposed, unexercised),
  real-track reinforcement magnitude (dims/heading perturbation),
  window/candidate selection, and unfreezing the seed across attempts.
- Evaluator semantics note: with real-track reinforcement, the
  baseline differential measures whether conditioning makes the SAME
  real actor more detectable than the no-injection baseline - the
  intended uplift measurement.

## Claim boundary
No semantic success claims. Scores are detector-floor-limited at
night (m1/m4/m5 at the 0.2 floor). Single window (candidate70);
synthetic path still unvalidated in a clean window lacking the
requested actor. Cross-version comparisons to v8 numbers are invalid
(metric changed: baseline differential + real-track mode).
