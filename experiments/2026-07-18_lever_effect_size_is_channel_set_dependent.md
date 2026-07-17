# 2026-07-18 The +38 percent FT lever is +20 percent under the metric the code was meant to compute

The lighting channel that has been dead since 99ee69a4 would score 1.0 on every
case of every arm of the candidate70 lever benchmark. It separates no arm from
any other. Restoring it cuts the reported FT lift from +38 percent to +20
percent, because S_ctrl averages over whatever channels happen to be measurable
and a constant channel still compresses every gap through the denominator.

## Run set, identified and validated
2026-07-13_v9c_corrected_matrix_ft_and_dims_scale.md reports mean J over five
cases for exp_v9c_official_open_anchor, exp_v9c_ft6322_open_loop_bank0_v2 and
exp_v9c_official_open_dims1p5. Recomputing those means from the archives
reproduces the record: 0.310479 against 0.311, 0.428905 against 0.429, 0.399513
against 0.399. All three arms fingerprint to the candidate70 source window.

## Measurement
Brightness is the archived best view of each case, recomputed with the
evaluator's own layout and reader. S_ctrl_new adds the lighting channel the dead
block would have supplied. J_new = J_old + 0.3 * dS_ctrl.

    arm      case  view  bright  S_ctrl_old  S_ctrl_new    J_old     J_new
    anchor   m1      0   43.035     0.0       0.333333    0.200000  0.300000
    anchor   m2      1   55.650     0.5       0.666667    0.545779  0.595779
    anchor   m3      1   52.814     0.5       0.666667    0.406618  0.456618
    anchor   m4      0   37.247     0.0       0.500000    0.200000  0.350000
    anchor   m5      0   40.904     0.0       0.333333    0.200000  0.300000
    ft6322   m1      1   67.852     0.5       0.666667    0.533903  0.583903
    ft6322   m2      1   67.456     0.5       0.666667    0.423855  0.473855
    ft6322   m3      1   67.489     0.5       0.666667    0.420864  0.470864
    ft6322   m4      0   53.401     1.0       1.000000    0.565902  0.565902
    ft6322   m5      0   52.124     0.0       0.333333    0.200000  0.300000
    dims1p5  m1      1   54.665     0.5       0.666667    0.537281  0.587281
    dims1p5  m2      0   44.640     0.5       0.666667    0.423469  0.473469
    dims1p5  m3      1   52.991     0.5       0.666667    0.421947  0.471947
    dims1p5  m4      0   37.247     0.0       0.500000    0.200000  0.350000
    dims1p5  m5      0   40.953     0.5       0.666667    0.414868  0.464868

    arm      mean J old   mean J restored
    anchor    0.310479      0.400479
    ft6322    0.428905      0.478905
    dims1p5   0.399513      0.469513

    lever          lift old    lift restored   reported as
    ft6322        0.118425      0.078425       +38% -> +20%
    dims1p5       0.089034      0.069034       +29% -> +17%

## The channel carries no arm information and moves the lever anyway
Every brightness above is between 37.2 and 67.9, all below the 90.0 threshold, so
lighting_night scores 1.0 on 15 of 15 cases. It is identical for the anchor, for
FT and for dims. It cannot distinguish the arms and does not claim to. It still
removes a third of the lift, because S_ctrl is a mean and a constant added to a
mean of a smaller set moves each arm by a different amount: the anchor, sitting
lower, gains more. ft6322 m4 is the exception that shows the shape: its S_ctrl is
already 1.0, so a further 1.0 channel changes nothing.

The candidate162 windows show the mirror image. There the same channel scores 0.0
on 8 of 8, also identically across arms, and also compresses the m5 arm gap, by
21.3 percent. The sign of the channel is irrelevant. What moves the comparison is
that the channel set is variable and enters a mean.

## What this does and does not overturn
The direction of the FT lever survives: +20 percent is still positive, on the
same five cases, and 2026-07-18_c70_subtraction_probe.md separately established
that the FT arm's motorcycle detections are real and survive subtraction. The
lever is not a subtraction artifact and it is not a lighting artifact.

What does not survive is the effect size as a reportable number. +38 and +20 are
both products of which channels happened to be measurable on the day the run was
scored, and neither is more true than the other. A quantity that is constant
across the arms should not touch the arm comparison; under a mean over a variable
channel set, it does. Reviving the dead block would replace one arbitrary channel
set with another, so it is not the repair. The repair is to stop letting channel
availability into the arm comparison: score per channel, or fix the channel set
across arms, or exclude channels the bound source determines.

## Claim boundary
The restored numbers are counterfactual. They are what the archived runs would
have scored had the block executed, computed from the archived videos and metrics
by the same code path the evaluator uses. No run was re-executed and no GPU was
used. The recomputation of the archived means to three decimals is what licenses
treating them as the same runs the record describes.

The 90.0 threshold is not calibrated. It is not questioned here because it does
not need to be: every candidate70 case is far below it and every candidate162
case is above it, so the verdicts are not threshold-sensitive on either window.
On windows nearer to 90 they would be. NOT MEASURED for any other window.

2026-07-13_bank1_seed_replication_detectability.md quotes a bank1 mean J of 0.200
for the anchor and 0.293 for the stacked arm, and 2026-07-13_ft_dims_stacking_probe.md
quotes a stacked mean of 0.479. Those arms were not recomputed here, so the
effect of the channel on the stacking and seed-replication results is NOT
MEASURED.

## Method note
The first attempt at this measurement used exp_v9r1_ft6322_dims1p5_open and
exp_v9r1_official_open_anchor, on the reasoning that they fingerprint to the
candidate70 window and carry the right case names. They do, and they are the
wrong run set: the record names exp_v9c_*. The v9r1 arms give a per-case gap
change of -21.3 and -21.6 percent on m1 and m2, which is a real measurement of a
different run set and was nearly attached to the 0.311 -> 0.429 claim on the
strength of the window matching. Matching the window is not matching the run.
The archived means are the thing that identifies a run set, and checking them
against the record is cheap.
