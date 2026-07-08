# 2026-07-08 Rendering quality is distance/bearing dependent; 0704 success decoded

## Geometry diff (override dumps, HEAD vs d4c23b6, audit-only, measured)
- 0704 cam_front injection: x +6.4 -> +8.8 (RIGHT side, moving OUTWARD,
  i.e. the mirror-era cut-out), z 20.0 -> 17.6 m.
- HEAD cam_front injection: x -3.6 -> -1.2 (left, approaching), z 11.0
  -> 8.6 m. The 2026-07-07 mirror fix is VINDICATED: current geometry
  is semantically correct; 0704 cam_front geometry was wrong.
- The human-passed "left cut-in" in the 0704 video was enacted by the
  CAM_FRONT_LEFT clone of the camera-frame box (all-view append era):
  a physically inconsistent clone accidentally rendered the requested
  semantics at 17-20 m range.

## Coverage probe (DRIVELOOP_INJECT_ALL_CAM_TYPES=1, diagnostic only)
Restoring 6-view append under current geometry does NOT restore render
quality (person 0.56-0.85, motorcycle single-frame 0.22). Multi-view
coverage is not the cause; the 2026-07-08 multiview-regression record's
"true per-view projections" wording is corrected by this record: the
0704 appends were same-box clones, not projections.

## Distance probe (geometry_left_distance_probe.json, single pass, clean metrics)
- lat 2.0 / lon 14: S_perc 0.365594 (person-blob rendering persists)
- lat 2.0 / lon 18: S_perc 0.414859
- lat 2.0 / lon 22: S_perc 0.426166
- lat 3.5 / lon 20: S_perc 0.488158 (left-side record high) with a
  motorcycle detection at 0.64 confidence; HUMAN REVIEW (tangzimo):
  recognizable motorcycle approaching from the left. First
  human-verified motorcycle from the synthetic injection path.

## Reading
- Renderer quality rises with injection distance and realistic lateral
  offset (adjacent-lane ~3.5 m) at the mini config; the 07-07 side
  calibration swept only lon 5-9 m, entirely inside the weak near
  range. "Left side renders weaker" is partially confounded with
  near-range weakness. Escalation ladder gains a distance axis.

## Claim boundaries
- Single pass, one scene, night, n=1 per grid point; motorcycle 0.64 is
  one frame (human-verified, coverage still thin). Not paper numbers.
- Detector night floor (same-day record) still applies to far/dim
  targets; human spot checks remain the gate.

## Next
1. 2D re-calibration sweep: lat 3.0-4.5 x lon 16-24, both sides.
2. Re-derive defaults and escalation ladder with the distance axis.
3. v9 three arms at re-calibrated geometry; tau from the v9 open arm;
   video spot checks before any claim.
