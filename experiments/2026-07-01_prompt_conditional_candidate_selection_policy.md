# Prompt-Conditional Candidate Selection Policy

Date: 2026-07-01

## Core Principle

DriveLoop / DriveDreamer-2 generation must be driven by the user's accepted prompt.

The system must not use a fixed scene, fixed object class, fixed candidate, or fixed background as a default. If the prompt asks for a motorcycle, the candidate search may look for motorcycle-supporting data. If the prompt does not ask for a motorcycle, the system must not force motorcycle candidates into the generation path.

In short:

- The prompt defines the target video semantics.
- Candidate selection is conditional on the prompt.
- Dataset candidates are evidence/support for a requested condition, not hidden defaults.
- If no suitable candidate exists, record a negative result instead of changing the task.

## Required Boundary

1. Do not hard-code a dataset candidate as the default generation scene.
2. Do not force motorcycle/scooter candidates unless the accepted prompt asks for motorcycle/scooter or a semantically compatible target.
3. Do not force lane-change candidates unless the accepted prompt asks for lane-change or compatible road motion.
4. Do not silently add objects, roads, weather, lighting, or actors that are not requested by the accepted prompt.
5. Do not rewrite ASR mistakes into target words with hard-coded rules.
6. Preserve `raw_transcript`.
7. Treat `suggested_transcript` only as a suggestion.
8. Only user-confirmed or edited `accepted_transcript` may enter Generate.
9. If DD2 data support is weak or absent for the requested prompt, record that as a negative result.
10. Do not claim prompt-to-video semantic success unless the generated video is reviewed and measured as semantically matching the prompt.

## DD2-Specific Interpretation

DriveDreamer-2 is not a pure prompt-to-video model. It strongly depends on dataset candidates for:

- background
- road topology
- HDMap
- initial image
- boxes / actors
- camera views
- temporal context

Therefore, prompt-conditioned generation requires a candidate support audit before GPU generation when the prompt depends on concrete scene structure.

Examples:

- If the prompt requests motorcycle lane-change, first search for candidates with visible motorcycle/scooter, compatible road context, and temporal continuity.
- If the prompt requests rainy night traffic, search for rainy/night/traffic-supporting candidates.
- If the prompt requests pedestrians crossing, search for pedestrian crossing candidates.
- If the prompt does not specify motorcycle, do not bias the retrieval toward motorcycle.

## Current Motorcycle Investigation Example

The full nuScenes trainval audit found stronger motorcycle source candidates than v1.0-mini.

A manually reviewed source candidate was identified:

- rank: 16
- split: train
- front anchor index: 369792
- related selected view: cam_front_right index 370271
- source review: daytime, clear, dynamic, motorcycle visible, lane-related context

This candidate is not a general default. It is only a prompt-specific candidate for the motorcycle-related investigation.

## Claim Boundary

A strong source candidate does not prove DD2 generation success.

- Source candidate support means the dataset contains relevant evidence.
- Runtime tensor audit means selected tensors/conditions changed or were targeted.
- Generated video existence means only that video generation ran.
- Prompt-to-video semantic success requires visual/manual/perception/VLM review of the generated video.
- Negative results must be recorded honestly.
