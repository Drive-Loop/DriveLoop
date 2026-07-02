# Candidate70 Velocity Runtime Claim Correction

Date: 2026-07-02

## Scope

This note records a non-GPU correction to the trajectory runtime surface audit velocity-consumption claim.

It does not run GPU, does not claim lane-change control, and does not claim prompt-to-video semantic success.

## Issue

The candidate70 trajectory runtime surface audit previously exposed a contradictory velocity surface:

- velocity_tensor.available_in_runtime_audit: false
- velocity_consumed_by_dd2_runtime: true

This was an audit interpretation bug. A velocity-consumption claim from a velocity audit must not be treated as DD2 runtime consumption unless a runtime velocity tensor is actually observed.

## Fix

The trajectory runtime surface audit now requires both:

- velocity tensor observed in runtime audit
- velocity audit claim indicates DD2 runtime consumption

Only then may `velocity_consumed_by_dd2_runtime` be true.

The refreshed candidate70 audit now reports:

- velocity_tensor.available_in_runtime_audit: false
- velocity_consumed_by_dd2_runtime: false
- velocity_consumed_claimed_by_velocity_audit: true
- velocity_runtime_consumption_requires_runtime_tensor: true
- blocker restored: velocity_or_displacement_tensor_not_consumed_by_runtime

## Current Status

- candidate70 trajectory runtime surface status: not_runtime_connected
- trajectory_tensor_available: false
- velocity_consumed_by_dd2_runtime: false
- hdmap_lane_geometry_override_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Claim Boundary

Allowed claims:

- Candidate70 has velocity metadata / velocity audit evidence.
- Candidate70 does not have verified runtime velocity tensor consumption.
- The trajectory runtime surface audit now separates velocity metadata claims from runtime tensor consumption.

Disallowed claims:

- Velocity metadata proves DD2 runtime motion control.
- Candidate70 verifies lane-change or cut-in control.
- Candidate70 verifies trajectory, velocity, displacement, or HDMap lane geometry is consumed by DD2 runtime.
- Candidate70 proves prompt-to-video semantic success.

## Next Step

Continue non-GPU investigation of actual runtime-consumed motion surfaces. Do not run GPU until trajectory, displacement, velocity, or lane geometry control is observably connected to DD2 runtime.
