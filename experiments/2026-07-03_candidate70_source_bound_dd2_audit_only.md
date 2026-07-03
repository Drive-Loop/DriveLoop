# Candidate70 Source-Bound DD2 Audit-Only Result

Date: 2026-07-03 server time

## Scope

Scenario: candidate70_source_bound_dd2_audit_only

Prompt: night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.

This record summarizes the non-GPU source-bound DriveDreamer-2 audit-only pass after candidate70 source-sample binding readiness passed.

## Evidence

Source-sample binding readiness:

- path: outputs/driveloop/source_sample_binding_readiness/candidate70_source_sample_binding_readiness.json
- status: ready
- resolved_dd2_batch_skip: 0
- runtime generation dataset: ready
- blockers: none

DD2 audit-only output:

- path: outputs/driveloop/candidate70_source_bound_dd2_audit_only/
- runtime audit: outputs/driveloop/candidate70_source_bound_dd2_audit_only/artifacts/candidate70_source_bound_dd2_audit_only/dd2_runtime_input_audit_00.json
- paper alignment report: outputs/driveloop/candidate70_source_bound_dd2_audit_only/artifacts/candidate70_source_bound_dd2_audit_only/paper_alignment_report_00.json
- override audit: outputs/driveloop/candidate70_source_bound_dd2_audit_only/artifacts/candidate70_source_bound_dd2_audit_only/dd2_override_audit_00.jsonl

Refresh/status summary:

- path: outputs/driveloop/refresh_all_audit_status/motorcycle_refined_candidate_refresh.json
- active readiness source: candidate70_gpu_readiness_gate
- candidate70 source-sample binding readiness: ready
- candidate70 GPU readiness: blocked
- candidate70 GPU smoke allowed: false
- semantic_success_claim_allowed: false

## What This Proves

- Candidate70 source-bound runtime dataset is available.
- Candidate70 source sample can be resolved to DD2 runtime batch 0.
- DD2 audit-only path uses the candidate70 source-bound trainval dataset rather than the old mini dataset.
- Runtime input audit records prompt embedding, image conditioning, HDMap grounding input, and box grounding input.
- Scene description / prompt override reaches the DD2 audit path.

## What This Does Not Prove

- No video was generated in this audit-only pass.
- This is not GPU approval.
- This is not prompt-video semantic success.
- This does not prove lane-change or cut-in success.
- This does not prove runtime motion control is connected.
- This does not prove true lane geometry replacement.
- Boxes3d, image_box, and image_hdmap were not target-overridden.
- Actor identity remains unavailable inside processed runtime labels.

## Current Blockers

- runtime_motion_control_not_connected
- trajectory_runtime_surface_not_connected
- true_lane_geometry_replacement_not_available
- runtime_motion_control_claim_not_allowed
- semantic_success_claim_not_allowed

## Decision

Do not run another GPU smoke from this state.

The next technical work should either:

1. connect or explicitly mark unavailable the runtime motion / trajectory / lane-geometry control surfaces, or
2. frame the current result as source-bound DD2 audit evidence only, not semantic success.

semantic_success_claim_allowed: false
gpu_smoke_allowed: false
