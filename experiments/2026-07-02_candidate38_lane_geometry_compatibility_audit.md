# Candidate38 Lane Geometry Compatibility Audit

Date: 2026-07-02

## Scope

This note records a non-GPU lane geometry compatibility audit for candidate38.

It does not claim lane-change control, HDMap lane geometry override, runtime motion control, prompt-to-video semantic success, or paper-level success.

## Candidate

- candidate: candidate38
- scene: scene-0796
- map: singapore-queenstown
- target accepted prompt: motorcycle visible lane-change from the left into the ego lane

## Positive Evidence

Candidate38 contains a visible motorcycle/scooter source actor in CAM_FRONT frames.

Raw nuScenes recovery verified the same target actor across frames:

- instance_token: d0d878e38f744577ad7c91edd001da08
- category: vehicle.motorcycle

This supports:

- motorcycle identity verified in source material
- target actor can be recovered from raw nuScenes metadata
- source candidate has motorcycle visibility evidence

## Motion Evidence

Processed CAM_FRONT target centers showed:

- processed_total_delta_x_m: -0.8441
- processed_total_delta_z_m: -17.7843

Interpretation:

The target actor mostly approaches the ego camera with only small lateral movement. This is not sufficient evidence for a visible lane-change into the ego lane.

## Lane Geometry Evidence

Closest-lane and polygon audits showed:

- target closest lane / connector token changes are observable
- ego and target are not in the same lane token in any audited frame
- target is only inside checked lane_connector polygons at frame 48
- target has no containing checked map polygon for frames 51, 54, 57, 60, 63, 66, and 69
- ego is in a complex intersection / connector region for later frames

Interpretation:

The token changes appear compatible with intersection / connector topology. They do not prove that the motorcycle changes from the left adjacent lane into the ego lane.

## Runtime Surface Evidence

Existing candidate38 DD2 audits show:

- prompt changed: true
- boxes3d changed: true
- image_box changed: true
- image_hdmap override changed: false
- trajectory tensor observed: false
- velocity or displacement consumed by runtime: false

This means candidate38 did not establish a runtime lane-change control surface.

## Recommended Status

- candidate38_motorcycle_identity_verified: true
- candidate38_lane_geometry_compatibility: weak_not_sufficient
- lane_change_source_support_verified: false
- hdmap_lane_geometry_override_verified: false
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Claim Boundary

Allowed claims:

- Candidate38 contains source motorcycle visibility evidence.
- The same raw nuScenes motorcycle instance can be recovered across audited frames.
- Candidate38 has weak lane/map proximity signals around an intersection or connector region.

Disallowed claims:

- Candidate38 verifies a motorcycle lane-change into the ego lane.
- Candidate38 verifies lane-change source support.
- Candidate38 verifies HDMap lane geometry override.
- Candidate38 verifies runtime motion control.
- Candidate38 video generation proves semantic success.
- Tensor or metadata changes prove video semantics.

## Next Step

Record this as a partial / negative result and search or audit a stronger candidate with clear target actor lane crossing, map containment evidence, and runtime-consumed motion or HDMap control evidence before any new GPU run.
