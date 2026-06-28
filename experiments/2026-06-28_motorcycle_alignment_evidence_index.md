# Motorcycle Alignment Evidence Index

Date: 2026-06-28

## Scope

This index records the audit evidence for the refined motorcycle lane-change prompt in DriveLoop / DriveDreamer-2.

Prompt:

`daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.`

This index does not claim video semantic success. It only records evidence, tools, outputs, and claim boundaries.

## Current Claim State

- DD2 structural tensor control readiness: observed for `scene_description`, `boxes3d`, and derived `image_box`
- Refined audit-only GPU generation: not run
- Refined prompt-to-video semantic success: not measured
- Lane-change temporal actor motion control: not verified
- Trajectory tensor control: not runtime connected
- HDMap override control: not verified
- Motorcycle previous GPU smoke semantic result: measured_failed for visible left lane change

## Key Negative Result

The earlier motorcycle GPU smoke generated a video candidate, but manual review recorded:

- `object_presence.motorcycle`: passed, score 0.6
- `spatial_relation.left_lane_change`: failed, score 0.0
- `lighting.daytime`: passed, score 1.0
- `scene_type.urban_road`: passed, score 1.0
- overall video semantic claim: `measured_failed`

This negative result remains part of the evidence trail.

## Runtime Hash Evidence

Runtime hash comparison for earlier vs refined motorcycle audit-only:

Output:

`outputs/driveloop/dd2_runtime_hash_compare/motorcycle_earlier_vs_refined.json`

Observed boundary:

- `prompt_embed`: changed
- `box_downsampler_input`: unchanged
- `grounding_downsampler_input`: unchanged
- `img_cond`: unchanged

Interpretation:

The refined prompt changed text conditioning. It did not change the audited static structural or image-conditioning runtime inputs compared with the earlier audit-only run.

This does not prove video semantics.

## Motion Control Gap Evidence

Output:

`outputs/driveloop/motion_control_gap_audit/motorcycle_manual_feedback_motion_gap.json`

Recorded status:

- `lane_change_motion_tensor_control`: `not_verified`
- `video_semantic_claim`: `not_evaluated_by_this_audit`
- `trajectory_tensor`: `not_implemented`
- `temporal_actor_motion`: `not_implemented`

Interpretation:

Static actor placement and changed boxes do not prove lane-change temporal motion.

## Velocity Surface Evidence

Output:

`outputs/driveloop/dd2_velocity_surface_audit/mini_velocity_surface.json`

Recorded status:

- dataset label velocities exist
- velocity surface not observed as DD2 runtime input
- actor track identity not observed in inspected mini samples
- lane-change trajectory control remains `not_verified`

## Trajectory Control Contract

Document:

`experiments/2026-06-28_trajectory_control_contract_v0.md`

Runtime status:

- `trajectory_control_contract.status`: `not_runtime_connected`
- `trajectory_control_contract.control_level`: `contract_only`

Purpose:

Defines required evidence before claiming lane-change or cut-in trajectory control.

## GPU Smoke Readiness Gate

Script:

`scripts/run_gpu_smoke_readiness_gate.py`

Output:

`outputs/driveloop/gpu_smoke_readiness/motorcycle_refined_candidate_gate.json`

Recorded boundary:

- `gpu_smoke_allowed`: true when audit evidence and runtime resources are present
- `semantic_claim_allowed`: false
- allowed claim after GPU: `candidate_video_generated_only`

## Single GPU Smoke Command Plan

Script:

`scripts/run_single_gpu_smoke_command_plan.py`

Output:

`outputs/driveloop/gpu_smoke_command_plan/motorcycle_refined_candidate_plan.json`

Purpose:

Generates the audited command sequence without running GPU.

Execution order:

1. readiness gate
2. candidate GPU smoke
3. post-GPU review gate
4. prompt-video alignment evaluation after completed review

## GPU Smoke Protocol

Document:

`experiments/2026-06-28_gpu_smoke_protocol_v0.md`

Purpose:

Records when a short GPU smoke is allowed and what claims are forbidden afterward.

Key boundary:

A successful GPU run produces only a candidate video. It does not prove semantic alignment or lane-change control.

## GPU Smoke Runbook

Script:

`scripts/run_gpu_smoke_runbook.py`

Generated output:

`outputs/driveloop/gpu_smoke_runbook/motorcycle_refined_candidate_runbook.md`

Purpose:

Renders the command plan into a human-readable runbook.

## Post-GPU Review Gate

Script:

`scripts/run_post_gpu_review_gate.py`

Purpose:

After a candidate video exists, this gate preserves `not_measured` status, creates a manual review pack, and requires explicit manual/perception/VLM evidence before measured claims.

## Alignment Review Summary

Script:

`scripts/run_alignment_review_summary.py`

Purpose:

Summarizes explicit review/evaluator reports without treating unrelated smoke summaries as semantic evidence.

## Relevant Commits

- `a49e60b` feat: add auditable runtime hash and motion gap reports
- `cc2a4ab` feat: add DD2 velocity surface audit
- `4e23125` feat: add trajectory control contract
- `1b628c8` feat: add alignment review summary tool
- `a0e8760` feat: add GPU smoke readiness gate
- `dfe59c4` feat: add post GPU review gate
- `0859e96` feat: add single GPU smoke command plan
- `9b512c3` docs: add GPU smoke protocol
- `f94dfab` feat: add GPU smoke runbook generator

## Claim Boundary

Allowed current claims:

- audit-only refined prompt changed text conditioning
- static DD2 structural overrides are auditable
- short GPU smoke is gated and ready as a candidate-generation experiment
- post-GPU semantic claims require explicit review evidence

Disallowed current claims:

- the refined prompt fixes lane-change generation
- DD2 now has verified lane-change trajectory control
- runtime tensor hash changes prove video semantic correctness
- a generated video alone proves prompt-to-video alignment

## Next Evidence Needed

Before any measured semantic success claim:

1. Run a short gated GPU smoke only if intentionally chosen.
2. Preserve video artifact and runtime audit metadata.
3. Run post-GPU review gate.
4. Complete explicit manual/perception/VLM review.
5. Run prompt-video alignment evaluation.
6. Record measured result, including negative results.
