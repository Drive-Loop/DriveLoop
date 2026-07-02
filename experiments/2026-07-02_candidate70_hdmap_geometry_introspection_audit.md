# Candidate70 HDMap Geometry Introspection Audit

Date: 2026-07-02

## Scope

This note records a non-GPU introspection audit of candidate70 HDMap geometry.

It does not construct a replacement raster, does not modify DD2 model inputs, does not run inference, and does not claim lane-change control or prompt-to-video semantic success.

## Method

The audit reuses candidate70 HDMap raster probe records and rebuilds the HDMap raster through the same converter geometry path:

- `road_divider`
- `lane_divider`
- `ped_crossing`
- `road_segment`
- `lane`
- `get_map_geom(...)`
- `line_geoms_to_vectors(...)`
- `poly_geoms_to_vectors(...)`
- `preprocess_map(...)`

For each audited frame, the script records:

- map location
- patch box and patch angle
- raw geometry counts
- projected visible vector stats
- rebuilt raster path
- rebuilt raster SHA256
- converter raster SHA256
- hash match status

## Artifact

- summary: `outputs/driveloop/candidate70_hdmap_geometry_introspection/candidate70_hdmap_geometry_introspection_summary.json`
- rebuilt rasters: `outputs/driveloop/candidate70_hdmap_geometry_introspection/images/`

## Expected Interpretation

If rebuilt rasters match converter rasters, the audit confirms that the introspection path reproduces the current baseline HDMap geometry/raster pipeline.

This is a prerequisite for designing a future true lane-geometry replacement raster, but it is not itself a replacement.

## Claim Boundary

Allowed claims:

- Candidate70 HDMap geometry can be introspected through the converter path.
- Rebuilt baseline rasters can be compared against converter rasters by hash.
- Visible map-layer vector counts can be recorded per frame.

Disallowed claims:

- Candidate70 has a true lane-geometry replacement raster.
- HDMap lane geometry override is verified.
- Lane-change or cut-in control is verified.
- Runtime motion control is connected.
- Raster or tensor changes prove video semantics.
- Prompt-to-video semantic success is verified.

## Recommended Status

- candidate70_hdmap_geometry_introspected: true
- candidate70_true_lane_geometry_replacement_available: false
- hdmap_lane_geometry_override_verified: false
- lane_change_control_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Use the per-frame geometry/vector stats to decide whether a minimal, auditable lane-geometry replacement raster can be constructed.

Do not run GPU from this audit alone.
