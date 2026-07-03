# P0 candidate70 source-bound actor-motion identity fix

Date: 2026-07-03

## Purpose

Record the non-GPU P0 evidence that candidate70 source-bound actor motion now reaches the DriveDreamer-2 runtime tensor surface through per-frame `boxes3d` append with sample-identity matching.

This record is not a handoff file.

## Scope

This experiment covers only structural runtime conditioning evidence:

- source-bound DD2 sample selection
- relative actor-motion frame mapping to source-bound sample identities
- per-frame `boxes3d` append application
- regenerated `image_box` condition change
- candidate70 readiness gate blocker update for runtime/trajectory motion surface evidence

This experiment does not claim GPU video generation success, video semantic success, measured lane-change/cut-in success, true HDMap lane-geometry replacement, or velocity/displacement tensor control.

## Code changes under test

Modified files at verification time:

- `dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_tester.py`
- `driveloop/backends/drivedreamer2.py`
- `driveloop/dd2_override.py`
- `scripts/run_candidate70_gpu_readiness_gate.py`
- `tests/test_actor_motion_surface.py`
- `tests/test_candidate70_gpu_readiness_gate.py`
- `tests/test_dd2_override.py`

Key logic changes:

- Source-bound DD2 audit-only runs with `DRIVELOOP_DD2_SOURCE_BOUND=1` now use the targeted dataset subset even when `DRIVELOOP_DD2_BATCH_SKIP=0`.
- Backend maps relative actor-motion frames onto source-bound DD2 sample identities instead of relying on raw relative frame ids.
- DD2 override matching accepts sample-identity based per-frame entries, with old frame-index matching kept as fallback.
- Candidate70 GPU readiness gate now accepts the source-bound actor-motion audit as structural runtime motion evidence only.

## Source-bound actor-motion audit evidence

Audit path:

    outputs/driveloop/p0_candidate70_source_bound_actor_motion_after_identity_fix/run/p0_candidate70_source_bound_actor_motion_audit_only_after_identity_fix

Key runtime log marker:

    DRIVELOOP_DD2_BATCH_SKIP=0: use targeted dataset subset with 48 records

Previously, source-bound audit-only still used the first contiguous batch when batch skip was zero. This fix makes the audit use the selected source-bound subset.

Actor-motion frame mapping evidence:

    {
      "available": true,
      "mode": "source_bound_relative_step_to_sample_identity",
      "source_identity_count": 48,
      "input_per_frame_count": 4,
      "mapped_entry_count": 24,
      "unmapped_relative_frame_idx": []
    }

Override audit evidence:

    {
      "override_entry_count": 48,
      "override_changed_counts": {
        "boxes3d": 24,
        "image_box": 24,
        "scene_description": 48
      },
      "applied_per_frame_append_count": 24,
      "sample_identity_applied_count": 24
    }

Representative changed row showed:

- `boxes3d` changed from shape `[5, 9]` to `[6, 9]`
- `image_box` changed
- accepted entry carried `relative_frame_idx`, `sample_identity`, `source_record_index`, and `provenance: driveloop_actor_motion_surface`

## Candidate70 readiness gate evidence

Default gate after patch:

    {
      "readiness_status": "blocked",
      "gpu_smoke_allowed": false,
      "blockers": [
        "true_lane_geometry_replacement_not_available",
        "semantic_success_claim_not_allowed"
      ],
      "checks": {
        "runtime_surface_not_connected": false,
        "trajectory_surface_not_connected": false,
        "runtime_motion_control_connected": true,
        "source_bound_actor_motion_runtime_connected": true,
        "source_bound_actor_motion_sample_identity_verified": true,
        "source_bound_actor_motion_boxes3d_changed": true,
        "source_bound_actor_motion_image_box_changed": true,
        "true_lane_geometry_replacement_available": false,
        "semantic_success_claim_allowed": false
      }
    }

Interpretation:

- The previous motion/runtime blockers are addressed for this structural tensor-conditioning surface.
- The gate correctly remains blocked because HDMap true lane geometry replacement and semantic success are not yet proven.
- This does not authorize GPU execution by itself.

## Verification

Focused regression:

    38 passed in 0.15s

Full non-GPU test suite:

    234 passed, 1 warning in 7.11s

The warning was a TensorFlow / NumPy deprecation warning and was not related to DriveLoop logic.

## Claim boundary

Allowed claim:

Candidate70 source-bound actor motion is now connected to the DD2 runtime tensor surface via sample-identity matched per-frame `boxes3d` append, and this change is observed through `boxes3d` and `image_box` tensor-surface changes in audit-only execution.

Not allowed claim:

This is not GPU video evidence, not semantic success evidence, and not proof that the generated video performs the intended motorcycle cut-in. HDMap true lane-geometry replacement remains unavailable in the current gate.

## Remaining P0 work

1. Implement or verify true HDMap lane-geometry replacement, not only dry-run raster reaching the grounding downsampler.
2. Define and run measured semantic/alignment evaluation before claiming cut-in success.
3. Request explicit user approval before any GPU smoke run.
