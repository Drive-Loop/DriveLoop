# 2026-07-18 candidate70 subtraction probe: the candidate162 defect does not generalize, and the FT lever survives

Follow-up 1 of 2026-07-18_w162_baseline_subtraction.md, run the same day. The
result narrows that record rather than extending it: candidate70 is a real-track
source-bound window and does not exhibit the defect at all. The fidelity-lever
result of 2026-07-13_v9c_corrected_matrix_ft_and_dims_scale.md survives.

## Measurement (selected view per case, 8 frames, five cases per arm)
    arm      raw_frm  kept_frm  moto_raw  moto_kept   archived mean J
    anchor      6        5          3         3          0.311
    ft6322      6        5          6         6          0.429
    dims1p5     9        6          5         5          0.399

Per case the archived subtraction counter was reproduced on CPU with delta +0
on 14 of 15 cases and -1 on one (ft6322 m3).

## Findings
1. The candidate162 mechanism does not generalize. On candidate70 the
   subtraction removes none of the target's motorcycle detections in the
   selected view: moto_raw equals moto_kept in all three arms (3/3, 6/6, 5/5).
   Support scarcity here is genuine detection scarcity, not subtraction: the
   raw frames carrying a superclass actor are 1-3 per case out of 8, against 8
   of 8 on candidate162.
2. The FT lever on candidate70 has content behind it. The FT arm renders twice
   the motorcycle detections of the official anchor (6 against 3) and every one
   of them survives subtraction. The mean J lift 0.311 -> 0.429 reported on
   2026-07-13 is not a subtraction artifact. The dims1.5 arm sits between them
   (5), consistent with the complementary-lever reading of that record.
3. The operative condition for the candidate162 defect is narrower than that
   record states. It is not that a window is real-track source-bound; it is
   that the no-injection baseline renders the same actor detectably at the same
   place. candidate162's near, prominent motorcycle meets that condition and
   the arm's own actor is deleted against it. candidate70's night, distant
   actor does not: there is no detectable baseline actor to coincide with. An
   erratum is filed against finding 7 of the candidate162 record.
4. The registered prediction failed. It held that the FT arm's lift would be
   explained by its baseline subtracting less. The FT arm's archived
   subtraction counter is higher, not lower (mean 75.4 against the anchor's
   70.0 and dims1.5's 71.0). Whatever the lift is, it is not that.
5. The lever is real and underpowered. It amounts to three extra motorcycle
   detections across five cases of eight frames, and per-case J moves on one or
   two surviving detections (m1 support 0 -> 2 carries J 0.200 -> 0.534). That
   is a power problem, not an artifact, and the two should not be conflated.
   The claim boundary of the 2026-07-13 record already restricts it to a single
   window, one seed, five cases and detector level; this probe does not loosen
   it.

## Method caveat
The baseline identification is weak on this window. Both candidate baselines
yield 84 detections and the subtraction counters they produce are often equal,
so the fingerprint does not separate them: ft6322 m2 matched the official
baseline and ft6322 m3 came out one off. Ties in the probe break toward the
first entry, so the reported match column is not reliable here. Because the
subtraction removes none of the target's detections under either pairing, this
ambiguity does not affect findings 1 and 2, but the candidate70 baselines are
not identified with the certainty the candidate162 ones were (delta +0 on 8/8
with cross-pairings separating cleanly).

## Claim boundary
One window (candidate70), the three v9c open arms, bank0 seed, one attempt per
case, five cases per arm, the archived selected view only, superclass counting.
Detector level only; no video semantic success claim. Findings 1 and 2 concern
what the metric does on this window and do not revisit the human-review
questions, which remain unaddressed on candidate70. candidate2216 is unprobed.

## Follow-ups
1. Probe candidate2216, the remaining window, whose floor result may be either
   mechanism or neither.
2. The metric question raised by the candidate162 record stands, but only for
   windows meeting the narrowed condition in finding 3. A cheap detector for
   that condition: run the detector on the no-injection baseline at the target
   box and see whether anything is there to subtract.
3. The candidate70 lever remains underpowered and should not be promoted to a
   default on three detections. Seed repeats would cost five generations per
   arm.
4. candidate70 videos have still not had frame-stepped human review.
