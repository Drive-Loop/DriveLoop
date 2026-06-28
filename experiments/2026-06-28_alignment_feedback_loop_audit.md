# Alignment Feedback Loop Audit

Date: 2026-06-28

## Scope

This note documents the non-GPU alignment feedback work added after the DD2 tensor override audit.

It covers an auditable prompt-video alignment evaluator, manual review pack generation, and a mock-backed feedback-loop demo. It does not claim video semantic correctness or tensor-level correction of visual failures.

## Relevant Commits

- `d7534e4` - add auditable prompt video alignment evaluator
- `acc517e` - add prompt video alignment eval script
- `5545e1b` - clarify prompt video alignment claim states
- `bbb03ac` - add manual alignment review pack script
- `84b79d7` - feed alignment diagnostics into refiner
- `70d694c` - cover alignment feedback runner refinement
- `c1b5fa3` - carry alignment feedback in refinement state
- `837bce5` - trace alignment feedback in DD2 condition
- `790a185` - add alignment feedback loop demo

## Implemented Evidence Path

1. A generated video can be paired with an external alignment report.
2. `PromptVideoAlignmentEvaluator` scores only explicit external reports.
3. Missing reports produce `not_measured`.
4. Failed required checks produce `measured_failed`.
5. Passed required checks produce `measured_passed`.
6. `run_manual_alignment_review_pack.py` extracts review frames and writes a default-failing manual report template.
7. `RuleBasedRefiner` maps failed alignment checks into text feedback constraints.
8. The refinement state carries structured `alignment_feedback`.
9. `DriveDreamer2ConditionAdapter` records that feedback in `executable_condition.trace_metadata`.
10. `run_alignment_feedback_loop_demo.py` demonstrates this control flow with a mock backend.

## Verified Non-GPU Tests

Most recent server validation:

- `tests/test_alignment_feedback_loop_demo.py`: 2 passed
- full non-GPU test suite: 79 passed
- `git diff --check`: passed

## What This Proves

- Alignment evaluation now has an auditable entry point.
- The system no longer treats a video artifact as semantic success.
- Alignment failures can influence the next prompt through the refiner.
- Alignment feedback is carried as structured state into the next backend request.
- DD2 condition trace records alignment feedback for audit.
- A mock-backed control-flow demo shows evaluator -> refiner -> condition trace feedback across two iterations.

## What This Does Not Prove

- It does not prove the motorcycle GPU smoke video semantically matches the prompt.
- It does not inspect video pixels automatically.
- It does not run a perception model, VLM, detector, or tracker.
- It does not prove DD2 diffusion responds correctly to the refined prompt.
- It does not convert alignment failures into verified tensor-level DD2 controls.
- `alignment_feedback.control_level` is explicitly `text_feedback_only`.

## Claim Boundary

Allowed wording:

> We implemented an auditable alignment feedback path and demonstrated, with a mock backend, that alignment failures can drive refinement state and appear in the next DD2 condition trace.

Disallowed wording:

> DriveLoop has solved prompt-to-video semantic alignment.

> The motorcycle video is semantically correct.

> Alignment feedback is verified tensor-level DD2 control.

## Recommended Next Step

Attach a real external review source to the evaluator:

1. Manual review using the generated contact sheet.
2. Lightweight VLM review with saved prompts and raw responses.
3. Detector/tracker-based object presence and motion evidence.
4. Only after that, run short DD2 audit-only or GPU smoke to test whether refined prompts change the intended tensor/runtime evidence.
