# 2026-07-08 Left default -> 3.5/20; target attribution via baseline differential

## Baseline-differential evidence (deterministic generation)
Same window, only difference is injection. yolov8m@0.20, cam_front, f08:
- no-injection baseline (m4 artifact): person 0.65 at [160,71,228,204]
  (pre-existing source-region object; present in ALL cases).
- left 3.5/20: SAME source object (person 0.43 [165,83,222,193]) PLUS an
  additional motorcycle 0.64 at [175,159,226,207], consistent with the
  injected trajectory's projection (~10 deg left of center at 20 m).

## Attribution caveat
The injected location spatially coincides with the pre-existing source
object; the injection deterministically re-rendered that region into a
human-recognizable motorcycle. Valid for "generate a motorcycle cut-in
video"; NOT sufficient for an "inject anywhere" claim.

## Decisions applied
- LEFT default geometry: lateral 3.5 / longitudinal 20.0 (code +
  tests updated). RIGHT unchanged at 3.2/9: no human-verified right
  cell exists (far-range cells render a small lump; the historical
  0.642 at 3.2/9 was never human-reviewed and is on the audit list).
- Escalation ladder unchanged: size-1.5 sweet spot was measured at the
  old base; re-validate at the new base before touching it.

## Evaluator upgrade required before v9 analysis (integrity #7)
1. Target gating: only detections near the injected trajectory's
   projected pixel location may earn target-category credit.
2. Baseline-differential scoring: subtract detections present in the
   no-injection baseline video of the same window (determinism makes
   the baseline exact and reusable; this record is the method's first
   application).
3. Pair with #6 (multi-frame support) and detector upgrade (yolov8x).

## Injection-surface uplift (DriveDreamer-2 paper, AAAI-25)
DD2 derives 3D boxes from WORLD-frame agent trajectories and projects
them per camera onto the unified multi-view image canvas; conditioning
is image-plane box canvases. Our camera-frame per-record injection
sits below the intended interface (explains mirror/clone/single-view
pathologies and the distance-distribution effect). Plan: synthesize
world-frame trajectories from motion primitives and reuse the
runtime's own boxes3d -> image_box projection path
(image_box.mode=derive_from_boxes3d_after_override); audit calibration
fields in runtime records first.

## Claim boundaries
Single scene, night, n=1 per cell; human review covers left 3.5/20,
right 3.0/20 and 4.5/16 (lumps), the no-injection baseline, and the
0704 artifact. No paper numbers from today's grids until gated,
baseline-differential re-scoring exists.
