# Motorcycle Refined GPU Smoke Result

Date: 2026-06-30

## Scenario

- Scenario ID: `motorcycle_refined_candidate_gpu_smoke`
- Prompt: `daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.`
- Video artifact: `outputs/driveloop/motorcycle_refined_candidate_gpu_smoke/artifacts/motorcycle_refined_candidate_gpu_smoke/iteration_00.mp4`
- Runtime audit: `outputs/driveloop/motorcycle_refined_candidate_gpu_smoke/artifacts/motorcycle_refined_candidate_gpu_smoke/dd2_runtime_input_audit_00.json`
- Manual review report: `outputs/driveloop/post_gpu_review_gate/motorcycle_refined_candidate_gpu_smoke/manual_review_pack/manual_alignment_report.json`
- Alignment evaluation: `outputs/driveloop/prompt_video_alignment_eval/motorcycle_refined_candidate_gpu_smoke_manual_review/prompt_video_alignment_evaluation.json`
- Dashboard: `outputs/driveloop/experiment_status_dashboard/motorcycle_refined_candidate_dashboard.json`

## Result

- Candidate generated: yes
- Bundle status: `measured_ready`
- Video semantic claim: `measured_failed`
- Semantic success claim allowed: `false`

## Manual Review Summary

The generated video was reviewed from the video and frame contact sheet.

Required checks:

- `object_presence.motorcycle`: failed, score `0.3`
  - A bicycle/cyclist-like object is visible, but the reviewer was not confident it is a motorcycle.
- `spatial_relation.left_lane_change`: failed, score `0.0`
  - No visible lane change from the left was observed.
  - The road center marking appears to be double solid lines, which conflicts with the requested lane-change maneuver.
- `lighting.daytime`: passed, score `1.0`
  - The scene is visibly daytime.
- `scene_type.urban_road`: passed, score `0.8`
  - The scene appears to be a modern road environment.

## Audit Interpretation

This run is a negative result.

The GPU run generated a candidate video, but the explicit manual review failed the required motorcycle and left-lane-change checks. Therefore this run does not support a prompt-to-video semantic success claim.

Runtime/tensor evidence remains limited to input/control surfaces. It can support claims that runtime inputs changed, but it cannot prove video semantics.

Observed runtime/control evidence:

- `scene_description`: changed
- `boxes3d`: changed
- `image_box`: changed
- `image_hdmap`: kept from mini dataset baseline
- trajectory tensor control: `not_runtime_connected`
- temporal lane-change motion control: `not_verified`
- velocity consumed by DD2 runtime: `false`

## Claim Boundary

Allowed claims:

- A gated short GPU candidate was generated.
- The candidate bundle reached `measured_ready`.
- Manual prompt-video review measured the candidate as failed.
- Runtime/control audits show changed input tensors and known limitations.

Disallowed claims:

- Do not claim prompt-to-video semantic success.
- Do not claim visible motorcycle lane-change success.
- Do not claim trajectory control or temporal lane-change control.
- Do not claim HDMap override control.
