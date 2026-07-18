# 2026-07-18 Reviving the lighting channel imports a view mismatch and an uncalibrated constant, and on candidate2216 the two manufacture a 27 percent regression

The lighting channel has been dead since 99ee69a4 (2026-07-07 10:22).
2026-07-18_lever_effect_size_is_channel_set_dependent.md showed that restoring
it moves the candidate70 FT lever from +38 to +20 percent, and concluded that
reviving the block would replace one arbitrary channel set with another. That
conclusion was right and understated. Revival is worse than arbitrary: it is
incoherent, and the incoherence is measurable.

## What the revived channel would actually score
The killed block reads brightness from the BEST view:

    if best_view in brightness_map:
        metrics["perception_best_view_brightness"] = brightness_map[best_view]

S_perc does not come from the best view. It comes from the SELECTED view:

    metrics = dict(selected_evaluation.metrics)

where selected_view is the highest-scoring view among the target views when the
request names any, and falls back to best_view only when it does not. So a
revived lighting channel would score the scene's illumination on a different
camera than the one perception was scored on, whenever the two differ.

They differ often:

    window         best != selected
    candidate70    5 of 15   anchor/m1 anchor/m5 ft6322/m5 dims1p5/m2 dims1p5/m5
    candidate162   1 of 8    ftdims/m2
    candidate2216  8 of 8    every case of both arms

## The candidate2216 lever is the view mismatch, entirely
Recomputing the same lever with lighting taken from the selected view instead of
the best view (C6, and C7 for the fixed channel set):

    window         lighting on best view    lighting on selected view
    candidate70    +0.078425 (+19.6%)       +0.078425 (+19.6%)
    candidate162   -0.091147 (-17.6%)       -0.091147 (-17.6%)
    candidate2216  -0.075000 (-27.3%)       +0.000000  (+0.0%)

candidate70 and candidate162 do not move by a single digit. candidate2216 goes
to exactly zero. The entire -27.3 percent is the choice of camera. It carries no
information about the arms: its S_perc term is exactly 0.000000, on a window
where 2026-07-18_three_window_metric_regimes.md established the detector never
detects the actor at all.

The mechanism is visible per case. Three of the four candidate2216 anchor cases
sit below the threshold on their best view and above it on their selected view:

    case   b_best   verdict     b_sel    verdict
    m1     89.962   night 1.0   94.333   night 0.0
    m3     86.020   night 1.0   92.393   night 0.0
    m5     82.207   night 1.0   90.453   night 0.0

Every ftdims case is above the threshold on both views. So on the best view the
anchor collects lighting credit on three of four cases and ftdims on none, and
that gap is the whole lever.

## Both defects are inert until the window straddles the constant
candidate70 has the view mismatch on 5 of 15 cases and it changes nothing,
because every candidate70 brightness on either view is 22 to 53 units below the
threshold. The channel scores 1.0 whichever camera is asked. candidate162's one
mismatched case is 4.7 and 9.9 units above the threshold on its two views: 0.0
either way.

The mismatch only becomes load-bearing where a window's brightness straddles the
constant. candidate2216 is that window: 82.2 to 98.3, with 90.0 inside it.

    window         brightness range   straddles 90.0   view mismatch bites
    candidate70    37.2 - 67.9        no               no
    candidate162   92.4 - 100.7       no               no
    candidate2216  82.2 - 98.3        yes              yes, 8 of 8

## The threshold is load-bearing on two of the three windows
_NIGHT_BRIGHTNESS_MAX = 90.0 has never been calibrated. Sweeping it and
recomputing the FT lever:

    thr    candidate70        candidate162           candidate2216
           best / selected    best / selected        best / selected
    80-82  +0.07843 +0.07843  -0.09115 -0.09115      +0.00000 +0.00000
    83-86  +0.07843 +0.07843  -0.09115 -0.09115      -0.02500 +0.00000
    87-89  +0.07843 +0.07843  -0.09115 -0.09115      -0.05000 +0.00000
    90.0   +0.07843 +0.07843  -0.09115 -0.09115      -0.07500 +0.00000  <- current
    91-92  +0.07843 +0.07843  -0.09115 -0.09115      -0.07500 -0.02500
    93     +0.07843 +0.07843  -0.11615 -0.11615      -0.05000 -0.05000
    94     +0.07843 +0.07843  -0.14115 -0.14115      -0.05000 -0.05000
    95     +0.07843 +0.07843  -0.16615 -0.19115      -0.07500 -0.10000
    96-99  +0.07843 +0.07843  -0.16615 -0.19115      varies   varies
    100    +0.07843 +0.07843  -0.11615 -0.11615      +0.00000 +0.00000
    101-105 +0.07843 +0.07843 -0.09115 -0.09115      +0.00000 +0.00000

candidate70 is flat across the entire range. Its verdict does not depend on the
constant at any value between 80 and 105, because no candidate70 brightness comes
within 22 units of any of them.

candidate162 is not flat. Between 93 and 100 its lever nearly doubles, from
-0.091 to -0.166 or -0.191. Its insensitivity at 90.0 is a property of where 90
happens to sit relative to its 92.4-100.7 band, not a property of the window. A
constant nobody calibrated is being asked to sit outside a band it was never
checked against.

candidate2216 is not even monotonic. Both arms cross the constant at different
points, so the lever wanders between 0 and -0.10 and back.

## Reviving on the selected view does not rescue it
The obvious repair is to score lighting on the same view as perception. It gives
candidate2216 a lever of exactly 0.000000 at threshold 90.0, which looks like the
defect being removed. It is not. It is the same coin landing the other way:

    candidate2216 anchor m1  best view    89.962   0.038 below the threshold
    candidate2216 anchor m5  selected view 90.453  0.453 above the threshold

At 91.0 the selected-view lever is -0.025 and no longer zero. The zero at 90.0 is
worth 0.453 units of brightness. Coherent revival relocates the arbitrariness; it
does not remove it. Nothing that puts a hard threshold on a scene-level pixel mean
is safe on a window whose brightness sits on the threshold.

## The two flat regions prove the channel's value is irrelevant
On candidate162 the lever is -0.09115 at every threshold at or below 92, where the
channel scores 0.0 on all eight cases, and -0.09115 again at every threshold at or
above 101, where it scores 1.0 on all eight. The same number. A channel constant
across the arms compresses the arm gap by the same amount whether it is constantly
one or constantly zero, because what compresses is the denominator, not the value.
This independently reproduces the claim in 2026-07-18_lever_effect_size_is_channel_
set_dependent.md that the sign of the channel is irrelevant.

## Defect 3: upgraded from "not repaired" to "measured, and not repairable by revival"
The dead block was previously left alone on the judgment that it could not be
fixed by reviving it. That judgment now has evidence rather than only a reading of
the code:

1. It is unreachable and unrunnable. It sits after a return inside
   _maneuver_direction_check(self, metadata, centers), which has no metrics in
   scope. Reaching it would raise NameError. Its blast radius is four metric
   families, not only brightness: perception_view{i}_brightness,
   perception_best_view_brightness, perception_layout_views and
   perception_generated_row_height. The layout provenance the evaluator used was
   never archived either.
2. Revived on the best view, it manufactures a 27 percent regression on
   candidate2216 with a zero S_perc term.
3. Revived on the selected view, it is coherent and still arbitrary, by 0.453
   brightness units.

The code is left in place. It cannot execute, so it carries no runtime risk, and
it is the evidence for this record. Deleting it is a separate, optional cleanup.

## Claim boundary
Counterfactual arithmetic on archived metrics plus a brightness recompute from the
archived videos, by the evaluator's own layout and reader. No run was re-executed,
no GPU.

The brightness recompute is licensed on candidate70 and there only: the 15
per-case best-view values reproduce 2026-07-18_lever_effect_size_is_channel_set_
dependent.md to three decimals, 15 of 15, and the archived best_view matches the
view column of that record 15 of 15. candidate162 and candidate2216 brightness has
no recorded counterpart and is NOT independently gated. It is produced by the same
code path that reproduces candidate70 exactly, which is a reason to believe it and
not a check on it.

The layout is assumed to be CompositeVideoLayout's defaults (448 wide, 256-high
generated row, 6 views). The candidate70 gate would fail under a different layout,
which is what makes the assumption safe for that window. It is NOT independently
verified for candidate162 or candidate2216.

Whether the threshold should be 90.0 is not decided here. This record measures how
much each window's verdict depends on it, which is: candidate70 not at all,
candidate162 between 93 and 100, candidate2216 everywhere.

## Method note
The prediction that candidate162 would be flat across the sweep, made on the
grounds that its brightness is far from 90.0, was wrong. Far from the current
value of an uncalibrated constant is not the same as insensitive to the constant.
The window spans 92.4 to 100.7 and any threshold inside that band splits it; 90.0
merely happens to fall outside. The whole point of calling a constant uncalibrated
is that its current value carries no authority, so "far from 90" was never the
relevant distance.
