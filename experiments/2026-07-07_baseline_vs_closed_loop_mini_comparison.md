# Mini baseline-vs-closed-loop comparison (candidate70, 5 prompts)

Date: 2026-07-07

## Setup

- backend: DriveDreamer-2 frozen runtime, config drivedreamer2_img_cond_mini_local
- source: candidate70 source-bound trainval subset (same binding for all runs)
- evaluator: CompositePerceptionVideoEvaluator (yolov8m, conf 0.25, generated-row
  crop + 6-view split) with Eq.(5) task utility (w=0.5/0.3/0.2), tau=0.8
- open-loop baseline: max_iterations=1; closed loop: max_iterations=3 with
  escalation refiner (commit 9785ce0); identical everything else
- determinism check: repeated prompts reproduce identical scores across runs

## Results

| case | open-loop J | closed-loop J | attempts | delta |
| --- | ---: | ---: | ---: | ---: |
| m1_night_cut_in_left   | 0.963 pass | 0.963 pass | 1 | 0 |
| m2_rainy_night_cut_in  | 0.976 pass | 0.976 pass | 1 | 0 |
| m3_lane_change_left_to_ego | 0.500 fail | 0.977 pass | 3 | +0.477 |
| m4_intersection_approach   | 0.500 fail | 0.962 pass | 3 | +0.462 |
| m5_low_visibility_cut_in   | 0.978 pass | 0.978 pass | 1 | 0 |

- acceptance rate: 3/5 (60%) -> 5/5 (100%)
- mean best J: 0.783 -> 0.971
- failed-case J floor 0.500 equals w_c*S_ctrl + w_i*S_intent with S_perc=0
- v1 control run (pre-escalation refiner, commit 836dd04 era): m3/m4 stayed at
  0.500 across 3 identical retries, confirming the gain comes from
  feedback-driven prompt refinement rather than retry count.

## Artifacts

- open loop: outputs/driveloop/exp_c70_open_loop_baseline/
- closed loop v1 (saturated refiner): outputs/driveloop/exp_c70_closed_loop/
- closed loop v2: outputs/driveloop/exp_c70_closed_loop_v2/

## Claim boundary

- J is the Eq.(5) acceptance utility; S_ctrl/S_intent here are plan-level and
  saturate at 1.0, so J differences are driven by measured perception (S_perc).
- semantic_success_claim_allowed remains False pending manual alignment review
  of the newly accepted m3/m4 videos.
- n=5 prompts on one source-scene family; this is the mini protocol, not the
  full Section 4 suite.
