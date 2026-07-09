# 2026-07-09 C4 ego-frame injection surface: shipped + end-surface verification

## Shipped (commits 0c29398, ce3eaf4; 415 tests green)
- New override surface boxes3d.per_frame_append_ego behind
  DRIVELOOP_EGO_INJECTION=1 (default off): backend emits ONE ego-frame
  entry per video frame ({center_ego, dims, heading_ego}, category,
  actor_id, ref cam_front ego2global, all-cam sample identities);
  legacy per-cam clone surface suppressed when active.
- Consumption in driveloop.dd2_override: each camera record converts
  the entry into its own frame via ego_entry_to_cam_box9 with the
  record's calib (cam2ego/ego2global confirmed present at runtime,
  (4,4) each). Audit mode per_frame_append_ego.
- Behind-camera cull at consumption (center cam z <= 0), reason
  behind_camera_culled: required because the DD2 transform asserts
  mean corner depth > 0 BEFORE the z>0.5 crop (first audit-only run
  crashed on that assert; fix verified).
- Ego math moved to driveloop/ego_injection.py (shim kept at old
  DD2-side path); emission->consumption cam_front round trip and
  anti-mirror sentinel covered end-to-end in tests.

## Audit-only end-surface evidence (c4_ego_injection_audit_only)
- 48 override-audit rows (8 frames x 6 cams), candidate70 source-bound
  window, DRIVELOOP_EGO_INJECTION=1.
- cam_front / cam_front_left / cam_front_right: 8/8 frames accepted,
  per-cam boxes DISTINCT (17 distinct boxes3d sum deltas across cams).
- cam_back / cam_back_left / cam_back_right: 8/8 culled as
  behind_camera_culled (forward actor invisible to rear cams).
- Emitted trajectory varies per frame (center_ego x 23.66->21.27,
  y 5.24->2.83: left cut-in approaching). Note: cam_front per-frame
  sum delta is constant (23.35) because the maneuver's lateral and
  longitudinal linspace spans cancel in the component sum; verified
  equal to the per-frame plan box sums (exact round trip), not a
  static-injection bug.

## GPU replay (c4_ego_injection_gpu_replay)
- Archived night motorcycle cut-in command replayed with the ego
  surface on; video generated (2688x784, 8 frames, 4 fps).
- YOLO probe yolov8x@0.20: zero detections in all views. Consistent
  with the documented night detector floor (2026-07-08); probe-only,
  no baseline differential run yet.
- Human review (single reviewer): motorcycle visible cutting in from
  the left, frame-to-frame coherent motion; rendering quality mediocre
  ("pasted-on" look). The actor is generated under box conditioning,
  not composited; the look is the known mini-checkpoint rendering
  ceiling (v8 honest baseline), not a loop-mechanics failure.

## Claim boundary
Mechanism-level success only: the ego-frame injection surface is
verified end to end (per-view geometry, per-frame motion, audit
integrity). NOT semantic success, NOT perception acceptance; no
S_perc numbers claimed from this session. v9 three arms with the new
evaluator (baseline-differential, tau_v9 from the v9 open arm) remain
next per the 2026-07-09 handoff step 4.
