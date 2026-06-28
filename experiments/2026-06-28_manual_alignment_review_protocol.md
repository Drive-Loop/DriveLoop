# Manual Prompt-Video Alignment Review Protocol

Date: 2026-06-28

## Purpose

This protocol defines how to manually review generated driving videos for prompt-video alignment without overstating results.

Manual review is an external evidence source for `PromptVideoAlignmentEvaluator`. It is not a tensor audit and does not prove why a model produced a visual element.

## Required Evidence

Reviewers must use the generated review pack:

- contact sheet
- sampled frame images
- original video path
- prompt text
- report JSON with explicit checks

Each passed check must include:

- `evidence`: short text summary
- `evidence_frames`: one or more frame filenames or frame indices
- `rationale`: why the evidence supports the check
- `score`: numeric confidence from 0.0 to 1.0

A check must remain failed if evidence is absent, ambiguous, or only inferred from the prompt.

## Scoring Rules

Use conservative scores:

- `0.0`: not visible, not reviewed, or contradicted by evidence
- `0.25`: weak or highly ambiguous evidence
- `0.5`: partially visible but insufficient for a strong claim
- `0.75`: mostly visible with minor ambiguity
- `1.0`: clear evidence across the sampled frames or video

The report should pass only when all required checks are passed and the average required score meets the evaluator threshold.

## Required Checks For Motorcycle Prompt

Prompt:

`daytime urban road with a motorcycle changing lane from the left`

Required checks:

1. `object_presence.motorcycle`
   - Pass only if a motorcycle-like actor is visibly present.
   - Do not pass if the actor could plausibly be a car, bicycle, or artifact.

2. `spatial_relation.left_lane_change`
   - Pass only if motion or position over time supports a lane change from the left.
   - A single static frame is usually insufficient.

3. `lighting.daytime`
   - Pass if frames clearly show daytime lighting.

4. `scene_type.urban_road`
   - Pass if the scene is plausibly an urban road or street setting.

## Claim Boundary

Allowed wording:

> Manual review found evidence for selected prompt-video alignment checks.

Disallowed wording:

> The model reliably follows the prompt.

> The visual semantics are proven by tensor audit.

> The alignment failure is fixed at the DD2 tensor level.

## Workflow

1. Inspect the contact sheet.
2. Inspect individual frames if needed.
3. Optionally inspect the original video.
4. Fill `manual_alignment_report_review_v0.json`.
5. Run `scripts/run_prompt_video_alignment_eval.py` on the filled report.
6. Record `not_measured`, `measured_failed`, or `measured_passed`.
