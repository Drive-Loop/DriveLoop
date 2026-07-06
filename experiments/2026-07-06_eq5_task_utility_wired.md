# Eq.(5) task-aware utility wired into the closed loop

Date: 2026-07-06

## What was added

- `driveloop/utility.py`: J = w_p*S_perc + w_c*S_ctrl + w_i*S_intent.
  - S_perc: evaluator score (perception path).
  - S_ctrl: measured alignment score when present in evaluation metrics
    (`alignment_score`), otherwise plan-level control coverage (Eq. 10).
  - S_intent: recall-oriented retention of the original grounded intent
    (objects, motion primitives, relations, informative environment).
- `DriveLoopConfig.use_task_utility` (default False) and
  `DriveLoopConfig.utility_weights`.
- When enabled, the runner computes J per attempt, records
  J/S_perc/S_ctrl/S_intent in evaluation metrics, and uses J as the
  acceptance score against target_score (Algorithm 1 threshold tau).

## Tests

- tests/test_utility.py: 7 tests (weights, intent retention, ctrl source).
- tests/test_runner_task_utility.py: 4 tests (default-off, metric injection,
  weight override, early stop by J).
- Full suite: 336 passed.

## Claim boundary

Eq.(5) is an acceptance/refinement principle, not a training objective. J is
not evidence of semantic success; S_ctrl falls back to plan-level coverage
when no measured alignment is available and is marked accordingly.
