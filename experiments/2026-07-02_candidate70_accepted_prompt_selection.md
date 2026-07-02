# Candidate70 Accepted Prompt Selection v0

Date: 2026-07-02

## Scope

This note records the first user-confirmed accepted prompt selection for candidate70 GPU readiness.

It does not run GPU inference, generate video, modify Generate business logic, or claim prompt-to-video semantic success.

## Selected Prompt

- selected_prompt_id: c70_pos_001
- split: candidate70_positive
- support_expectation: candidate_supported
- tags: motorcycle, night, urban, cut_in, left, ego_vehicle
- prompt: night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.

## Claim Boundary

- This accepted prompt selection is not GPU approval.
- This accepted prompt selection is not video semantic success.
- This accepted prompt selection does not connect runtime motion control.
- This accepted prompt selection does not prove lane-change control.
- This accepted prompt selection does not prove true lane-geometry replacement.

## Next Required Steps

- Wire the accepted prompt selection into the candidate70 GPU readiness gate.
- Keep GPU smoke blocked until explicit user approval.
- Keep semantic success blocked until measured video review evidence exists.

