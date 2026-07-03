# Paper Loop Contract Alignment

Date: 2026-07-03

Commit recorded: `da2c8fc feat: align driveloop pipeline with paper loop contracts`

## Purpose

This note records the code alignment work that closed the main gap between the current DriveLoop code and the paper-style closed-loop DriveDreamer-2 workflow.

The work was intentionally non-GPU. It added executable contracts, runtime records, and auditable claim boundaries, but it does not claim video semantic success by itself.

## Implemented

1. Algorithm-style attempt state
   - Added `DriveLoopAttempt`.
   - Added `DriveLoopResult.attempt_history`.
   - Persisted attempt records into `history.jsonl`.
   - Recorded scene specification, long-tail plan, DD2 condition package, source binding, source selection, generation, evaluation, refinement, status, and claim boundary per attempt.

2. Perception evaluation loop
   - Allowed runner/API evaluator injection through `BaseEvaluator`.
   - Integrated optional `PerceptionVideoEvaluator` through `CompositeEvaluator`.
   - Preserved measured perception metrics in attempt history.

3. Source selection contract
   - Added `SourceSelection`, `NoOpSourceSelector`, and `DD2SourceSelector`.
   - Wired source selection into runner metadata and attempt records.
   - Blocked acceptance when requested source selection is unavailable.

4. Long-tail condition support
   - Expanded long-tail tags for vulnerable road users, motorcycle cut-in, motorcycle lane change, and left/right lane relations.
   - Added structured executable controls and perception requirements for these conditions.

5. Diagnosis-driven refiner
   - Added perception, source-selection, and runtime-control feedback branches.
   - Preserved claim boundaries when feedback is only advisory or audit-level.

6. Experiment pipeline
   - Added `ExperimentPipeline`, `ExperimentCase`, `ExperimentPipelineConfig`, and `load_experiment_cases`.
   - Added `scripts/run_driveloop_experiment.py`.
   - Pipeline writes per-case `result.json`, `attempts.jsonl`, `history.jsonl`, `case_summary.json`, plus run-level `summary.json` and `summary.md`.

## Verification

Before commit and push:

- `git diff --cached --check`: passed
- `pytest -q tests`: `218 passed, 1 warning`
- no GPU training or DD2 video generation was run

No-GPU smoke run:

- manifest: `outputs/driveloop/experiment_pipeline_smoke/cases.json`
- summary: `outputs/driveloop/experiment_pipeline_smoke/run/summary.md`
- mock accepted count: `2`
- mock semantic success claim allowed count: `0`

## Claim Boundary

The code now records more of the paper loop, but these records are not proof of generated video semantic success.

In particular:

- Mock backend acceptance is not DD2 GPU evidence.
- Source selection readiness is not GPU approval.
- Runtime control feedback is not verified trajectory control.
- Perception metrics can support evaluation, but detector/tracker metrics alone do not prove full prompt-video semantic success.
- A semantic success claim still requires measured, passed alignment/perception evaluation on generated DD2 outputs, with source/candidate support verified.

## Next Work

1. Add a real DD2 backend adapter path into the experiment pipeline.
2. Add a CPU-only candidate pool audit manifest for paper cases.
3. Run source-bound DD2 smoke only after candidate/source readiness gates pass.
4. Attach measured perception/alignment evidence before making any semantic-success claim.
