# 2026-07-08 Multi-view conditioning regression and detector night floor

## Human re-review of the 07-04 artifact
Frame-level manual re-review of the 2026-07-04 measured-passed retry
video: motorcycle clearly visible, cutting in from the front-left lane.
The 07-04 manual review verdict is VINDICATED (the "48f" label erratum
stands separately; the video is 8 frames).

## Detector night floor (evaluation limitation)
yolov8m at conf 0.20-0.25 produces ZERO detections (any class, any
view) on this human-passed night video. The composite S_perc would
score the project's only human-verified success as 0. Conversely the
current blob renderings score via person/single-frame class flips.
Metric and target are misaligned at night; needs a dedicated fix
(stronger/open-vocab detector, threshold study, or human-eval channel)
before capability conclusions are read off S_perc.

## Regression root cause (audit diff, measured)
- 07-04 override audit: motorcycle boxes per_frame_append to ALL cam
  types with DISTINCT source_record_index per cam (cam_front_left=0,
  cam_front=30, cam_back_right=72, cam_back_left=120): true per-view
  projections of the real track, not clones.
- Replay of the same archived command under current code: only
  cam_front rows change; all other cams changed=false. The anti-clone
  stopgap (17983a4: restrict injection to cam_front pending
  extrinsics) also crippled the source-bound path, which never had a
  clone problem.
- Consequence: a left cut-in's approach phase lives in cam_front_left
  and is dropped; the renderer receives truncated conditioning ->
  degraded actor rendering (person-like blob, YOLO person 0.7-0.85,
  motorcycle only single-frame flips).
- Side-calibration caveat: "left side renders weaker" (2026-07-07) may
  be partly an artifact of single-view injection; re-verify after fix.

## Additional measured facts from today
- Dataset switch mini val -> candidate70_source_bound trainval is a
  NO-OP for this scene (md5-identical generations; the frames are the
  same underlying data). The 07-04 differentiator was per-view
  source-bound conditioning, not the dataset.
- Replay does not reproduce the 07-04 artifact byte-wise under current
  code (expected: conditioning surface changed as above).

## Fix plan (v9 direction)
1. Restore per-view injection for source-bound entries: each per-frame
   entry carries its own cam_type/sample identity; append it to its
   own cam record only. No clones by construction.
2. Synthetic path stays cam_front-only until extrinsics-based per-view
   projection is implemented (do NOT revert the anti-clone fix).
3. Keep target-view S_perc scoring as is (metric-side fix was correct).
4. v9 arms after fix: open vs closed vs no-escalation with restored
   multi-view conditioning; re-derive tau from the new open arm;
   re-check side asymmetry.
