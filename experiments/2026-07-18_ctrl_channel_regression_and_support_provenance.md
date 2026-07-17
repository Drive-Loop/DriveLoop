# 2026-07-18 S_ctrl lost its lighting channel on 2026-07-07; support provenance now archived

S_ctrl stopped measuring lighting on 2026-07-07 and nobody could see it, because
the evaluator's channel breakdown is computed and then discarded. The two
provenance defects recorded on 2026-07-18 are fixed in d0f8f22. Auditing them
surfaced two more, one of which changes reported numbers.

## The regression, dated
The block that writes perception_view*_brightness, perception_best_view_brightness,
perception_layout_views and perception_generated_row_height belongs at the end of
CompositePerceptionVideoEvaluator.evaluate(). It reads that method's locals
(metrics, best_view). It is currently the tail of _maneuver_direction_check(),
after that method's unconditional return, so it never executes; if it ever did it
would raise NameError.

Reachability was tested by AST on every commit that touched the file:

    beb1e2ff  2026-07-07  video-derived automatic S_ctrl                LIVE
    17983a45  2026-07-07  Fix cross-view duplication of injected actor  LIVE
    99ee69a4  2026-07-07  Fix mirrored maneuver geometry               DEAD
    88d7fe18  2026-07-07  Filter maneuver-direction check to category  DEAD
    19347114  2026-07-08  Add evaluator integrity guards               DEAD
    5bc6d19e  2026-07-17  Add v10b maneuver view restriction           DEAD

99ee69a4 introduced _maneuver_direction_check above the block and left it inside
the new method. The commit changed no line of the block itself, which is why
git log -S does not find the breakage.

The archives agree exactly. 115 json files carry perception_best_view_brightness
and every one has mtime 2026-07-07. 335 json files carry
perception_baseline_available, i.e. the composite evaluator ran, dated 2026-07-09
(75), 2026-07-10 (59), 2026-07-13 (165) and 2026-07-18 (36). The two sets do not
intersect.

## Why the archives looked silent
control_visibility_score returns score, channels, unmeasured, source and a claim
boundary. The runner keeps score and source and drops the rest, so no artifact
records which channels produced an S_ctrl. Zero json files contain
auto_control_visibility; zero contain S_ctrl_source. The reported S_ctrl of 0.5
in the 2026-07-13 records therefore has no recorded channel composition: it had
to be reconstructed offline to be read at all.

## Effect on the three-window matrix
Reconstructed offline from the archived scene_specification, condition plan and
metrics. The reconstruction reproduces every archived S_ctrl exactly on 8/8
candidate162 cases, which is what licenses the rest of this section.

All eight candidate162 cases have environment.lighting == 'night'. The lighting
branch is reached, finds no brightness, and lands in unmeasured=['lighting.night'],
excluded from the average. Archived S_ctrl is therefore a two-channel mean:

    m1 ftdims   0.5       = mean(object_presence 1.0, target_motion 0.0)
    m2 ftdims   0.0       = mean(0.0, 0.0)
    m3 ftdims   0.5       = mean(1.0, 0.0)
    m5 ftdims   0.854598  = mean(1.0, 0.709195)
    m1 anchor   0.5       = mean(1.0, 0.0)
    m2 anchor   0.5       = mean(1.0, 0.0)
    m3 anchor   0.61321   = mean(1.0, 0.22642)
    m5 anchor   0.5       = mean(1.0, 0.0)

The pre-regression cohort is the control. exp_geometry_sweep runs the same
environment.lighting == 'night', carries measured brightness (36.212, 42.894) and
records S_ctrl 0.666667 = mean(1.0, 0.0, lighting_night 1.0) and 0.816621. Same
scene class, same channel definitions, three channels before 2026-07-07 and two
after. S_ctrl and J are not comparable across that date.

Restoring the block would not shift S_ctrl by a constant. Because the score is a
mean over a variable channel set, the shift depends on the other channels:

    brightness 50 (night, channel passes)   dS_ctrl +0.048 to +0.333, dJ +0.015 to +0.100
    brightness 100 (night, channel fails)   dS_ctrl -0.285 to  0.000, dJ -0.085 to  0.000

Arm-dependent shifts change the gaps between arms, not just their levels. The
2026-07-13 lever result is an arm gap, so this is decision-relevant for the v10
adoption question rather than cosmetic.

## Claim boundary
The true brightness of the candidate162 windows is NOT MEASURED. The dead block
never computed it, so 50 and 100 are brackets, not estimates, and the sign of the
effect on those windows is unknown. The 2026-07-07 night windows measured 36-43,
below the 90.0 threshold, but that is a different window set and does not
transfer. Collapsing the bracket to a point estimate needs only CPU: decode the
archived generated rows and take the view mean.

Within the 2026-07-09 and later cohort every run shares the same two-channel
S_ctrl, so comparisons inside that cohort stay internally consistent. What is
invalid is any comparison of S_ctrl or J across 2026-07-07, and any claim that
S_ctrl measured lighting after that date. The failure is fail-safe in the sense
that an unmeasured channel is excluded rather than counted as passed, so no
published claim is overturned by it.

Reviving the block changes the definition of a reported metric. It is a paper
gate decision, not a silent bug fix, and it should follow the brightness
recomputation rather than precede it.

## What landed
d0f8f22 fixes only the two 2026-07-18 provenance defects and changes no metric.
The evaluator exposes resolve_baseline_video() as the single resolution point and
the runner archives perception_baseline_video_resolved and
perception_baseline_video_exists into generation metadata. metadata['baseline_video']
becomes dd2_raw_output_video. 483 tests pass, 476 before plus 7 new.

348 archived json files still carry the old baseline_video key. The warning in
2026-07-18_w162_baseline_subtraction.md remains correct for those archives and is
deliberately left unedited.

## Method note
Two predictions in this audit were stated ahead of their evidence and both were
falsified by the next probe. First: "the metric was never emitted", contradicted
by 115 files carrying it. Second: "the channel-set shift is an established fact",
whose own stated test failed, because the unmeasured list is never archived; the
claim only became true after the offline reconstruction reproduced the archived
S_ctrl. The reachability of a code path is not evidence about what the archives
contain, and reasoning forward from code to consequences produced a plausible and
wrong story twice in a row. Probe first, generalize after.
