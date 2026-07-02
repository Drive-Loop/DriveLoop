# Candidate70 HDMap Raster Source Probe

Date: 2026-07-02

## Scope

This note records a non-GPU probe of the candidate70 HDMap raster source.

It does not modify model logic, does not run inference, does not create a replacement HDMap raster, and does not claim lane-change control or prompt-to-video semantic success.

## Artifacts

- summary: outputs/driveloop/candidate70_hdmap_raster_probe/candidate70_hdmap_raster_probe_summary.json
- generated raster images: outputs/driveloop/candidate70_hdmap_raster_probe/images/

## Result

The current nuScenes converter `_get_hdmap(cam_token, scene_token)` can regenerate candidate70 CAM_FRONT HDMap rasters for all 8 audited frames.

Observed summary:

- frame_count: 8
- all_generated_nonzero: true
- processed_match_true: 16
- processed_match_false: 0

Each generated raster matched the processed HDMap LMDB entry by SHA256 for both checked processed versions:

- /data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_train/v0.0.2/hdmaps
- /data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_train/v0.0.1/hdmaps

For all 8 frames, the generated-vs-processed image diff had `diff_nonzero: 0`.

## Interpretation

Candidate70's baseline `image_hdmap` raster condition is reproducible from raw nuScenes map data using the existing converter path.

This verifies baseline raster provenance for candidate70. It also confirms that the `data_index` mapping used by the candidate70 converter-derived label subset aligns with the processed HDMap LMDB entries.

## Claim Boundary

Allowed claims:

- Candidate70 baseline HDMap rasters are reproducible from the current converter path.
- Candidate70 generated HDMap rasters match processed HDMap LMDB entries by hash for the audited 8 frames.
- Candidate70 has a verified baseline HDMap raster source.

Disallowed claims:

- A replacement HDMap raster has been constructed.
- HDMap lane geometry override is verified.
- Lane-change or cut-in control is verified.
- Runtime motion control is connected.
- HDMap raster hash match proves video semantics.
- Prompt-to-video semantic success is verified.

## Recommended Status

- candidate70_baseline_hdmap_raster_reproducible: true
- candidate70_processed_hdmap_matches_converter: true
- candidate70_verified_baseline_hdmap_source_available: true
- candidate70_verified_replacement_hdmap_raster_available: false
- hdmap_lane_geometry_override_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Do not run GPU yet.

The next non-GPU step is to decide whether to add an explicit replacement-raster override mode. If added, it must require a verified raster source and audit-only hash comparison before any inference run.
