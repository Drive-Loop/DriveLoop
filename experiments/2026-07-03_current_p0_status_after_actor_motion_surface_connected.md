# Current P0 Status After Actor Motion Surface Connected

Date: 2026-07-03

## Handoff Summary

This is the current handoff file for the DriveLoop / DriveDreamer-2 project after P0 actor motion surface work.

The previous handoff file:

- `experiments/2026-07-03_current_p0_status_after_structural_override_readiness.md`

is now historical. It captured structural override readiness before actor-level motion was connected.

## Current Repository State

Latest known pushed commit:

- `19c269c feat: connect actor motion to per-frame dd2 boxes3d surface`

Latest verified full test result:

- `PYTHONPATH=.:dreamer-datasets:dreamer-train:dreamer-models pytest -q`
- Result: `231 passed, 1 warning`

## Current P0 Status

P0 is scoped complete for the following runtime chain:

1. prompt / structured condition
2. `motion_primitives`, including `lane_change` or `cut_in`
3. `actor_motion_plan`
4. `actor_motion_surface_plan`
5. `boxes3d.per_frame_append`
6. DD2 transform override hook
7. derived `image_box_canvas`
8. derived `box_downsampler_input`

This means DriveLoop actor-level lane-change / cut-in intent can now be represented as per-frame structural actor boxes and passed into the DD2 runtime transform surface.

## Verified Runtime Evidence

Observed backend/audit values:

- `trajectory_status`: `runtime_connected_via_per_frame_actor_boxes3d`
- `actor_motion_surface_ready`: `true`
- `tensor_control_ready`: `true`
- `actor_motion_surface_available`: `true`
- `actor_motion_surface`: `boxes3d.per_frame_append`
- `override_mode`: `append_and_per_frame_append`
- `per_frame_append_count`: `4`

Related experiment records:

- `experiments/2026-07-03_p0_actor_motion_surface_connected.md`
- `experiments/2026-07-03_per_frame_boxes3d_transform_surface_audit.md`
- `experiments/2026-07-03_p0_runtime_motion_surface_blocker_evidence.md`

## Claim Boundary

Allowed claims:

- Actor-level per-frame boxes3d structural motion conditioning is connected.
- Lane-change / cut-in intent can be represented as per-frame actor boxes.
- The DD2 transform surface can receive and apply `boxes3d.per_frame_append`.
- Per-frame `image_box` / `box_downsampler_input` changes are auditable.
- P0 is scoped complete for structural actor-motion conditioning.

Not allowed yet:

- Do not claim velocity tensor control.
- Do not claim displacement tensor control.
- Do not claim physically verified trajectory dynamics.
- Do not claim true HDMap lane geometry replacement.
- Do not claim generated video semantic success.
- Do not claim lane-change / cut-in visual success before GPU output and manual semantic review.

## Remaining Work After P0

Recommended next steps:

1. Run a CPU audit command that records the current actor-motion surface output for paper evidence.
2. Prepare a GPU smoke only after confirming the exact candidate, prompt, override JSON, and audit path.
3. Review generated video manually if GPU smoke is run.
4. Keep paper claims limited to auditable structural conditioning unless semantic video evidence passes review.
5. If the paper needs stronger motion-control claims, implement a real velocity / displacement / trajectory tensor path instead of relying only on structural boxes.

## Paper Writing Position

The current paper should describe DriveLoop as an auditable closed-loop scenario editing and structural conditioning system.

The strongest current contribution is:

- source-bound candidate selection
- prompt-conditioned structured editing
- per-frame actor boxes3d motion surface
- DD2 transform-level runtime conditioning audit
- strict claim boundary between tensor evidence and semantic video success

The paper should not present this as fully verified dynamic motion generation until GPU output and human semantic review support that claim.
