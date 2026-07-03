# Current P0 Status After Semantic Alignment Protocol Gate

Date: 2026-07-03

## One-Line Status

Candidate70 P0 structural runtime/input readiness is addressed, and the semantic/alignment review protocol is now defined. P0 semantic success is still not claimed. The default readiness gate remains blocked only by semantic_success_claim_not_allowed.

## Latest Non-GPU Verification

- pytest -q tests: 245 passed, 1 warning
- git diff --check: passed
- readiness_status: blocked
- gpu_smoke_allowed: false
- blockers: semantic_success_claim_not_allowed
- runtime_motion_control_connected: true
- true_lane_geometry_replacement_available: true
- semantic_alignment_protocol_defined: true
- semantic_alignment_required_check_count: 9
- semantic_success_claim_allowed: false
- does_not_run_gpu: true
- does_not_generate_video: true

The warning is the known TensorFlow / NumPy np.bool8 deprecation warning and is not related to DriveLoop logic.

## What Changed In This Step

A candidate70-specific semantic/alignment protocol was added and wired into the readiness gate.

New protocol file:

- scripts/run_candidate70_semantic_alignment_protocol.py

New test file:

- tests/test_candidate70_semantic_alignment_protocol.py

Generated protocol artifact:

- outputs/driveloop/candidate70_semantic_alignment_protocol/candidate70_semantic_alignment_protocol.json

Generated report template:

- outputs/driveloop/candidate70_semantic_alignment_protocol/candidate70_manual_alignment_report_template.json

The protocol defines 9 required checks:

- artifact.video_available_and_decodable
- object_presence.motorcycle_or_scooter_visible
- object_consistency.target_actor_trackable_across_frames
- maneuver.cut_in_from_left_toward_ego_visible
- temporal_motion.lateral_displacement_visible
- spatial_relation.starts_left_or_adjacent_lane_and_moves_toward_ego_path
- road_context.night_urban_multilane_or_lane_markings_visible
- hdmap_alignment.lane_geometry_visually_consistent_with_scene
- control_binding.structural_evidence_referenced_without_overclaiming

## Claim Boundary

Allowed claims:

- Source-bound actor motion reaches DD2 runtime tensor surfaces.
- Local-map-vector HDMap lane geometry replacement reaches the DD2 grounding surface.
- Candidate70 semantic/alignment evaluation protocol is defined and wired into the readiness gate.
- The default gate has only semantic_success_claim_not_allowed remaining.

Not allowed claims:

- Do not claim GPU approval.
- Do not claim generated video semantic success.
- Do not claim lane-change/cut-in visual success.
- Do not claim physical trajectory or velocity/displacement tensor verification.
- Do not set semantic_success_claim_allowed to true without a measured_passed review.

## Next Required Step

If the user explicitly approves a short GPU smoke, generate only a candidate video first. Then run the post-GPU review gate and complete the semantic/alignment report. Only a measured_passed report may support a semantic-success claim.
