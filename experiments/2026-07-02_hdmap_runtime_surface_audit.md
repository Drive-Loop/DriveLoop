# HDMap Runtime Surface Audit

Date: 2026-07-02

## Scope

This note records a non-GPU DD2 audit for the `image_hdmap` raster runtime surface.

It does not claim HDMap lane geometry override, lane-change control, runtime motion control, prompt-to-video semantic success, or paper-level semantic success.

## Artifact

Audit output:

`outputs/driveloop/hdmap_runtime_surface_audit/mini_hdmap_zero_surface_audit.json`

Script:

`scripts/run_hdmap_runtime_surface_audit.py`

## Observed Result

The audit compared a baseline transformed sample against an explicit `image_hdmap` zero ablation.

Observed result:

- `status`: `hdmap_raster_runtime_surface_mutable`
- `does_not_run_gpu`: `true`
- `does_not_generate_video`: `true`
- `image_hdmap_override.changed`: `true`
- `grounding_downsampler_input.changed`: `true`
- `box_downsampler_input.changed`: `false`
- `input_image.changed`: `false`

Interpretation:

This verifies that the `image_hdmap` raster reaches the DD2 grounding downsampler runtime surface and can be changed by an explicit audit-only ablation.

## Claim Boundary

Allowed claims:

- `image_hdmap` is a DD2 model-facing raster condition surface.
- An explicit HDMap zero ablation changes `grounding_downsampler_input`.
- The audit is non-GPU and does not generate video.

Disallowed claims:

- HDMap lane geometry override is verified.
- Lane-change control is verified.
- Runtime motion control is connected.
- HDMap raster hash changes prove lane-change motion.
- Runtime tensor audit proves video semantics.
- Prompt-to-video semantic success is achieved.
- The motorcycle lane-change case is semantically successful.

## Next Non-GPU Work

1. Audit lane geometry compatibility with the accepted lane-change target.
2. Investigate whether a verified replacement HDMap raster or lane geometry source can be constructed.
3. Keep `semantic_success_claim_allowed` false until a generated video is measured as semantically matching the accepted prompt.
