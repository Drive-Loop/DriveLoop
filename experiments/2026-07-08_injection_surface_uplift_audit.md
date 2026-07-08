# 2026-07-08 Injection-surface uplift audit: all pieces exist

## Findings (code audit, measured)
- Runtime has intrinsics: drivedreamer2_transforms.py:200 reads
  data_dict['calib']['cam_intrinsic']; image_box canvas is derived by
  boxes3d_to_corners3d -> crop_corners3d(z>0) ->
  corners3d_to_corners2d(cam_intrinsic) at runtime.
- Extrinsic chain exists: nuscenes_converter stores lidar2ego and
  ego2global (matrix + quat) for lidar and per-cam sensor calibs.
- Projection/transform utilities are complete in
  dreamer_datasets.structures (boxes3d corners2d/rotate/convert_to).
- The paper's text->trajectory->HDMap front-end (LLM function library,
  HDMap generator) is NOT in the released repos (grep: zero hits).
  DriveLoop's motion primitives are the minimal substitute for that
  missing front-end; this defines our contribution boundary.

## Uplift design v1 (next session)
Ego-frame per-frame trajectory boxes -> per-sample ego2global +
per-cam sensor2ego transforms -> per-cam camera-frame boxes3d append
(true per-view projections, no clones; behind-camera culled by the
existing z>0 crop) -> existing canvas derivation unchanged.
New code: one coordinate-transform module + tests. Everything else
(projection, canvas, audits, evaluator) is reused.

## Remaining verification before implementation
Confirm the processed dataset records carry the calib extrinsic fields
at runtime (cam_intrinsic confirmed; sensor2ego/ego2global pending a
record dump).

## Claim boundary
Audit only; no behavior change in this record.
