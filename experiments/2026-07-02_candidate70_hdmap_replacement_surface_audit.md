# Candidate70 HDMap Replacement Surface Audit

Date: 2026-07-02

## Scope

This note records a non-GPU audit-only check for the new `image_hdmap.mode == "replace_from_path"` override mode.

It does not run inference, does not generate video, does not modify DD2 model logic, and does not claim lane-change control or prompt-to-video semantic success.

## Implementation

The override path now supports loading a verified HDMap raster from disk into `image_hdmap`.

The override requires:

- `path`
- `source`
- `provenance`
- `expected_sha256`

The override fails closed when:

- the path is missing
- the file does not exist
- the image cannot be loaded
- the SHA256 does not match `expected_sha256`

## Audit Run

Artifact:

- `outputs/driveloop/hdmap_replacement_surface_audit/candidate70_verified_raster_to_grounding_surface.json`

Observed status:

- `status`: `replacement_raster_reaches_grounding_surface`
- `does_not_run_gpu`: `true`
- `does_not_generate_video`: `true`
- `image_hdmap_override.changed`: `true`
- `grounding_downsampler_input.changed`: `true`
- `box_downsampler_input.changed`: `false`
- `input_image.changed`: `false`

Verified raster source:

- source: `candidate70_hdmap_raster_probe.converter_hdmap_path`
- provenance: `converter_generated_raster_matches_processed_hdmap_lmdb_by_sha256`
- frame index: `0`
- data index: `9935`
- expected SHA256: `675156e27b620c47d93ea00fad453d83bb36fb93bedec5ce4d1a2f1365720958`

## Interpretation

A verified raster can be loaded through the DriveLoop override path and observed at the DD2 `grounding_downsampler_input` runtime surface.

This confirms the replacement-raster override plumbing and hash/audit recording path.

## Claim Boundary

Allowed claims:

- A verified raster source can be loaded by `image_hdmap.mode == "replace_from_path"`.
- The replacement raster changes `image_hdmap`.
- The replacement raster reaches `grounding_downsampler_input`.
- `box_downsampler_input` and `input_image` stayed unchanged in this HDMap-only audit.

Disallowed claims:

- Candidate70 has a verified lane-geometry replacement raster.
- HDMap lane geometry override is verified.
- Lane-change or cut-in control is verified.
- Runtime motion control is connected.
- Generated video semantics are evaluated.
- Prompt-to-video semantic success is verified.

## Recommended Status

- candidate70_replacement_raster_reaches_grounding_downsampler_input: true
- candidate70_verified_replacement_hdmap_raster_available: false
- hdmap_lane_geometry_override_verified: false
- lane_change_control_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Do not run GPU yet.

The next non-GPU step is to construct or select a true candidate70-compatible lane-geometry replacement raster, then re-run the same audit with its own source/path/hash/provenance.
