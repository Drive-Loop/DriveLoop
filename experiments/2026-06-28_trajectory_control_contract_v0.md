# Trajectory Control Contract v0

Date: 2026-06-28

## Purpose

Record the evidence required before DriveLoop can claim lane-change or cut-in trajectory control in DriveDreamer-2.

## Current Status

The contract is emitted in `dd2_executable_condition.v0` as `trajectory_control_contract`.

Status is `not_runtime_connected`.
Control level is `contract_only`.

## Required Runtime Surfaces

- actor track identity
- per-frame actor boxes3d
- velocity or displacement tensor consumed by DD2 runtime
- HDMap lane geometry
- temporal consistency audit

## Current Runtime Surfaces

- `boxes3d`: static sample-level override
- `image_box`: derived from boxes3d
- `velocities`: present in dataset labels, not observed in DD2 runtime input
- `actor_track_identity`: not observed in inspected mini samples
- `hdmap_lane_geometry`: mini dataset baseline

## Claim Boundary

This contract does not prove lane-change control or video semantics. It only defines what evidence is required before such a claim can be made.
