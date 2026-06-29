# Mini Motorcycle Candidate Pool Assessment

Date: 2026-06-30

## Goal

Assess whether the available nuScenes v1.0-mini DD2 candidate pool can support a paper-level prompt-to-video success claim for:

`daytime urban multi-lane road with dashed lane markings, a motorcycle or scooter in the left adjacent lane performs a visible lane change into the ego lane while cars overtake nearby, panoramic multi-view video.`

## Evidence Summary

The mini validation pool was too small and structurally unsuitable:

- `cam_all_val/v0.0.2` had only 19 DD2 candidate starts.
- Those candidates covered only two scenes:
  - pedestrian/cyclist/bike-rack urban scene
  - parking lot with parked bicycles/scooters/motorcycle
- A previous val GPU candidate did not show a visible motorcycle lane change.

The mini train pool had more candidates:

- `cam_all_train/v0.0.2` had 73 DD2 candidate starts across 8 scenes.
- Candidate 38 was selected because it was daytime, road/intersection-like, and had moving scooter/motorcycle context.
- Runtime audit confirmed targeted selection:
  - selected batch index: 38
  - dataset: `cam_all_train/v0.0.2`
  - prompt, image conditioning, grounding, and box tensors were present.
- Generated video was source-consistent and visibly different from the val candidate.
- Human review found that the generated video did not clearly preserve or synthesize the motorcycle target.
- Source review confirmed the source material did contain a rider on a motorcycle, but the target was small/back-facing and weakly visible.

Additional candidate review:

- Candidate 4 and candidate 5 contain a motorcycle, but it appears parked/static and partially occluded by buildings.
- Candidate 38 is still more relevant to dynamic road context, despite the motorcycle being small/back-facing.
- Night candidates had stronger motorcycle/scooter labels, but they conflict with the daytime prompt and introduce difficult-lighting confounds.

## Conclusion

The current v1.0-mini DD2 candidate pool does not contain a strong motorcycle lane-change candidate suitable for a paper-level semantic success claim.

This is a negative result, not a prompt success:

- `video_semantic_claim`: `measured_failed`
- `semantic_success_claim_allowed`: `false`
- Main blocker: weak/occluded/small motorcycle source visibility plus DD2 generation failing to preserve the target actor clearly.
- Tensor audits demonstrate changed/targeted runtime inputs, but do not prove video semantics.

## Recommended Next Step

Do not continue blind GPU search on the mini candidate pool.

Recommended paths:

1. Expand to a larger nuScenes processed split or full trainval pool and search for a clearer motorcycle/scooter candidate.
2. Temporarily test a more visible target class, such as car/bus lane-change, to validate the DriveLoop control and review pipeline.
3. If motorcycle remains required, search for candidates with:
   - daytime lighting
   - front or front-left camera visibility
   - large/near motorcycle target
   - minimal occlusion
   - dynamic road context
   - lane-compatible road topology
