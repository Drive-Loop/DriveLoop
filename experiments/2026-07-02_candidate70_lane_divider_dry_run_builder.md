# Candidate70 Lane Divider Dry-Run Builder

Date: 2026-07-02

## Scope

This note records a non-GPU dry-run builder for candidate70 HDMap lane-divider raster perturbation.

It does not construct a verified map-geometry replacement, does not modify DD2 model inputs, does not run inference, and does not claim lane-change control or prompt-to-video semantic success.

## Method

The builder reuses the candidate70 HDMap geometry introspection path, rebuilds the baseline HDMap raster, then applies a synthetic projected-image-space perturbation:

- target: visible `lane_divider` vectors
- operation: `translate_projected_lane_divider_pixels`
- default dx: `-32.0`
- default dy: `0.0`

For each audited frame, the script records:

- baseline raster hash
- converter raster hash
- baseline-vs-converter match
- dry-run candidate raster hash
- baseline-vs-candidate diff hash
- diff nonzero count
- modified visible lane divider count
- provenance and claim boundary

## Artifact

- summary: `outputs/driveloop/candidate70_hdmap_lane_divider_dry_run/candidate70_lane_divider_dry_run_summary.json`
- candidate rasters and diffs: `outputs/driveloop/candidate70_hdmap_lane_divider_dry_run/images/`

## Interpretation

This dry run proves that the audited geometry/raster pipeline can generate a candidate raster with a controlled lane-divider perturbation and measurable raster diff.

This is only a synthetic projected-pixel perturbation. It is not a verified nuScenes map-geometry replacement.

## Claim Boundary

Allowed claims:

- Candidate70 baseline rasters can be rebuilt before perturbation.
- A synthetic lane-divider dry-run candidate raster can be generated.
- The dry-run candidate differs from baseline by hash and pixel diff.
- The dry-run operation is recorded with source/path/hash/provenance.

Disallowed claims:

- Candidate70 has a true map-geometry replacement raster.
- HDMap lane geometry override is verified.
- Lane-change or cut-in control is verified.
- Runtime motion control is connected.
- Raster diff proves video semantics.
- Prompt-to-video semantic success is verified.
- This audit alone is not sufficient for a GPU run.

## Recommended Status

- candidate70_lane_divider_dry_run_candidate_built: true
- candidate70_dry_run_raster_diff_observed: true
- candidate70_true_lane_geometry_replacement_available: false
- hdmap_lane_geometry_override_verified: false
- lane_change_control_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Inspect the generated candidate rasters and diffs.

The next non-GPU step is to decide whether a map-geometry-grounded replacement operation can be defined. Run GPU only after separate readiness gate and explicit user approval.
