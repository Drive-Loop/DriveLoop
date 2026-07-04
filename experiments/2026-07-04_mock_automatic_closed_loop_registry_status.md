# Mock Automatic Closed-loop Registry Status

Date: 2026-07-04

## What changed

The closed-loop experiment registry now reads `automatic_closed_loop_manifest.json` artifacts and records automatic-loop evidence in each case record.

## Current registry evidence

- `case_count`: 2
- `case_study_claim_allowed_count`: 1
- `paper_claim_allowed_count`: 0
- `automatic_multiround_supported_count`: 1
- `automatic_closed_loop_manifest_available_count`: 1
- `registry_automatic_closed_loop_manifest_is_not_video_semantic_success`: true

## Case separation

- `candidate70_failed_to_passed`
  - task family: `motorcycle_cut_in`
  - evidence level: `case_study_evidence`
  - automatic multiround supported: false
  - role: measured failed-to-passed single-case evidence with manual review

- `mock_automatic_closed_loop_demo`
  - task family: `mock_automatic_closed_loop`
  - evidence level: `metadata_only`
  - automatic multiround supported: true
  - role: non-GPU proof that the system can execute generate, evaluate, diagnose, refine, and regenerate across multiple attempts

## Claim boundary

This is not real DD2 semantic success evidence. The mock automatic case supports the Algorithm 1 engineering loop only. The candidate70 case remains separate and should not be claimed as automatic multiround evidence.

## Verification

- `python -m pytest tests/test_closed_loop_experiment_registry.py tests/test_automatic_closed_loop_manifest.py -q`
- result: `17 passed`
