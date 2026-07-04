# Candidate70 GPU Retry Approval Template

Date: 2026-07-04

## Summary

Candidate70 now has a GPU retry approval template generator.

This does not approve a retry by default, does not run GPU, and does not generate video.

## Purpose

The template separates three ideas:

1. non-GPU retry readiness
2. explicit user approval for one short GPU retry
3. post-GPU measured review

The approval artifact is not semantic success evidence.

## Default Behavior

The script writes a template with:

- approved_for_candidate70_gpu_retry: false
- approval_status: template_not_approved
- requires_post_gpu_review: true
- approval_is_not_semantic_success: true
- does_not_run_gpu: true
- does_not_generate_video: true

## Approval Contract

The candidate70 retry gate only accepts an approval artifact when:

- scenario_id is candidate70_night_cut_in_gpu_smoke
- approved_for_candidate70_gpu_retry is true
- requires_post_gpu_review is true
- approval_is_not_semantic_success is true

Even then, approval only permits a bounded retry attempt. It does not permit a semantic success claim.

## Claim Boundary

Allowed claim:

- Candidate70 has an auditable approval artifact template for future GPU retry decisions.
- The template can record explicit approval later if the user chooses to approve one short retry.

Forbidden claims:

- Do not treat the template as approval.
- Do not run GPU from the template generator.
- Do not claim semantic success from approval.
- Do not skip post-GPU review.
