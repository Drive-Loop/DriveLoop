# GPU Smoke Protocol v0

Date: 2026-06-28

## Purpose

Define when DriveLoop may run a short DriveDreamer-2 GPU smoke and what claims are allowed afterward.

## Pre-GPU Evidence Required

Before running GPU smoke, the project must preserve:

- DD2 runtime hash comparison between earlier and refined audit-only runs
- motion control gap audit
- DD2 velocity surface audit
- trajectory control contract
- GPU smoke readiness gate output

The readiness gate must report `gpu_smoke_allowed: true`.

## Allowed GPU Scope

Only a single short candidate generation is allowed by this protocol.

The generated artifact may only be described as:

- candidate video generated
- not yet semantically measured

## Disallowed Claims After GPU Smoke Alone

A successful GPU run does not prove:

- prompt-to-video semantic success
- visible lane-change behavior
- temporal actor motion control
- trajectory tensor control
- HDMap override control

## Required Post-GPU Steps

After candidate video generation:

1. Preserve the video artifact.
2. Preserve DD2 runtime input audit metadata.
3. Run the post-GPU review gate.
4. Generate a manual review pack.
5. Complete an explicit manual, perception, or VLM review report.
6. Run prompt-video alignment evaluation from that explicit report.
7. Record `measured_failed` or `measured_passed` only from the explicit review result.

## Current Motorcycle Boundary

For the refined motorcycle prompt, current audit evidence shows that the refinement changed text conditioning, while static structure and image conditioning hashes did not change between earlier and refined audit-only runs.

This means the refined GPU smoke, if run, should be treated as a candidate test of text refinement only. It must not be claimed as lane-change control unless explicit review evidence supports that claim.

## Command Plan

Use `scripts/run_single_gpu_smoke_command_plan.py` to regenerate the audited command sequence.

The command plan includes:

- readiness gate command
- candidate GPU smoke command
- post-GPU review gate command
- alignment evaluation command template

## Claim Boundary

Runtime tensor audits can prove runtime inputs changed. They cannot prove video semantics.

Video semantic claims require explicit visual, perception, or VLM review evidence.
