# 2026-07-07 Geometry semantics: cross-view clones, mirrored maneuvers, side asymmetry

## Bugs found and fixed (evaluation-integrity cases 3-5)
1. Cross-view box duplication: injected per-frame boxes3d were mapped to
   ALL six cam_types and S_perc was max over all views. One requested
   actor rendered as six clones; the metric rewarded wrong-view
   detections. Fix: target_cam_types filtering + target-view S_perc.
   Sweep v1 numbers are diagnostic only.
2. Mirrored maneuver geometry (99ee69a): camera-frame box x positive is
   camera RIGHT (verified: injected x trajectory matches detected
   pixel-x trajectory). All 'left' requests rendered on the right;
   cut_in moved AWAY from ego (a cut-out). Fix: signed lateral side,
   approach trajectories, single-view injection (cam_front) pending
   extrinsics. v6 numbers are diagnostic only.
3. Direction-check distractor leakage (88d7fe1): the maneuver-direction
   check tracked all detections; distractors produced verdicts when the
   target was absent (m5). Fix: filter to target category.

## New capability
Automated maneuver-direction verification: detected pixel-x trajectory
of the target category in the selected view must match the requested
side (left -> moving toward image center). Mismatch fails diagnosis and
blocks semantic_success_claim_allowed. Reduces manual review to
paper-figure spot checks.

## Calibration evidence (clean metrics, single-pass, m1 prompt)
- RIGHT regime (exp_geometry_sweep_v2): winner lateral 3.2 / lon 9.0,
  S_perc 0.642, S_ctrl 1.0, rank-1 in both sweeps.
- LEFT side (exp_geometry_sweep_left): render window is closer and
  weaker. lon 5 all fail, lon 7 mostly fail; best base 2.0/9.0 with
  S_perc 0.462, Q_cov 0.125 at size 1.0.
- Size probe (exp_geometry_left_size_probe, lat 2.0 lon 9):
  size 1.25 -> Q_cov 0.125; size 1.5 -> Q_cov 0.375, direction
  consistent 1.0 (delta +32); size 1.75 -> Q_cov 0.125.
  Size 1.5 is the left-side rendering-strength sweet spot; kept as an
  escalation lever, not a default.
- v7 closed loop recovered m1 via escalation to S_perc 0.423 with
  direction consistency 1.0 (pixel delta +139): open loop fails on the
  left, closed loop recovers. This asymmetry is mechanism evidence, not
  a defect to calibrate away.

## Defaults after this session
lateral: 3.2 m (side >= 0) / 2.0 m (left), longitudinal: 9.0 m,
size_scale 1.0. Escalation ladder unchanged (relative scales over the
side-specific base; absolute overrides bypass it).

## Status of experiment series
- v1-v6: INVALID for paper (leakage / clones / mirror). Diagnostic only.
- v7: valid mechanism evidence (saturated == open loop exactly), but
  left-side geometry was uncalibrated; not paper-grade quality numbers.
- v8 (three arms, side-specific defaults): next session.

## Claim boundaries
- Perception acceptance is never semantic success; direction consistency
  is necessary, not sufficient (manual spot check gates paper claims).
- candidate70 left region is intersection/connector space (2026-07-02
  audit); left-side weakness may be scene-specific. Scenario-family
  expansion must re-verify both sides per source scene.
- m4_intersection_approach has no lane_change/cut_in primitive: no
  injection path exists. Scenario-family work, not a geometry issue.
