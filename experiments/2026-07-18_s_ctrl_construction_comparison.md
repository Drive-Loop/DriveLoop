# 2026-07-18 What S_ctrl could be: five constructions on three windows, and the licence to ask the question

The +38 percent FT lever is one of five defensible numbers, and four of the
other four are smaller. This record measures all of them on the same archives
and does not choose between them. Choosing is a paper-scope decision and it is
currently entangled with a data defect: m4 is missing its motion plan, and
repairing it would collapse two of the five constructions into each other.

## The licence, and what it does not cover
Rescoring an archived run under a different S_ctrl is only meaningful if the
archive contains enough to reproduce the S_ctrl it was scored with. It does,
for the seven arms of the three windows: replaying control_visibility_score on
the archived metrics and scene specification reproduces the archived S_ctrl to
1e-9 on all 34 attempts, and archived J equals wp*S_perc + wc*S_ctrl +
wi*S_intent from the archived weights on every one of them. That is what
licenses moving S_ctrl and recomputing J.

    window         arms                                          cases  replay
    candidate70    exp_v9c_official_open_anchor                  m1-m5  5/5 exact
                   exp_v9c_ft6322_open_loop_bank0_v2             m1-m5  5/5 exact
                   exp_v9c_official_open_dims1p5                 m1-m5  5/5 exact
    candidate162   exp_v10w_candidate162_official_anchor         m1,2,3,5  4/4 exact
                   exp_v10w_candidate162_ft6322_dims1p5          m1,2,3,5  4/4 exact
    candidate2216  exp_v10w_candidate2216_official_anchor        m1,2,3,5  4/4 exact
                   exp_v10w_candidate2216_ft6322_dims1p5         m1,2,3,5  4/4 exact

The run set is identified by recomputing the archived means against the record,
not by the run name: 0.310479, 0.428905, 0.399513 against the values
2026-07-13_v9c_corrected_matrix_ft_and_dims_scale.md reports. Matching the
window is not matching the run (2026-07-18_lever_effect_size_is_channel_set_
dependent.md, method note).

The licence is scoped to these seven runs. Nothing else in the archive was
rescored and nothing else may be.

## The 53 archive-wide replay mismatches are a construction change, not damage
Replaying every run under the root produces 545 exact reproductions and 53
mismatches, all in exp_c70_closed_loop (9), exp_c70_closed_loop_v2 (8),
exp_c70_open_loop_baseline (5), exp_v3_closed_loop (9), exp_v3_closed_loop_
saturated (9), exp_v3_open_loop (5) and exp_v4_closed_loop_structural (8).

Every one of the 53 has archived S_ctrl exactly equal to control_coverage(plan).
beb1e2f (2026-07-07 05:30) says it in its own subject line: video-derived
automatic S_ctrl "replaces plan-level saturation in Eq.5". Those runs were
scored before it, took S_ctrl from the plan-level coverage, and coverage returns
1.0 when the plan carries no tags. Zero mismatches are unexplained.

The boundary is visible from both sides, which is what makes the harness
credible rather than merely passing. exp_v5, exp_v6 and exp_geometry_sweep ran
in the roughly five-hour window between beb1e2f (05:30) and 99ee69a4 (10:22) on
2026-07-07, archived perception_best_view_brightness, and replay reproduces them
because the archived brightness lets the lighting channel be recomputed. The v9c
runs postdate 99ee69a4, archive no brightness, and replay reproduces them too
because both sides exclude the channel. The same code reproduces both regimes.

## The five constructions
    C1 current      mean over whichever channels happened to be measurable
    C2 lighting on  C1 plus the channel 99ee69a4 killed, scored on the best view
    C3 fixed set    window-wide union of channels; a channel a case lacks scores
                    0 and still counts in the denominator
    C4 fixed + lit  C3 with lighting in the union
    C5 per channel  no mean and no denominator: each channel's arm difference

C3 is a window-wide union deliberately, not a per-case cross-arm union. A
cross-arm union does not repair m4: both of m4's arms lack motion primitives, so
both lack target_motion, so m4 keeps n=1 and keeps its double-weight swing. The
m4 defect is across cases, not across arms.

## FT lever, three windows, five constructions
ft6322 or ftdims against the official anchor. Every lift below is checked
against its own term decomposition and sums back exactly.

    window         C1 current        C3 fixed set      C2 lighting       C4 fixed+lit
    candidate70    +0.118425 +38.1%  +0.088425 +28.5%  +0.078425 +19.6%  +0.068425 +17.5%
    candidate162   -0.097612 -17.1%  -0.097612 -17.1%  -0.091147 -17.6%  -0.091147 -17.6%
    candidate2216  +0.000000  +0.0%  +0.000000  +0.0%  -0.075000 -27.3%  -0.075000 -27.3%

    dims1p5 against anchor, candidate70 only
                   +0.089034 +28.7%  +0.089034 +28.7%  +0.069034 +17.2%  +0.069034 +17.7%

C5 does not produce a J. What it produces is the shape:

    window         lever            channel           differs on  mean delta
    candidate70    ft6322/anchor    object_presence   2 of 5      +0.4000
                                    target_motion     0 of 4      +0.0000
    candidate162   ftdims/anchor    object_presence   1 of 4      -0.2500
                                    target_motion     2 of 4      +0.1207
    candidate2216  ftdims/anchor    object_presence   0 of 4      +0.0000
                                    target_motion     0 of 4      +0.0000

## What the table says that no choice of construction changes
The sign is window-conditional, not construction-conditional. candidate70 is
positive and candidate162 is negative under all five. The direction of the FT
lever survives every construction; only its size moves. That is the same shape
2026-07-18_c70_subtraction_probe.md established from detections, and it does not
depend on any denominator.

C3 differs from C1 on candidate70 alone. candidate162 and candidate2216 have no
missing channel, so their union changes nothing and C3 is C1 exactly. Within
candidate70, C3 moves only the ft6322 lever and not the dims1p5 lever, because
m4 scores S_ctrl 0.0 on both the anchor and the dims arm and 1.0 on the FT arm.
The m4 defect inflates the FT lever specifically.

On candidate162 the two channels point in opposite directions: object_presence
favours the anchor by 0.25 and target_motion favours ftdims by 0.12. Any mean
cancels them against each other. Only C5 reports them.

## The gate is open, and it is entangled with m4
Not decided here. The costs as measured:

C3 removes an artifact that is real: m4's single binary flip swings the full
range because it has one channel to divide by. It needs no video and is
reproducible from the archive alone. It does not touch the uncalibrated
threshold. Its cost is that "a missing channel scores 0" is itself a choice, and
an unkind one: m4 never requested a motion primitive, and C3 penalises it for
not showing what it never asked for. C3 patches a data defect rather than fixing
it.

Repairing m4 (adding the missing surface plan and re-running it) would give all
five cases two channels naturally, at which point C1 and C3 coincide and most of
this question dissolves. It needs GPU. It would shrink the lever, which is the
expected outcome and not a surprise.

C2 and C4 are not available: see 2026-07-18_lighting_revival_imports_view_
mismatch_and_threshold.md. Reviving the channel imports a view mismatch and an
uncalibrated constant, and on candidate2216 the two manufacture a 27 percent
regression out of a window where the detector detects nothing at all.

C1 keeps the m4 denominator in every J-based arm comparison, including the v10
adoption decision.

C5 is the most honest and produces no J, so it cannot support v10a/v10b
adoption on its own.

## Corrections to earlier claims
target_motion is not constant at 0.0 in general. That holds on candidate70
(4 of 4, no usable track) and was recorded without a window qualifier. On
candidate162 it carries arm signal: anchor m3 scores 0.22642 and ftdims m5
scores 0.709195, and it is the only channel on that window that favours ftdims.

exp_v10w_candidate2216_official_anchor exists and holds four cases with mean J
0.200000. The handoff's note that candidate2216's official arm was not measured
is wrong, or means something other than this run.

## Claim boundary
Arithmetic on archived metrics. No run was re-executed, no GPU, no video was
read for C1, C3 or C5. The counterfactual constructions are what the archived
runs would have scored had S_ctrl been defined differently; they are not
measurements of anything new about the models.

candidate2216's mean J of 0.200000 on both arms under C1 and C3 is not "no
difference between the arms". It is the detector floor: S_perc is 0 and S_ctrl
is 0 on all eight attempts, and J is entirely the S_intent term.
2026-07-18_three_window_metric_regimes.md established that the detector does not
detect the actor on that window at all.

The stacked arm of 2026-07-13_ft_dims_stacking_probe.md and the bank1 arms were
not rescored. NOT MEASURED.

## Method note
The first version of this harness demanded that every run in the archive replay
under today's code, and failed with 53 mismatches. The demand was wrong: the
archive spans months of code evolution and a construction change that the commit
history states outright. The licence that was actually needed is narrow, seven
runs, and it holds. A gate that fails for a reason outside its own question is a
badly posed gate, not a finding.

The prediction that candidate2216's lever would be 0.0 under every construction,
made from its C1 arm means being identical, was wrong. Under C2 and C4 it is
-27.3 percent. Identical arm means under one construction imply nothing about
another.
