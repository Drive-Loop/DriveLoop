# Candidate70 Dry-Run Replacement Surface Audit

Date: 2026-07-02

## Scope

This note records a non-GPU runtime-surface audit for a candidate70 dry-run HDMap raster.

It uses the `image_hdmap.mode == "replace_from_path"` override path to load a synthetic lane-divider dry-run raster and checks whether the replacement reaches `grounding_downsampler_input`.

This audit does not run inference and does not generate video.

## Input

Dry-run source:

- summary: `outputs/driveloop/candidate70_hdmap_lane_divider_dry_run/candidate70_lane_divider_dry_run_summary.json`
- selected frame index: `0`
- source: `candidate70_lane_divider_dry_run.candidate_raster_path`
- provenance: `synthetic_projected_lane_divider_pixel_translation_dry_run`

## Artifact

- report: `outputs/driveloop/candidate70_hdmap_dry_run_replacement_surface_audit/candidate70_dry_run_raster_to_grounding_surface.json`
- override audit: `outputs/driveloop/candidate70_hdmap_dry_run_replacement_surface_audit/candidate70_dry_run_raster_to_grounding_surface.override_audit.jsonl`

## Observed Result

- `status`: `dry_run_raster_reaches_grounding_surface`
- `dry_run_candidate_available`: `true`
- `image_hdmap_override.changed`: `true`
- `grounding_downsampler_input.changed`: `true`
- `box_downsampler_input.changed`: `false`
- `input_image.changed`: `false`

## Interpretation

The dry-run candidate raster can be loaded through the verified `replace_from_path` path and observed at the DD2 `grounding_downsampler_input` runtime surface.

This confirms the plumbing from dry-run raster artifact to runtime-consumed HDMap surface.

## Claim Boundary

Allowed claims:

- The dry-run candidate raster can be loaded by `replace_from_path`.
- The dry-run candidate raster changes `image_hdmap`.
- The dry-run candidate raster reaches `grounding_downsampler_input`.
- The audit preserves unrelated `box_downsampler_input` and `input_image` surfaces.

Disallowed claims:

- The dry-run candidate is verified nuScenes map geometry.
- Candidate70 has a true lane-geometry replacement raster.
- HDMap lane geometry override is verified.
- Lane-change or cut-in control is verified.
- Runtime motion control is connected.
- Runtime tensor/raster change proves video semantics.
- Prompt-to-video semantic success is verified.

## Recommended Status

- candidate70_dry_run_raster_reaches_grounding_downsampler_input: true
- candidate70_true_lane_geometry_replacement_available: false
- hdmap_lane_geometry_override_verified: false
- lane_change_control_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false
- gpu_requires_separate_readiness_gate: true

## Next Step

The next step is to decide whether a map-geometry-grounded replacement operation can be defined, using the dry-run as a plumbing check only.

A GPU run can be considered later only after true replacement evidence, a readiness gate, and explicit user approval.
