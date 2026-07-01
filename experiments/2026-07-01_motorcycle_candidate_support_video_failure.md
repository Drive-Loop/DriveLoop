# Motorcycle Candidate Support vs Video Failure Evidence

Date: 2026-07-01

## Scope

This note records the current refined motorcycle experiment boundary:

- the source candidate is prompt-conditional and allowed
- a candidate video exists
- the completed manual alignment evaluation is measured
- the video semantic result is `measured_failed`

This document must not be interpreted as a success claim.

## Accepted Prompt

`daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.`

## Source Candidate Support

Prompt-conditional candidate audit:

`outputs/driveloop/prompt_conditional_candidate_audit/motorcycle_source_candidate_rank16_audit.json`

Result:

- `status`: `allowed`
- `allowed`: `true`
- requested rules:
  - `motorcycle`
  - `lane_change`
  - `daytime`
  - `urban`
- missing requested support: none
- unrequested selection bias: none

Interpretation:

The selected source candidate is acceptable as prompt-conditioned dataset support for this motorcycle lane-change investigation.

This does not prove generation success.

## Generated Candidate Video

Video artifact:

`outputs/driveloop/motorcycle_refined_candidate_gpu_smoke/artifacts/motorcycle_refined_candidate_gpu_smoke/iteration_00.mp4`

Dashboard state:

`outputs/driveloop/experiment_status_dashboard/motorcycle_refined_candidate_dashboard.json`

Recorded state:

- `dashboard_status`: `measured_ready`
- `candidate_status`: `candidate_video_only`
- `bundle_status`: `measured_ready`
- `video_semantic_claim`: `measured_failed`
- `semantic_success_claim_allowed`: `false`
- `source_candidate_support_status`: `allowed`

Interpretation:

The pipeline produced a candidate video and review/evaluation artifacts are present, but semantic success remains disallowed because the explicit review result failed.

## Manual Alignment Evaluation

Alignment evaluation:

`outputs/driveloop/prompt_video_alignment_eval/motorcycle_refined_candidate_gpu_smoke_manual_review/prompt_video_alignment_evaluation.json`

Overall result:

- score: `0.525`
- video semantic claim: `measured_failed`
- required checks: 4
- passed required checks: 2

Failed checks:

1. `object_presence.motorcycle`
   - passed: `false`
   - score: `0.3`
   - evidence: a bicycle/cyclist-like object is visible, but reviewer is not confident it is a motorcycle

2. `spatial_relation.left_lane_change`
   - passed: `false`
   - score: `0.0`
   - evidence: no visible lane change from the left was observed; road center marking appears to be double solid lines, conflicting with the requested maneuver

Passed checks:

1. `lighting.daytime`
   - passed: `true`
   - score: `1.0`

2. `scene_type.urban_road`
   - passed: `true`
   - score: `0.8`

## Interpretation

This result separates three layers:

1. Source candidate support: allowed
2. Candidate video generation: available
3. Prompt-video semantic alignment: measured failed

The failure is no longer simply "no candidate support." It is a generation/alignment failure under a source candidate that supports the requested prompt conditions.

## Claim Boundary

Allowed claims:

- The selected source candidate is prompt-conditionally allowed for the accepted prompt.
- A candidate video was generated.
- Manual alignment evaluation was completed.
- The candidate video failed motorcycle object confidence and visible left-lane-change checks.

Disallowed claims:

- The refined prompt produced a semantically correct motorcycle lane-change video.
- Source candidate support proves generation success.
- Candidate video existence proves prompt-video alignment.
- Runtime tensor/hash changes prove video semantics.
- Lane-change temporal motion control is verified.

## Recommended Next Work

Do not overfit with hard-coded defaults.

Recommended next non-GPU work:

1. Add a failure taxonomy summarizer that classifies this result as:
   - candidate_support_allowed
   - video_generated
   - semantic_measured_failed
   - object_identity_failed
   - lane_change_motion_failed

2. Use the taxonomy to guide the next intervention:
   - improve candidate-to-DD2 structural conditioning
   - audit whether candidate-derived boxes/HDMap/trajectory surfaces are actually consumed
   - investigate whether DD2 can represent the requested maneuver under this source candidate

Recommended GPU work only after a concrete intervention:

1. Run a new audit-only/runtime audit proving the intervention changed target runtime inputs.
2. Run one gated candidate GPU smoke.
3. Run post-GPU review gate.
4. Complete explicit review/eval.
5. Record measured result, including negative results.
