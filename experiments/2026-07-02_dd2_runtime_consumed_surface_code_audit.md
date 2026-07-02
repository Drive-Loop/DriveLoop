# DD2 Runtime-Consumed Surface Code Audit

Date: 2026-07-02

## Scope

This note records a non-GPU code-path audit of the DD2 runtime-consumed condition surfaces.

It does not run inference, does not modify model logic, and does not claim lane-change control or prompt-to-video semantic success.

## Observed Runtime Path

The inspected transform path builds:

- `grounding_downsampler_input` from the configured grounding input, expected here to be `image_hdmap`
- `box_downsampler_input` from rendered 3D boxes
- `motion_metadata` containing metadata-only observations such as velocity availability, actor labels, identity fields, and box shapes

The inspected tester path passes only these condition tensors into runtime `input_dict`:

- `grounding_downsampler_input`
- `box_downsampler_input`
- optional `img_cond`
- optional `video_cond`

`motion_metadata` is summarized into the audit JSON, but is not passed into the model runtime `input_dict`.

The inspected pipeline consumes:

- `grounding_downsampler_input`
- `box_downsampler_input`
- optional image/video conditioning latents

The pipeline concatenates the downsampled HDMap and box condition latents into the UNet input channels.

## Negative Findings

No direct runtime-consumed tensor path was found for:

- `trajectory`
- `velocity`
- `velocities`
- `displacement`

In the inspected transform code, `velocities` are observed only for metadata reporting. They are not converted into a model input tensor.

In the inspected tester code, `motion_metadata` is written to audit output only. It is not added to `input_dict`.

In the inspected pipeline and UNet forward paths, the runtime-consumed condition surfaces are raster/latent surfaces, not explicit trajectory or velocity tensors.

## Interpretation

The current DD2 runtime control surface appears to be raster-conditioned:

- HDMap raster surface through `grounding_downsampler_input`
- actor box raster surface through `box_downsampler_input`
- optional image/video conditioning

Candidate70 actor identity, velocity metadata, and trajectory-style audit metadata can support diagnosis and candidate readiness, but they do not by themselves prove runtime motion control.

## Claim Boundary

Allowed claims:

- Current inspected DD2 runtime consumes HDMap raster and box raster condition surfaces.
- Candidate70 velocity metadata is observable in audit metadata only.
- No direct trajectory, velocity, or displacement runtime-consumed tensor path was observed in the inspected code path.

Disallowed claims:

- Runtime motion control is connected.
- Velocity or displacement is consumed as a DD2 model input.
- Trajectory tensor is consumed by DD2 runtime.
- Lane-change or cut-in control is verified.
- HDMap lane geometry override is verified.
- Tensor, metadata, or generated video alone proves prompt-to-video semantic success.

## Recommended Status

- dd2_runtime_consumed_surface_code_audit_completed: true
- runtime_hdmap_raster_surface_consumed: true
- runtime_box_raster_surface_consumed: true
- trajectory_tensor_available: false
- velocity_consumed_as_model_input: false
- displacement_consumed_as_model_input: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Focus next on whether a candidate70-compatible HDMap raster replacement can be constructed and verified through the existing `grounding_downsampler_input` surface.

Do not run GPU yet.
