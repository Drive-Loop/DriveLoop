# Candidate70 Source-Bound Actor Motion Full-Coverage Gate

Date: 2026-07-04

## Summary

The candidate70 measured_failed GPU smoke exposed a structural weakness: the old readiness gate accepted source-bound actor motion evidence when any per-frame append existed. That allowed 24/48 actor motion coverage to count as connected.

The gate now requires full 48/48 source-bound actor motion coverage before the candidate70 path is considered structurally ready for another short GPU smoke.

## Required Coverage

The gate requires:

- expected_rows: 48
- override_entry_count: 48
- boxes3d_changed_count: 48
- image_box_changed_count: 48
- per_frame_append_row_count: 48
- per_frame_append_count: 48
- sample_identity_applied_count: 48
- no_matching_frame_idx_count: 0
- runtime input audit exists
- paper alignment report exists

## Claim Boundary

This is still structural conditioning evidence only. It is not GPU approval and not video semantic success. semantic_success_claim_allowed remains false until an explicit measured_passed review exists.
