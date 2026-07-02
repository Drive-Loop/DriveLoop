# HDMap Replacement Surface Gap Audit

Date: 2026-07-02

## Scope

This note records a non-GPU audit of the current HDMap override capability.

It does not modify DD2 model logic, does not run inference, and does not claim lane-change control or prompt-to-video semantic success.

## Observed Capability

The current DD2 runtime consumes the HDMap raster through the grounding condition path.

Existing HDMap runtime surface audit shows:

- `image_hdmap` can be changed by explicit zero ablation
- `grounding_downsampler_input` changes when `image_hdmap` is zeroed
- `box_downsampler_input` remains unchanged for HDMap-only ablation
- `input_image` remains unchanged for HDMap-only ablation

This supports the claim that the HDMap raster reaches a DD2 runtime-consumed surface.

## Observed Gap

The current override implementation supports:

- `boxes3d` append
- `scene_description` replace
- `image_hdmap` zero ablation

The current override implementation does not yet support loading or applying a verified replacement HDMap raster.

The existing HDMap audit script is explicitly a zero-ablation audit. It is not a lane geometry replacement audit.

## Candidate70 Implication

For candidate70, the next useful HDMap step is not GPU inference.

The next useful step is to determine whether a verified candidate70-compatible replacement HDMap raster can be constructed, serialized, loaded, and observed through the existing `grounding_downsampler_input` surface.

Until that exists, candidate70 can only use the existing baseline `image_hdmap` raster condition surface.

## Claim Boundary

Allowed claims:

- HDMap raster reaches the DD2 grounding runtime surface.
- Zeroing `image_hdmap` changes `grounding_downsampler_input`.
- Existing code has no verified replacement HDMap raster override path.

Disallowed claims:

- HDMap lane geometry override is verified.
- Candidate70 has a verified replacement HDMap raster.
- Lane-change or cut-in control is verified.
- Runtime motion control is connected.
- HDMap raster hash change proves video semantics.
- Generated video alone proves prompt-to-video semantic success.

## Recommended Status

- hdmap_raster_runtime_surface_mutable: true
- hdmap_zero_ablation_verified: true
- hdmap_replacement_raster_override_available: false
- candidate70_verified_replacement_hdmap_raster_available: false
- hdmap_lane_geometry_override_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Keep this as a capability gap unless explicitly adding a replacement-raster override mode.

If adding that mode later, require a verified raster source and audit-only hash comparison before any GPU run.
