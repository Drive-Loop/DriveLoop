# 2026-07-18 candidate2216 probe and the three-window picture: S_perc sits in a different regime on each window

The last of the three windows is probed. Nothing about it resembles
candidate162, and it is candidate70's pattern in extreme form. With all three
measured, the useful result is not any single window's number but the fact that
the same metric is measuring a different thing on each of them.

## candidate2216 measurement (selected view, four cases per arm, 8 frames)
    arm      raw_frm  kept_frm  moto_raw  moto_kept
    ftdims      4         3         0         0
    anchor      2         2         0         0

Per case raw_frm is 1 and kept_frm is 0 or 1. The archived subtraction counter
reproduced with delta +0 on all eight cases, and the fingerprint separated the
baselines cleanly (they differ: 12 detections against 9), so the weight-matched
pairing is identified here with the same confidence as on candidate162.

## Findings
1. candidate2216 is at the detector floor because the detector does not detect
   the actor, not because anything removes it. raw_frm is 1 of 8 per case and
   kept_frm tracks it; moto_raw is 0 in all eight cases in both arms. The
   subtraction is irrelevant on this window.
2. The class fidelity of 0.0 reported for this window in
   2026-07-18_window_expansion.md does not mean the actor is detected and
   mislabelled. There is no motorcycle detection at all to be right or wrong
   about; the one or two superclass detections present are person or bicycle.
   Fidelity 0.0 over a support of 1 is a statement about a single non-target
   detection.
3. The candidate2216 baselines are nearly empty to the detector: 12 and 9
   detections across 48 view-frames, against 52 and 54 on candidate162 and 84
   and 84 on candidate70. The scene renders very little that yolov8x
   recognises. This is consistent with the narrowed condition of
   2026-07-18_c70_subtraction_probe.md finding 3: subtraction can only bite
   where the baseline renders the same actor detectably.
4. The registered prediction held, the first of four registered today. It said
   candidate2216 would resemble candidate70 with raw frames of 1-3 per case and
   little removed by subtraction. Observed: raw_frm 1 per case, kept_frm
   tracking it, subtraction removing none of the target.

## The three-window picture
    window     baseline dets  target raw_frm  moto_raw  subtraction on target
    c70          84 / 84         1-3 of 8       3-6        removes none
    w162         52 / 54         8 of 8         40         removes most
    2216         12 / 9          1 of 8         0          nothing to remove

    window   what S_perc's support term is actually measuring there
    c70      detector sensitivity to a scarcely-detected rendered actor
    w162     box-extent jitter of the arm's actor against the same actor in
             the baseline; the label correction the lever produces is deleted
    2216     nothing; every cell is at floor

5. The same metric is in a different regime on each window. On candidate70 the
   support term carries a signal, small as it is, and the FT lever is visible
   through it. On candidate162 the support term is dominated by subtraction
   geometry and the lever is invisible by construction. On candidate2216 there
   is no signal to measure at all.
6. Consequence for the reporting unit. The three-window matrix remains the
   minimum reporting unit for a lever claim, but the mean across it is not a
   meaningful quantity: the three cells do not measure the same thing, so
   averaging them averages a sensitivity, a jitter, and a floor. Windows must
   be reported individually with their regime named. Any earlier statement of
   the form "mean S_perc across windows" should be read as an artifact of
   presentation, not a measurement.

## Claim boundary
One seed (bank0), one attempt per case, four cases per arm on candidate2216,
the archived selected view only, superclass counting, detector level. The
regime table summarises three probes each with its own boundary; the candidate70
row carries that record's weak baseline identification, the candidate162 row is
identified exactly. No video semantic success claim is made or implied.
candidate2216 has had no frame-stepped human review, and neither has
candidate70; only candidate162 has, and its arm-quality judgments did not
survive blinding.

## Follow-ups
1. The metric question is now well posed and confined: it concerns windows in
   the candidate162 regime only. A cheap regime detector exists and should be
   run before any window is admitted to the matrix: detect on the no-injection
   baseline at the target box and count what is there to subtract.
2. Deciding the metric for the candidate162 regime remains open. Options
   include label-aware subtraction, subtraction restricted to non-target
   classes, and an explicit reinforcement-mode metric that compares fidelity
   against the baseline rather than subtracting it.
3. candidate2216 cannot support any lever claim in either direction and should
   not be counted as evidence for or against one. Its value in the matrix is as
   a floor case that identifies where the pipeline stops working at all.
4. The v10 adoption decision should not be taken on a mean across these three
   windows.
