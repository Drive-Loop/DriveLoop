# Candidate70 Converter Identity Subset Audit

Date: 2026-07-02

## Scope

This note records a non-GPU audit-only candidate70 label subset created from the current nuScenes converter identity path.

It does not rebuild full processed labels, does not change DD2 model inputs, does not run GPU, and does not claim prompt-to-video semantic success.

## Artifacts

- subset labels: outputs/driveloop/candidate70_converter_identity_probe/cam_front_8/v0.0.1/labels/data.pkl
- subset summary: outputs/driveloop/candidate70_converter_identity_probe/cam_front_8/v0.0.1/labels/summary.json
- actor track audit: outputs/driveloop/actor_track_surface_audit/candidate70_converter_identity_probe_actor_track_surface_audit.json

## Result

The converter-derived candidate70 subset contains 8 CAM_FRONT frames.

Summary:

- all_frames_have_instance_tokens: true
- all_frames_have_sample_annotation_tokens: true
- all_frames_have_target: true
- target raw instance token: 21cdc9f24c614a6197fd044379697197
- target category: vehicle.motorcycle

Actor track audit:

- status: per_frame_actor_tracks_observed
- actor_identity_available: true
- boxes_grouped_by_instance_token: true
- target motorcycle observation_count: 8
- target motorcycle frame_indices: 144, 147, 150, 153, 156, 159, 162, 165
- blockers: none

## Interpretation

The current converter path can create a small candidate70 label subset with raw nuScenes actor identity fields preserved end-to-end.

This confirms that the previous identity-patched subset can be replaced, for this candidate, by a converter-derived audit-only subset. The old processed labels still need a rebuild before identity fields are available generally.

## Claim Boundary

Allowed claims:

- Candidate70 converter-derived subset preserves raw actor identity fields.
- The target motorcycle can be grouped into an 8-frame track from converter-derived labels.
- Converter identity path is available for this candidate-level audit.

Disallowed claims:

- Full processed labels have been rebuilt.
- Runtime motion control is connected.
- Lane-change or cut-in control is verified.
- Trajectory, velocity, displacement, or HDMap lane geometry is consumed by DD2 runtime.
- Actor identity metadata proves generated video semantics.

## Recommended Status

- candidate70_converter_identity_subset_created: true
- candidate70_converter_identity_track_observed: true
- target_motorcycle_track_covers_all_8_frames: true
- full_processed_labels_rebuilt_with_identity: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Use this subset for future non-GPU metadata and readiness audits. Do not run GPU until a runtime-consumed motion or lane-geometry control surface is verified.
