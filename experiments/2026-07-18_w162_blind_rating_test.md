# 2026-07-18 candidate162 blind rating falsifies the non-blind arm judgments

The arm judgments in 2026-07-18_w162_manual_frame_review.md were made
with arm identity visible in the folder names. This is the blind test
listed as follow-up 1 of that record. The registered prediction failed.

## Design
Ten trials, one per candidate162 video: the front-cell generated row, 8
frames, shuffled into content-free trial directories. The key stayed on
the server and was never included in the download. The prediction was
written at build time, before any score existed: ft6322_dims1p5 -> 0
(clean), official_anchor -> 1 (deformed), both no-injection baselines
-> 2 (deformed and smeared). Rubric: 0 clean, 1 deformed, 2 deformed
and smeared. Same reviewer as the non-blind pass, rating each trial in
isolation, with no GT or condition row shown.

## Result
    trial     config             case                        pred  obs
    trial_01  baseline_official  v10w_no_injection_baseline   2     2
    trial_02  ft6322_dims1p5     m1_night_cut_in_left         0     2
    trial_03  baseline_ft6322    v10w_no_injection_baseline   2     2
    trial_04  official_anchor    m5_low_visibility_cut_in     1     1
    trial_05  official_anchor    m2_rainy_night_cut_in        1     1
    trial_06  official_anchor    m1_night_cut_in_left         1     1
    trial_07  ft6322_dims1p5     m3_lane_change_left_to_ego   0     2
    trial_08  official_anchor    m3_lane_change_left_to_ego   1     2
    trial_09  ft6322_dims1p5     m2_rainy_night_cut_in        0     2
    trial_10  ft6322_dims1p5     m5_low_visibility_cut_in     0     2

Exact agreement 5/10. Zeros awarded: 0, where the prediction required 4.
By config: ft6322_dims1p5 [2,2,2,2] mean 2.00 (predicted 0);
official_anchor [1,1,1,2] mean 1.25 (predicted 1); baseline_ft6322 [2]
and baseline_official [2] mean 2.00 (predicted 2). Spearman rho between
registered prediction and blind score -0.244, permutation p 0.4339
(200000 permutations, seed 0).

## Findings
1. The registered prediction is falsified. Not one of the four
   ft6322+dims1.5 cases, all four of which the non-blind pass recorded
   as free of artifacts, received a clean score once arm identity was
   hidden. All four received the worst score on the rubric.
2. The blind point estimate reverses the non-blind ordering. Blind, the
   official-anchor arm rates best (1.25) and the ft6322+dims1.5 arm
   rates worst (2.00, tied with the no-injection baselines). The
   association with the registered prediction is negative and not
   significant (rho -0.244, p 0.43). The honest reading is that the
   non-blind ordering does not reproduce, not that the reverse ordering
   is established.
3. The inverse-instrument finding is withdrawn. Finding 6 of
   2026-07-18_w162_manual_frame_review.md held that v10b S_perc orders
   the arms inverse to human judgment, and inferred from that an
   obstacle to v10 adoption. Blind, human rating and v10b agree in
   direction: both place the official anchor above ft6322+dims1.5 on
   this window. The obstacle was an artifact of the non-blind pass and
   is removed.
4. Presence-type judgments survive. Every trial scored 1 or 2, and a
   deformation score presupposes a visible actor, so an actor is
   rendered in all ten videos. This is consistent with findings 1, 2
   and 7 of the frame review. The detector support gap therefore
   stands: the evaluator recovers 0-4 support frames on actors the
   reviewer sees throughout. That gap, not the arm ordering, is the
   durable result of this review cycle. Its cause is now known and was
   not a detector under-count: see
   2026-07-18_w162_baseline_subtraction.md, where the detector is shown
   to detect the actor in every frame and the label-blind baseline
   subtraction is shown to remove it.
5. Method caution for the project. The reviewer's artifact judgments
   reversed when folder names were hidden. Every earlier manual review
   in this project conducted with arm identity visible carries the same
   expectancy risk. Any such review used as a paper gate should be
   re-run blind before it is reported.

## What this does not settle
The blind task was absolute rating of an isolated cell; the non-blind
task was comparative judgment with the GT and condition rows in view.
These are different tasks, and the shift of the whole distribution
toward the worst score may partly reflect the loss of a reference. The
comparative claim, that an arm differs from its own matched baseline,
has therefore not had a fair blind test; that requires a paired design
with both cells side by side and labels hidden. Until then no
arm-quality claim may be drawn from human review on this window.

## Claim boundary
One window, one seed (bank0), one attempt, single reviewer with prior
exposure to the same images, ten trials, one camera cell, absolute
rating. Scene content was recognizable; blinding hid arm identity only.
The permutation test is on n=10 with heavy ties and is not powered to
establish any ordering; it is reported to bound the claim, not to
support one. v9 remains protocol of record. Nothing here bears on
candidate70 or candidate2216.

## Consequences for the open decisions
- v10 adoption: the obstacle raised by finding 6 of the frame review is
  withdrawn. The decision returns to its prior state, with the detector
  under-count probe still open.
- The first-multi-frame-track claim rests on presence and continuity,
  which the blind pass does not contradict, and may still enter the
  paper caliber as stated.
- Arm-quality claims from human review on this window: none, pending a
  paired blind test.

## Follow-ups
1. Paired blind test (matched arm and baseline cells side by side,
   labels hidden) if any arm-quality claim is to be made from human
   review.
2. Detector under-count probe, unchanged: why does the evaluator
   recover 0-4 support frames on an actor visible throughout?
3. Audit which earlier manual reviews in experiments/ were non-blind
   and mark them, before any of them reaches the paper.
