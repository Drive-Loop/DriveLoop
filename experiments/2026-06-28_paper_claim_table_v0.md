# Paper Claim Table v0

Date: 2026-06-28

## Purpose

Record which DriveLoop / DriveDreamer-2 claims are currently supported, unsupported, or pending additional evidence.

This table is intended for paper writing and reviewer-facing audit clarity.

## Claim Table

| Topic | Claim | Current Status | Evidence | Paper Wording Boundary |
|---|---|---:|---|---|
| Multimodal prompt intake | DriveLoop accepts text, image, and uploaded audio style inputs as multimodal prompt context. | supported | Rule-based intent adapter and smoke suite metadata paths | Say "supports multimodal prompt intake/prototyping"; avoid claiming robust open-vocabulary multimodal understanding. |
| ASR transcript safety | Raw ASR transcript is preserved and suggested transcript is advisory. | supported by design constraint | Project protocol and implementation policy | Say raw transcript is preserved; accepted transcript must come from user confirmation/edit before Generate. |
| Structured intent grounding | Prompt is grounded into structured intent / executable condition. | supported | `driveloop/grounding.py`, condition adapter tests | Say rule-based grounding prototype; avoid claiming learned general semantic parsing. |
| DD2 text conditioning | Refined motorcycle prompt changed DD2 text conditioning. | supported | `outputs/driveloop/dd2_runtime_hash_compare/motorcycle_earlier_vs_refined.json` | Say prompt refinement changed `prompt_embed`; do not say it fixed video behavior. |
| DD2 structural override | DriveLoop can auditably alter DD2 `scene_description`, `boxes3d`, and derived `image_box`. | supported | refined audit-only changed counts and runtime audit outputs | Say static structural conditioning is connected and auditable. |
| Image conditioning | Refined motorcycle audit-only did not change `img_cond` versus earlier audit-only. | supported negative result | runtime hash compare | Say image conditioning remained mini-dataset/baseline constrained in this comparison. |
| HDMap override | HDMap override control is available. | unsupported | motion gap and evidence index | Say HDMap remains baseline/not verified. |
| Velocity tensor control | DD2 runtime consumes velocity tensor for motion control. | unsupported | velocity surface audit | Say dataset labels include velocities, but runtime consumption was not observed. |
| Trajectory tensor control | DriveLoop controls lane-change trajectory tensors in DD2. | unsupported | trajectory control contract status `not_runtime_connected` | Say a trajectory control contract defines required evidence; do not claim runtime control. |
| Temporal actor motion | DriveLoop has verified temporal lane-change motion control. | unsupported | motion control gap audit | Say temporal lane-change motion remains unverified. |
| Motorcycle object presence | Earlier motorcycle smoke showed partial motorcycle/cyclist-like visual evidence. | measured with caveat | manual review score 0.6 | Say manual review found partial/ambiguous object evidence. |
| Left lane change video semantics | Earlier motorcycle smoke showed visible left lane change. | measured_failed | manual review score 0.0 | Say the prior video failed the lane-change check. |
| Refined prompt video semantics | Refined prompt fixes lane-change generation. | not measured | no refined GPU video generated | Say not evaluated yet; requires gated GPU smoke plus review. |
| GPU smoke readiness | A short candidate GPU smoke is audit-ready under gated protocol. | supported as readiness only | readiness gate, command plan, runbook, protocol | Say ready to generate a candidate video; not ready to claim semantic success. |
| Post-GPU review | Candidate videos must pass explicit review before measured semantic claims. | supported by workflow | post-GPU review gate and alignment evaluator | Say measured claims are derived only from explicit manual/perception/VLM review reports. |
| Negative-result reporting | Negative alignment results are preserved. | supported | manual review, evidence index, alignment summary tooling | Say negative evidence is retained and used for refinement. |

## Safe Paper Language

The current evidence supports language like:

- "DriveLoop translates multimodal scenario prompts into auditable DriveDreamer-2 text and structural conditioning inputs."
- "For the refined motorcycle scenario, audit-only execution changed text conditioning while static structural and image-conditioning hashes remained unchanged relative to the earlier audit-only run."
- "The system records a clear boundary between tensor-level changes and video-level semantic claims."
- "A previous motorcycle candidate was manually reviewed as failing the visible left-lane-change criterion, and this negative result is retained in the refinement loop."

## Unsafe Paper Language

Do not write:

- "DriveLoop solves prompt-to-video alignment for motorcycle lane changes."
- "DriveLoop controls lane-change trajectories in DriveDreamer-2."
- "Runtime tensor changes prove that the video follows the prompt."
- "The refined prompt fixes the lane-change failure."
- "HDMap and temporal actor motion are controlled end to end."

## Evidence Needed To Upgrade Claims

To upgrade the motorcycle lane-change claim, the project needs:

1. Gated short GPU smoke candidate generation.
2. Preserved video artifact and runtime audit metadata.
3. Post-GPU review gate output.
4. Explicit manual/perception/VLM review report.
5. Prompt-video alignment evaluation.
6. Recorded result as `measured_failed` or `measured_passed`.

To upgrade trajectory-control claims, the project needs:

1. Actor track identity.
2. Per-frame actor boxes3d.
3. Runtime-consumed velocity/displacement or trajectory tensor.
4. HDMap lane geometry evidence.
5. Temporal consistency audit.
6. Video-level review evidence.
