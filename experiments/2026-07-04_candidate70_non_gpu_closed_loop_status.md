# Candidate70 Non-GPU Closed-Loop Status

Date: 2026-07-04

## Summary

Candidate70 now has a non-GPU closed-loop status artifact that connects the measured_failed semantic review to taxonomy, rule-based refinement, source/runtime readiness, and remaining blockers.

This does not claim semantic success and does not approve another GPU run.

## Closed-Loop Artifact

Output:

- outputs/driveloop/candidate70_closed_loop_status/candidate70_closed_loop_status.json

Status:

- status: measured_failed_refinement_proposal_ready
- does_not_run_gpu: true
- does_not_generate_video: true
- semantic_success_claim_allowed: false

## Connected Steps

The artifact connects:

1. measured_failed alignment evaluation
2. failure taxonomy
3. refinement proposal
4. source binding readiness
5. runtime conditioning readiness gate
6. HDMap runtime surface evidence

Observed step statuses:

- measured_failed_alignment_evaluation: measured_failed
- failure_taxonomy: available
- refinement_proposal: available
- source_binding_readiness: ready
- runtime_conditioning_readiness: blocked
- hdmap_runtime_surface: local_map_vector_lane_geometry_replacement_reaches_grounding_surface

## Key Interpretation

Source binding is ready and candidate support is not the primary blocker.

The current blockers are semantic/evaluation loop blockers:

- semantic_success_claim_not_allowed
- generated_video_target_motorcycle_not_visible
- generated_video_target_actor_not_trackable
- generated_video_cut_in_not_measurable
- generated_video_lateral_motion_not_measurable
- automatic_perception_evaluator_not_yet_connected
- multi_round_regeneration_not_yet_automated

## Claim Boundary

Allowed claim:

- Candidate70 measured_failed evidence is now connected to a repeatable non-GPU closed-loop status artifact.
- The system can produce a refinement proposal from the measured_failed review.
- Source binding and runtime conditioning evidence are available as structural/audit evidence.

Forbidden claims:

- Do not claim semantic success.
- Do not set semantic_success_claim_allowed to true.
- Do not claim the generated video contains a visible motorcycle cut-in.
- Do not treat taxonomy, refinement, source binding, HDMap, or runtime conditioning evidence as video semantic proof.
- Do not run another GPU smoke without explicit approval and post-GPU review.

## Next Technical Direction

The next non-GPU priorities are:

1. connect or implement an automatic perception evaluator for object visibility, trackability, lateral motion, and cut-in checks
2. turn the refinement proposal into an audit-only condition/source/runtime check
3. only after those pass, request explicit approval for a short GPU retry
