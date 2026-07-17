# 2026-07-18 candidate162: label-blind baseline subtraction invalidates the support term on real-track windows

The detector does not under-count. It detects the actor in every frame the
reviewer sees it in. The archived support figures of 0-3 are produced entirely
by the evaluator's baseline subtraction, which is label-blind and therefore
deletes exactly the detections that a class-fidelity improvement creates. On
this window the support term rewards deviation from the no-injection render.

## Provenance of the measurement
The runtime passed --perception-baseline-video into the evaluator constructor
and never archived it, so the baseline each arm used had to be recovered. It
was recovered by fingerprint: perception_baseline_subtracted_count is stored
per case, and recomputing that counter against each candidate baseline
identifies the one used. All eight arm cases matched their weight-matched
baseline exactly (delta +0 on 8/8: ftdims -> baseline_ft6322, anchor ->
baseline_official), and cross-pairings did not match. The recomputation ran on
CPU with yolov8x at confidence 0.20 against the archived GPU numbers, so the
evaluation path is also confirmed deterministic across devices for this input.

Do not use metadata['baseline_video'] for this purpose. That key holds the DD2
tester scratch output, which is the arm's own render before it is copied to
artifacts. Using it as a perception baseline would subtract every detection
against itself and manufacture a perfect confirmation of the finding below.

## Measurement (front view, per case, 8 frames)
    arm     case   raw_frm  kept_frm  archived_support  moto_raw  moto_removed  moto_kept
    ftdims  m1        8        1            1              10          9           1
    ftdims  m2        7        0            0              10         10           0
    ftdims  m3        8        2            2              10          8           2
    ftdims  m5        8        3            3              10          7           3
    anchor  m1        8        3            2               4          2           2
    anchor  m2        8        3            2               8          6           2
    anchor  m3        8        4            3               7          4           3
    anchor  m5        8        4            3               5          2           3

raw_frm counts frames carrying any superclass detection before subtraction;
kept_frm counts them after. The ftdims kept_frm equals the archived support in
all four cases. The anchor kept_frm sits one above it in all four, because
kept_frm counts the superclass while support counts target labels after the
evaluator's own filter, and the anchor keeps a bicycle or person frame the
target filter drops. The offsets are systematic and explained, not error.

## Findings
1. The detector detects the actor in 8/8 frames (7/8 on ftdims m2) in every
   arm case. This matches the frame-stepped human reading exactly. The human
   and the detector never disagreed; the subtraction sits between them.
2. Support is subtraction output, not detection output. Every archived support
   figure is reproduced by subtracting the weight-matched baseline from the
   raw detections, and by nothing else.
3. The subtraction is label-blind. _subtract_baseline drops any detection
   reaching IoU >= 0.5 with any baseline detection in the same view and frame,
   regardless of label. The baseline of this window renders the same real
   motorcycle and yolov8x labels it person; the ftdims arm labels the same
   actor motorcycle at IoU 0.67-0.98 against that person box, and the
   motorcycle detection is deleted. Correcting person to motorcycle on a real
   actor is invisible to the metric by construction.
4. The ft6322+dims1.5 arm renders a markedly more motorcycle-readable actor
   than the official anchor: motorcycle detections raw 10/10/10/10 versus
   4/8/7/5, i.e. 40 against 24 over the four cases. After subtraction it keeps
   6 where the anchor keeps 10. The arm whose actor is more faithful and
   better aligned to the real track is penalized precisely for that alignment.
   v10b's preference for the anchor on this window (mean S_perc .420 vs .266)
   is a consequence of subtraction geometry and carries no information about
   rendering content or class fidelity.
5. What survives subtraction is geometric accident. The ftdims detections that
   remain are lower-body boxes (y0 around 184 against 134 for the full actor)
   whose IoU lands at 0.34-0.48, just under the threshold. The support term on
   this window measures box-extent jitter relative to the baseline.
6. The ftdims m2 zero is solved and is not seed variance. That case renders and
   detects the actor in 7/8 frames with 10 motorcycle detections, and all 10
   are removed by subtraction. The bank1 seed recheck listed as an open item is
   moot and should be closed.
7. The subtraction is not wrong in general. For a window where injection adds an
   actor absent from the baseline, subtracting the baseline correctly removes
   scene clutter and keeps the new actor. The defect is specific to real-track
   source-bound windows, where the injection reinforces an actor the baseline
   already renders, and there is by definition nothing for the subtraction to
   leave behind. All three current windows are of that kind.

## Consequences
- Every candidate162 S_perc, under v9 and under v10b, is contaminated: its
  support term measures subtraction geometry on an actor present in both arm
  and baseline. The arm ordering on this window carries no content claim.
- 2026-07-18_window_expansion.md finding 2 ("the ft+dims arm trades evidence
  volume for label purity") is now explained and inverted: the arm produces
  more label-pure evidence, and the subtraction removes it for coinciding with
  the baseline. The mean-S_perc preference for the anchor reported there
  measures the anchor's deviation from its baseline.
- The v10 adoption decision cannot proceed on the current matrix. The candidate
  protocol inherits the same subtraction from the v9 evaluator, so re-anchoring
  tau or recomposing J will not address this.
- The scope beyond this window is unmeasured. candidate70 and candidate2216 are
  also source-bound real-track windows and are the basis of the fidelity-lever
  narrative and of the protocol of record. They need the same probe before any
  claim resting on their S_perc is reported.

## Reproducibility defects found in passing
1. --perception-baseline-video decides the support term and is not archived
   anywhere: not in metadata, result.json, or summary.json. It survives only in
   shell history, and the candidate162 invocations are not in the history that
   remains. The pairing here was recovered by fingerprint, which works only
   because the subtraction counter happens to be stored. Fix: record the
   resolved perception baseline path in generation metadata.
2. metadata['baseline_video'] is a name collision. It holds the DD2 tester
   scratch output, i.e. the arm's own render, and it points at a transient path
   that is overwritten by every subsequent run. An auditor reaching for the
   obvious key gets the arm's own video as its baseline and a fabricated
   confirmation of any subtraction hypothesis. Fix: rename to something like
   dd2_raw_output_video.

## Claim boundary
One window (candidate162), one seed (bank0), one attempt per case, four cases
per arm, front view only, superclass counting. The fingerprint identification
is exact on 8/8 cases and the support reproduction is exact on the four ftdims
cases and systematically explained on the four anchor cases. Nothing here is
measured on candidate70 or candidate2216; the scope claim in the consequences
above is a suspicion to be tested, not a result. This record concerns what the
metric measures; it makes no claim about video semantic success, and the
detector remains the only caliber for detector conclusions.

## Follow-ups
1. Run this probe on candidate70, the protocol-of-record window and the basis
   of the fidelity-lever chain, before any lever claim is reported.
2. Then candidate2216, whose floor result may be the same artifact.
3. Decide the metric question the probe raises: on a real-track window, what
   should the support term count? Options include label-aware subtraction,
   subtraction restricted to non-target classes, or an explicit
   reinforcement-mode metric that compares fidelity against the baseline
   instead of subtracting it.
4. Close the bank1 seed recheck of ftdims m2 as answered by finding 6.
5. Archive the resolved perception baseline path and rename the colliding key.
