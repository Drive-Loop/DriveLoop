# Candidate70 Current Readiness Checkpoint

Date: 2026-07-02

## Current Evidence

- converter identity path available
- converter-derived candidate70 identity subset created
- target motorcycle track covers all 8 audited frames
- candidate70 baseline HDMap raster is reproducible from raw nuScenes converter path
- processed HDMap entries match regenerated converter rasters for all audited frames
- DD2 runtime consumes HDMap raster and box raster surfaces
- dashboard surfaces candidate70 identity and HDMap raster provenance signals

## Current Blockers

- no direct trajectory tensor consumed by DD2 runtime
- velocity metadata is observable but not consumed as runtime model input
- displacement is not observed as runtime model input
- HDMap replacement raster override mode is not available
- HDMap lane geometry override is not verified
- lane-change / cut-in control is not verified
- runtime motion control is not connected

## Claim Boundary

Allowed claims:

- Candidate70 has verified source identity and baseline HDMap raster provenance.
- Candidate70 target motorcycle identity is observable across 8 audited frames.
- Existing DD2 runtime consumes raster condition surfaces.
- Baseline HDMap raster reproducibility is verified for candidate70.

Disallowed claims:

- Runtime motion control is connected.
- Trajectory, velocity, or displacement is consumed by DD2 runtime.
- HDMap lane geometry override is verified.
- Candidate70 replacement HDMap raster exists.
- Lane-change or cut-in semantic success is verified.
- Prompt-to-video semantic success is allowed.

## Recommended Status

- candidate70_converter_identity_subset_created: true
- candidate70_target_motorcycle_track_covers_all_8_frames: true
- candidate70_baseline_hdmap_raster_reproducible: true
- candidate70_processed_hdmap_matches_converter: true
- candidate70_verified_replacement_hdmap_raster_available: false
- trajectory_tensor_available: false
- velocity_consumed_as_model_input: false
- hdmap_lane_geometry_override_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Decision Point

Do not run GPU yet.

Next decision: either keep replacement HDMap as a documented gap, or explicitly add an audit-only replacement-raster override mode with verified source and hash checks before any inference.
