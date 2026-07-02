# Candidate70 Lane Geometry / HDMap Compatibility Audit

Date: 2026-07-02

## Scope

This note records a non-GPU lane geometry and HDMap compatibility audit for candidate70.

It does not claim runtime motion control, lane-change control, HDMap lane geometry override, prompt-to-video semantic success, or paper-level success.

## Candidate

- candidate: candidate70
- source candidate id: nuscenes_train_candidate70_cam_front_9935
- scene: scene-1100
- map: singapore-hollandvillage
- target raw instance token: 21cdc9f24c614a6197fd044379697197
- category: vehicle.motorcycle
- prompt status: allowed only for the explicit night lane-change / cut-in suggested prompt; old daytime prompt remains blocked

## Inputs

The audit used existing non-GPU artifacts and raw nuScenes map metadata:

- candidate runtime metadata audit
- candidate70 identity-patched audit-only labels
- raw nuScenes v1.0-mini
- nuScenes map API for singapore-hollandvillage

The audit is read-only and does not modify source labels, raw nuScenes, DD2 model inputs, or generated videos.

## Motion Evidence

The target motorcycle / scooter moves strongly toward the ego/front camera region.

Global relative motion:

- target_global_delta_xy: [8.458, 13.501]
- ego_global_delta_xy: [-0.009, -0.003]
- target_minus_ego_start_xy: [-16.697, -17.289]
- target_minus_ego_end_xy: [-8.23, -3.785]

Processed camera-space motion:

- processed_cam_delta_xz: [9.92, -15.34]

Interpretation:

Candidate70 has strong left-to-front / approach motion support. It is stronger than candidate38 as source evidence.

## Lane / Connector Evidence

Ego map position:

- unique_ego_closest: cb962fb2-f68a-403a-86c2-ef47ecf24501:lane_connector
- ego_layer_lane: empty in all audited frames
- ego is consistently in or closest to a connector / stop-line intersection region

Target map position:

- first audited frames closest to lane: 560dea1d-3467-498a-8db1-0ba97f4a9672:lane
- later audited frames closest to lane connector: baa86582-8dbc-4e5d-a006-656eea789213:lane_connector
- unique_target_layer_lane: empty or 560dea1d-3467-498a-8db1-0ba97f4a9672

Overlap checks:

- any_same_closest_token: false
- any_same_layer_lane: false

Interpretation:

The target shows a lane-or-connector transition while moving from left/front-left toward the ego-front region. However, the target never shares the ego closest lane / connector token in the audited frames, and no same ego lane membership is verified.

This supports an intersection / connector cut-in or crossing-style candidate, but it does not verify a lane-change into the ego lane.

## Recommended Status

- candidate70_lane_geometry_compatibility: partial_intersection_connector_support_not_ego_lane_verified
- candidate70_left_to_front_motion_supported: true
- candidate70_target_lane_or_connector_transition_observed: true
- candidate70_same_ego_lane_or_connector_verified: false
- candidate70_lane_change_into_ego_lane_verified: false
- hdmap_lane_geometry_override_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Allowed Claims

- Candidate70 has strong source-level left-to-front motorcycle / scooter motion.
- Candidate70 target moves from a lane-associated map region into a different connector-associated region.
- Candidate70 is compatible with a cautious night intersection cut-in / crossing-style source description.
- Candidate70 is stronger than candidate38 for source-level motion and map/context compatibility.

## Disallowed Claims

- Candidate70 verifies a motorcycle lane-change into the ego lane.
- Candidate70 verifies same-lane or same-connector interaction with the ego vehicle.
- Candidate70 verifies lane-change or cut-in runtime control.
- Candidate70 verifies HDMap lane geometry override.
- Candidate70 proves trajectory, velocity, displacement, or lane geometry is consumed by DD2 runtime.
- Candidate70 proves prompt-to-video semantic success.
- Tensor, metadata, source visibility, map proximity, or generated video alone proves video semantics.

## Next Step

Record this as a partial result.

Before any GPU run, continue non-GPU work on runtime-consumed control surfaces:

1. Decide whether to preserve raw nuScenes instance and annotation tokens in converted labels with tests.
2. Investigate whether a model-facing trajectory, displacement, or lane geometry surface can be exposed and verified.
3. Keep generated videos, if any, framed as candidate videos until manual or perception-based semantic review passes.
