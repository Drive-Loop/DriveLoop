# 2026-07-18 The candidate windows are not night; S_ctrl scores a control the pipeline cannot exert

The candidate162 and candidate2216 windows are not night. Their source rows
measure 102.2 and 105.1. Only the prompt says night, and the run is source-bound,
so the lighting was never the pipeline's to control. S_ctrl's lighting channel
was scoring a request that could not be satisfied, which changes what should be
done about the dead brightness block recorded earlier: it should not simply be
revived.

## Measurement method, validated first
Brightness is recomputed from the archived videos with the evaluator's own layout
and frame reader, so the path is the same one the live code used before 99ee69a4.
On the pre-regression cohort it reproduces the archived value exactly on 4/4:
36.212, 42.894, 36.502 and 43.877, each matching perception_best_view_brightness
on its own archived best view. The J weights are confirmed the same way:
0.5*S_perc + 0.3*S_ctrl + 0.2*S_intent reproduces the archived J on 8/8
candidate162 cases.

## The bracket collapses, and it collapses the other way
The earlier record carried a bracket because the brightness of these windows had
never been computed. Measured on the archived best view of each arm:

    arm       case  view        brightness  dS_ctrl     dJ
    ftdims    m1    cam_front      100.652  -0.166667  -0.050000
    ftdims    m2    cam_front_left  94.697   0.000000   0.000000
    ftdims    m3    cam_front       99.980  -0.166667  -0.050000
    ftdims    m5    cam_front       99.131  -0.284866  -0.085460
    anchor    m1    cam_front       94.825  -0.166667  -0.050000
    anchor    m2    cam_front       94.954  -0.166667  -0.050000
    anchor    m3    cam_front       93.408  -0.204403  -0.061321
    anchor    m5    cam_front       92.356  -0.166667  -0.050000

Every value is at or above the 90.0 night threshold, so lighting_night would
score 0.0 on 8/8 and dJ is negative or zero throughout. The earlier record
guessed the sign would be positive by extrapolating from the 2026-07-07 windows
at 36-43. It labelled that extrapolation as not measured for candidate162, and
the extrapolation was wrong.

## The windows are not night
The DD2 mosaic is 784px tall and stacks source and condition rows above the
generated row. The top 256px band, measured on the cam_front column:

    c162  no-injection baseline, official weights   102.199
    c162  no-injection baseline, ft6322 weights     102.199
    c162  arm m1, official weights                  102.199
    c162  arm m1, ft6322 weights                    102.187
    c2216 no-injection baseline, ft6322 weights     105.081
    07-07 geo_lat3p2_lon12p0                         56.362

The top band is identical to three decimals across the candidate162 baseline and
both arms. Neither injection nor a change of weights moves it, which is what a
source row should do and what a generated row should not. The candidate162 source
window sits at 102.2 and the 2026-07-07 window at 56.4: these are different scene
classes, both declaring lighting == 'night' because both prompts asked for night.

environment.lighting comes from the requested prompt, not from the bound source
window. On a source-bound run the lighting is fixed by the source, so 'night' in
m1_night_cut_in_left, m2_rainy_night_cut_in and m5_low_visibility_cut_in is a
nominal label, not a realized condition. The three-window matrix should be
described accordingly.

## Reviving the dead block would dilute, not measure
Restoring the block gives every candidate162 and candidate2216 arm a channel
worth 0.0, whose only effect is to move the mean's denominator from 2 to 3. The
cost is measurable on the arm gap that carries the lever claim. On m5, ftdims J
0.717901 and anchor J 0.551289 give a gap of 0.166612; after restoration the gap
is 0.131152, a 21.3 percent reduction, produced entirely by the denominator.

The threshold makes it worse rather than better. At 90.0 it cuts through the
middle of this window's brightness cluster: the official baseline is 88.410 and
its own m5 arm is 92.356, four points apart and on opposite sides. Worse, the
weights themselves move brightness: the same candidate162 window renders at
101.522 under ft6322 and 88.410 under official, a 13-point gap from weights
alone, aligned exactly with the arm axis the comparison uses. A channel decided
by that is a confound, not a control measurement.

The upstream defect is that control_visibility scores lighting at all on a
source-bound window. The repair belongs there: either exclude channels the bound
source fixes, or score lighting against the window's own no-injection baseline
instead of an absolute constant. Reviving the block before that would restore a
broken channel and pay a real cost in arm separation.

## Claim boundary
Brightness here is the mean of a 448x256 view. It is not a photometric night
detector, and headlights, sky or road surface can lift it. What it supports is
the contrast between 56.4 and 102.2 source rows and the position of the 90.0
threshold relative to each, not an absolute verdict on any single frame.

Calling the top band the source row is inferred from its invariance across
injection and weights, not read from the DD2 tester's mosaic specification. NOT
VERIFIED against that code.

candidate70 is the window the handoff describes as the night one, and it has no
composite runs under that name, so none of this is measured on it. If its source
row resembles the 2026-07-07 cohort then the lighting channel may behave
differently there, and the conclusion above may not transfer. NOT MEASURED.

## Method note
The band probe sliced at 0, 256 and 512 while the generated row starts at 528,
because 784 is not a multiple of 256. Its third band therefore mixed 16px of the
condition row with 240px of the generated row and is not quoted anywhere here.
The top band lies wholly inside the source region and is unaffected. Every
generated-row number in this record comes from layout.extract_view, not from that
band probe.
