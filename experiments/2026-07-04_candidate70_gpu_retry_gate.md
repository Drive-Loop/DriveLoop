# Candidate70 GPU Retry Gate

Date: 2026-07-04

## Summary

Candidate70 now has an explicit GPU retry gate inside the existing non-GPU readiness gate.

This does not run GPU and does not approve a GPU retry by itself.

## Gate Policy

The retry gate requires all of the following before a candidate70 GPU retry can be allowed:

1. source-bound actor motion has full 48/48 coverage
2. local-map-vector HDMap lane geometry replacement reaches the grounding surface
3. semantic alignment protocol is defined
4. closed-loop status has automatic perception measured_failed connected
5. perception video evaluation is measured_failed
6. an explicit user approval artifact exists for candidate70 GPU retry

The gate keeps semantic_success_claim_allowed false before retry. Retry approval is not a semantic success claim.

## Approval Artifact Contract

Expected approval path:

- outputs/driveloop/gpu_retry_approval/candidate70_gpu_retry_approval.json

Expected approval fields:

- approved_for_candidate70_gpu_retry: true
- scenario_id: candidate70_night_cut_in_gpu_smoke
- requires_post_gpu_review: true
- approval_is_not_semantic_success: true

## Current Status

The current live candidate70 gate should remain blocked until explicit approval exists.

Expected current retry blocker:

- explicit_gpu_retry_approval_missing

## Claim Boundary

Allowed claim:

- Candidate70 has a non-GPU retry gate that checks structural readiness, perception measured_failed evidence, closed-loop attachment, and explicit approval.
- The gate can identify when the only remaining retry blocker is missing explicit approval.

Forbidden claims:

- Do not claim semantic success.
- Do not treat retry approval as semantic success.
- Do not run GPU from this gate automatically.
- Do not skip post-GPU review after any approved retry.
