# 2026-07-13 v10 probes: detector evidence is class-flipped and view-split, not absent

Four zero-GPU probes on the existing bank0/bank1 arm and baseline
videos (yolov8x via the protocol crop path; /tmp/v10_probe*.py) to
locate the J ceiling identified in the m2 dissection (no track
formation anywhere in the corrected matrix).

## Probe results
1. Baseline-subtraction fragmentation: ACQUITTED. Raw and surviving
   support are identical in 19 of 20 arm-case cells (one subtracted
   target detection in total). The differential is not eating tracks.
2. Confidence threshold: ACQUITTED. Lowering 0.20 -> 0.05 adds no
   near-miss reservoir; every observed hit already scores >= 0.25.
3. Scene-native motorcycle: ACQUITTED. Three of four no-injection
   baselines contain zero motorcycle detections in any view or frame
   (single exception: b0_ft6322 v5 f6 at 0.28). The multi-view hits
   in arm videos are injection products.
4. Class flip + view split: CONVICTED. With all labels visible, the
   injected actor is detected as motorcycle in some frames and person
   in adjacent frames or views (b0_ftdims m5 v1 f6: motorcycle 0.71
   and person 0.60 on the same object; b1_anchor m3 v1 f7: person
   0.52; several v5 entries pair person with motorcycle). Pooling
   {motorcycle, bicycle, person} across views along the maneuver path
   raises per-case support from 1-2 to 3-5 of 8 frames, in a
   left-rear -> front view progression consistent with the planned
   cut-in geometry. The cam_back person walls are real scene
   pedestrians and are correctly removed by the differential.

## Human review reconciliation
The reviewer confirms the frame-stepped review was of the generated
(bottom) mosaic row, so the human verdict stands: the actor is
persistently visible to a human in the generated row. The detector
sees it in 3-5 frames only, flipping between person and motorcycle -
consistent with the far-entry human verdict (person-like rendering)
and with 256x448 night crops sitting on yolov8x's class boundary.

## Consequences
1. The v9 metric (target class, selected view) undercounts rendered
   evidence: at bank1 the anchor arm renders detector-visible actor
   evidence in most cases (e.g. m3 person at front view f7) yet
   scored 0/5. Corrected lever claim: FT and dims scale raise the
   actor's target-class, target-view visibility; raw renderability
   shows no consistent lever ordering across banks.
2. The generation-side persistence deficit stands but shrinks: the
   actor is detector-visible in 3-5 of 8 frames cross-view, not 1-2.
   Human 8/8 versus detector 3-5/8 remains a detector-domain gap that
   evaluator work cannot fully close.
3. v10 design implied by the data: (a) a target super-class
   {motorcycle, bicycle, person} for existence, support and track
   evidence, with class fidelity (motorcycle share of super-class
   detections) as a separately reported term; (b) cross-view pooling
   restricted to maneuver-relevant views (target cams plus
   approach-side neighbors) to keep scene-person residue out
   (unsubtracted person noise exists in v3/v4); (c) differential
   subtraction unchanged; (d) tau re-anchored after rescoring all
   existing arms. Rescoring may reorder arms; the metric is chosen
   for semantic faithfulness, not to preserve v9 conclusions.

## Claim boundary
Probe-level analysis of existing videos; no protocol change yet; no
new generations. Cross-view support counts come from label pooling on
3 probed cases plus motorcycle-only sweeps on all 20 cells; v10
numbers do not exist until the scorer is implemented and everything
is rescored under it.
