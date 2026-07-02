# Converter Identity Path Probe

Date: 2026-07-02

## Scope

This note records a non-GPU probe of the nuScenes converter actor identity path.

It does not rebuild processed labels, does not change DD2 model inputs, and does not claim runtime motion control or prompt-to-video semantic success.

## Result

Focused tests passed:

- tests/test_nuscenes_converter_actor_identity_schema.py
- tests/test_actor_track_surface_audit.py
- tests/test_dd2_motion_metadata_transform_unit.py

Observed result:

- 5 passed, 1 warning

A direct `_get_cam_label` probe on candidate70 CAM_FRONT token `03216170f7ff4849991a8ab534c40520` returned:

- box_count: 3
- has_sample_annotation_tokens: true
- has_instance_tokens: true
- target_present: true
- target instance token: 21cdc9f24c614a6197fd044379697197
- target sample annotation token: 44ca9bba35694c59981e34a82b70b848

## Interpretation

The current converter code path can preserve raw nuScenes actor identity fields for camera labels.

The earlier candidate70 runtime metadata audit found `processed_identity_fields_present_any: false` because the current processed labels were produced before identity fields were present, or otherwise need to be rebuilt. This is a processed-data freshness issue, not evidence that the converter code path cannot emit identity fields.

## Claim Boundary

Allowed claims:

- Converter `_get_cam_label` can emit `instance_tokens` and `sample_annotation_tokens`.
- Candidate70 target actor identity is recoverable through the current converter code path.
- Current processed labels may need to be rebuilt before identity fields are available without audit-only patching.

Disallowed claims:

- Rebuilt full processed labels have been verified.
- Runtime motion control is connected.
- Trajectory, velocity, displacement, or lane geometry is consumed by DD2 runtime.
- Actor identity metadata proves generated video semantics.
- Prompt-to-video semantic success is verified.

## Recommended Status

- converter_identity_path_available: true
- candidate70_target_identity_available_from_converter_probe: true
- processed_labels_need_identity_rebuild: true
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Do not rebuild full trainval and do not run GPU yet.

A safe next step is to create a tiny converter-derived candidate70 label subset using the current converter path, then run actor track and motion metadata audits on that subset. This would verify the identity path end-to-end without full dataset conversion.
