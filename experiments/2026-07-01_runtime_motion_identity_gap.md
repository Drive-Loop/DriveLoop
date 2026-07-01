# Runtime Motion Identity Gap

Date: 2026-07-01

## Scope

This note records the current non-GPU evidence for DriveLoop / DriveDreamer-2 runtime motion metadata and identity surfaces.

It does not claim lane-change control, prompt-to-video semantic success, or paper-level semantic success.

## Current Dashboard Evidence

Latest dashboard/refresh-all status:

- dashboard_status: measured_ready
- video_semantic_claim: measured_failed
- semantic_success_claim_allowed: false
- motion_metadata_runtime_status: metadata_observed_not_runtime_control
- motion_metadata_claim: metadata_observed_only_not_runtime_control
- actor_identity_available_in_batch_any: false
- per_frame_actor_boxes3d_observed_any: false
- refresh_does_not_run_gpu: true
- refresh_does_not_generate_video: true

## Interpretation

The DD2 runtime audit can now report motion metadata from the batch.

Observed metadata includes:

- velocities_available_in_batch_any
- velocities_available_in_batch_all
- boxes3d_available_in_batch_any
- actor label counts
- compact previews of velocity and boxes3d shapes

Not observed:

- persistent actor identity in batch
- per-frame actor boxes3d linked to persistent actors
- trajectory tensor consumed by runtime
- velocity/displacement consumed by runtime
- HDMap lane geometry override verified as a controllable runtime surface

## Claim Boundary

Allowed claims:

- Motion metadata can be surfaced in DD2 runtime audit.
- Velocity metadata and boxes3d metadata are observable in audit-only runtime evidence.
- Current runtime audit still does not prove lane-change control.

Blocked claims:

- The model follows the motorcycle lane-change prompt.
- Runtime motion control is connected.
- Video generation success is semantic success.
- Tensor metadata observation is video semantic success.

## Next Non-GPU Work

1. Trace dataset sample keys for instance tokens or track identifiers before collation.
2. Determine whether converter outputs persistent actor identity and whether DD2 transforms drop it.
3. If identity exists upstream, expose it as audit-only metadata first.
4. Search for per-frame boxes3d or temporal actor tracks in DD2 data structures.
5. Only after identity and per-frame actor boxes are observable should we design a runtime motion intervention.

## Validation

Before any commit:

- pytest -q tests
- git diff --check
