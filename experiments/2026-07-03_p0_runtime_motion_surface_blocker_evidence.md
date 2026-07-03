# P0 Runtime Motion Surface Blocker Evidence

Date: 2026-07-03

## Purpose

This record documents a P0 blocker for DriveLoop / DriveDreamer-2: the current DD2 runtime path does not expose a verified actor-level trajectory, velocity, or displacement control tensor for lane-change / cut-in generation.

This is not a P0 completion record. It is evidence for the current claim boundary and for the next implementation target.

## Research Question

Can the current DriveLoop wrapper control DD2 temporal actor motion, such as a motorcycle lane-change or cut-in, through existing DD2 runtime inputs?

## Finding

No.

The current DD2 runtime consumes image/box conditioning surfaces, but no verified trajectory, velocity, or displacement runtime control surface is currently connected.

Dataset velocity exists in converted data, but the current DD2 runtime uses velocity-related fields as metadata only. Metadata presence is not sufficient evidence of velocity-conditioned generation.

## Verified Evidence

Code audit now distinguishes true runtime motion-control inputs from metadata-only motion terms.

Verified command:

`PYTHONPATH=.:dreamer-datasets pytest -q`

Observed result:

`222 passed, 1 warning`

Relevant audit interpretation:

- `direct_motion_runtime_surface.status`: `not_observed`
- `metadata_only_motion_terms_observed`: `true`
- velocity mentions in DD2 runtime are metadata-only unless a trajectory / velocity / displacement tensor is passed through `input_dict` and consumed by pipeline / UNet

Current consumed DD2 conditioning surfaces remain:

- `grounding_downsampler_input`
- `box_downsampler_input`
- image/video condition surfaces

## Claim Boundary

Allowed claims:

- Dataset velocity exists in converted nuScenes-derived data.
- Static/spatial `boxes3d` and derived `image_box` conditioning can reach DD2 audit surfaces.
- Candidate70 boxes3d/image_box structural override readiness can be reported as audit-only structural conditioning evidence.
- The current audit pipeline can prevent overstated temporal-control claims.

Disallowed claims:

- Do not claim runtime trajectory control.
- Do not claim lane-change / cut-in temporal control.
- Do not claim velocity-conditioned generation.
- Do not claim generated video semantic success from tensor existence alone.
- Do not treat static boxes3d/image_box conditioning as temporal actor motion control.
- Do not use this evidence as GPU-smoke approval.

## P0 Status

P0 is not complete.

`gpu_smoke_allowed` remains `false`.

The current blocker is not prompt wording. The blocker is the absence of a verified runtime control surface for temporal actor motion.

## Paper Use

This result should be used in the paper as a claim-boundary and limitation/control-surface audit result.

It supports the argument that DriveLoop must separate:

1. source binding evidence,
2. structural conditioning evidence,
3. runtime temporal-control evidence,
4. generated-video semantic success evidence.

The current code supports the first two more strongly than the third and fourth.

## Next Required Work

To complete the original P0 temporal-control goal, DriveLoop must either:

1. implement and audit a real DD2 trajectory / velocity / displacement runtime condition surface, or
2. explicitly narrow the paper claim away from actor-level temporal motion control and toward auditable source binding plus structural conditioning.

