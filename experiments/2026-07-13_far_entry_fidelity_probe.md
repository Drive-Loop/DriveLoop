# 2026-07-13 Far-entry fidelity probe: person-like at distance in both arms

Zero-GPU label probe on the far-entry verdict pair
(far_entry_verdict_official_v2 / far_entry_verdict_ft6322_v2; window
325cef68, FAR_ENTRY=35, mini val). No same-window no-injection
baseline exists, so no differential: the two arms share seed and
scene, cross-arm label differences are weight effects, and readings
are taken per cell rather than from aggregates.

## Results
The far-entry actor's cam_front cell: official reads person 0.37 at
f7 (plus fire hydrant 0.39 at f6); ft6322 reads person 0.78 at f7.
A motorcycle cluster at cam_back_left appears identically in both
arms (five detections at f0) and is scene-native; the aggregate
motorcycle share (0.421 official vs 0.464 ft) is dominated by it and
carries no actor signal.

## Findings
1. The far-entry actor is person-labeled in BOTH arms: the human
   far-entry verdict (person-like figures, no class-fidelity fix from
   FT) is now detector-confirmed. If anything, FT strengthens the
   person reading's confidence (0.78 vs 0.37).
2. Combined with the v10 rescore, the FT fidelity effect is
   range-dependent: near and mid-range injected actors flip toward
   motorcycle under FT and dims (candidate70 window), while the
   distant small actor stays person-like at epoch 1.
3. Input to the second-epoch decision: continuing FT is a well-posed
   fidelity experiment with two measurable endpoints (candidate70
   class fidelity via the rescoring harness; the far-entry cam_front
   label), but no current evidence predicts distant-actor
   improvement from more epochs.

## Claim boundary
Probe-level, not protocol: no differential subtraction, one window
pair, one seed, small label counts. The range-dependence claim rests
on two windows total and needs more windows before any promotion.
