# 2026-07-18 candidate162 manual frame review: injection is visible only under FT weights, and v10b ranks the arms inverse to human judgment

First frame-stepped human review of the new-window videos, closing the
gap left open by 2026-07-18_window_expansion.md. All ten candidate162
videos were reviewed: official-anchor and ft6322+dims1.5 arms on
m1/m2/m3/m5, plus both per-weight no-injection baselines.

## Method
Mosaic layout confirmed from the generator code and from every file:
2688x784, vertical stack [GT, COND, GEN], row height 260, pad 2; six
camera cells of width 448 per row, reference order FL,F,FR,BR,B,BL.
Only the bottom (generated) row is judged. Two exports: the bottom row
per frame for all ten videos, then per-frame GT/COND/GEN triplets of
the front cell (index 1) so that the actor read in GEN can be checked
against the target box carried in COND. Single reviewer, non-blind,
frame stepping over 8 frames per case. Human visual reading only; this
record is not an evaluator-caliber result.

## Findings
1. Target identity confirmed. The actor read in the generated row
   aligns frame by frame with the conditioned box in COND (checked on
   ftdims m5 and ftdims m2). The readings below concern the target
   actor, not another motorcycle already present in this scene. This
   check was necessary because candidate162 is a real-motorcycle
   source window.
2. Both paper gates pass. ftdims m5: motorcycle-like actor visible in
   8/8 frames, identity continuous (evaluator: track of 3, S_perc
   .523). anchor m3: 8/8 frames, continuous (evaluator: track of 2).
   The project's first multi-frame tracks are visually real, and human
   support exceeds detector support in both cells.
3. Human artifact ordering across arms: ftdims cases clean; official
   anchor cases deformed; both no-injection baselines deformed and
   smeared.
4. Injection has a human-visible effect only under FT weights.
   Matched-weight comparisons on m5: ft6322+dims1.5 versus the ft6322
   no-injection baseline differ clearly (baseline deformed and
   progressively darker, injected arm clean); official anchor versus
   the official no-injection baseline are indistinguishable, both
   judged bad.
5. Weights and dims remain confounded on this window. The ftdims arm
   carries FT weights and dims_scale 1.5; the anchor arm carries
   official weights and dims_scale 1.0. Finding 4 is attributable to
   the package, not to either knob alone. The two missing cells
   (official + dims1.5, ft6322 + dims1.0) would separate them.
6. v10b S_perc orders the arms inverse to human judgment on this
   window. Mean S_perc favors the anchor (.420 vs .266), while review
   finds the ftdims arm the only clean one and the anchor arm
   indistinguishable from no injection. The support term drives the
   gap: the anchor's evidence volume is detections on a visibly
   deformed actor, and the ftdims arm's low support is the detector
   missing a clean, box-aligned actor present in 8/8 frames. The
   under-count mechanism is not established and is not interpreted
   further here.
7. The candidate162 ftdims m2 zero is degradation, not absence. The
   actor renders on the conditioned box in all 8 frames, but the
   rider's head is flattened, the machine is deformed, and the
   generated row darkens across the sequence. The zero-detection cell
   is a detector floor on a degraded but present actor.

## Consequences
- The first-multi-frame-track claim may enter the paper caliber,
  stated as: in the near window the generated row renders a
  box-aligned motorcycle-like actor continuously, and the evaluator
  recovers 2-3 frame tracks. Human review is the gate; the evaluator
  number remains the reported number.
- The v10 adoption decision acquires an obstacle. On the only window
  with human review, the candidate protocol's arm ordering is inverse
  to the human gate. Adoption should not proceed until the support
  term weighting is examined or the under-count mechanism is
  understood.
- The bank1 recheck of ftdims m2 now tests degradation stability, not
  whether generation failed.

## Erratum to 2026-07-18_window_expansion.md
Finding 2 of that record reads the anchor's higher support as more
evidence and the ftdims arm's lower support as an evidence sacrifice
("trades evidence volume for label purity"). Frame-stepped review
shows both arms render the actor in 8/8 frames, so the support
difference is a property of the detector, not of the generated
content. The mean-S_perc preference for the anchor stated there must
not be read as a rendering-quality preference; human review prefers
the opposite arm. Finding 2 stands only as a statement about detector
output.

## Claim boundary
Single human reviewer, non-blind: arm identity was visible from folder
names, so the discrimination judgments in findings 3 and 4 are not
protected against expectancy. One window, one seed (bank0), one
attempt, n=4 cases per arm, one camera cell (front) reviewed, 8 frames
per case. Human visual reading is not evaluator caliber; detector
conclusions remain per the evaluator. v9 remains protocol of record.
Nothing here bears on candidate70 or candidate2216, and the
three-window matrix remains the minimum reporting unit for any lever
claim. The inverse-ordering finding rests on one window and should be
confirmed blind before it gates the v10 decision.

## Follow-ups
1. Blind A/B confirmation of the arm-versus-baseline discrimination
   (shuffled cells, key withheld) before finding 6 gates v10 adoption.
2. Detector under-count probe: why does the evaluator recover 0-3
   support frames on an actor visible and box-aligned in 8/8? Target
   attribution under dims_scale 1.5 is the first suspect.
3. Factorial cells to separate FT weights from dims 1.5 (official +
   dims1.5, ft6322 + dims1.0); m5 alone would do.
4. Human review of the candidate70 and candidate2216 windows, without
   which findings 3-6 cannot be generalized past this window.
