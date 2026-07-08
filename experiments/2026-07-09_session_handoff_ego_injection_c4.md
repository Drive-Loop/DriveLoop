# 2026-07-09 Session handoff: ego-frame injection, remaining step C4

## State (all pushed, main @ 2f178ef, 406 tests green)
- Evaluator integrity #6 (min_target_support_frames) and #7
  (baseline-differential subtraction) shipped with real-data
  acceptance; honest scores: prior grid highs were single-frame
  degenerate credit (~0.2 at yolov8x@0.20 with 1-frame support).
- Injection yaw slot fixed (#8): yaw belongs at box9 index 7
  (rotation about camera y); old code applied a spurious z-roll.
- driveloop_ego_injection.py (DD2 side): ego<->camera box transforms,
  verified zero-error against real cross-camera annotation pairs;
  anti-mirror sentinel test (ego y=+3.5 -> cam_front x<0).
- Left default geometry 3.5/20; right 3.2/9 pending gated re-audit.

## Remaining: C4 (last piece of the injection-surface uplift)
1. Override JSON: new surface boxes3d.per_frame_append_ego carrying
   ONE ego-frame entry per video frame
   ({center_ego, dims, heading_ego}, category, actor_id, frame
   mapping), emitted by DriveDreamer2Backend behind a flag
   (suggest env DRIVELOOP_EGO_INJECTION=1; default off until
   end-surface verified).
2. Consumption in drivedreamer2_transforms.py: override loaded in
   _load_driveloop_override (line ~56, env DRIVELOOP_DD2_OVERRIDE_JSON);
   application happens inside __call__ (line ~171+; note: the literal
   "per_frame_append" does NOT appear in this file - locate the actual
   apply code first). Each record has data_dict['calib'] with
   cam_intrinsic/cam2ego/ego2global; use
   driveloop_ego_injection.ego_entry_to_cam_box9 with the per-frame
   cam_front record's ego2global as reference. Audit rows must record
   the new mode.
3. End-surface verification order: audit-only run (all six cams get
   DISTINCT per-cam boxes) -> GPU replay of the archived night cut-in
   command -> ffprobe/YOLO probe -> human review.
4. Then v9 three arms with the new evaluator
   (--perception-weights yolov8x.pt --perception-confidence 0.20
   --perception-baseline-video <per-window no-injection baseline>),
   tau_v9 from the v9 open arm.

## Conventions (unchanged)
No Chinese in code; anchored /tmp patches (abort if anchor not
unique); full pytest before commit; English commit messages; push per
milestone; perception acceptance != semantic success; human spot
checks gate paper claims.
