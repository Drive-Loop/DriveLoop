# DD2 Structural Override Audit - 2026-06-28

## Purpose

This audit validates the paper Chapter 3 implementation path:

`prompt -> scene_specification -> executable_condition -> DD2 text condition + DD2 structural condition`.

This is an audit-only experiment. It does not claim final video semantic alignment and does not run diffusion inference.

## Main Claims Supported

1. DriveLoop grounding produces `scene_specification` and `executable_condition` from prompt.
2. `executable_condition` is converted into `DRIVELOOP_DD2_OVERRIDE_JSON`.
3. The official backend path applies the override inside `DriveDreamer2_Transform`.
4. DD2 `boxes3d`, derived `image_box`, and final `box_downsampler_input` change.
5. Baseline `input_image/img_cond` and `image_hdmap/grounding_downsampler_input` remain fixed unless an explicit verified HDMap source is provided.

## Evidence A - Transform-Level Structural Audit

Artifact: `outputs/driveloop/dd2_structural_audit/paper_ch3_barrier_structural_audit_rerun.json`

```json
{
  "box_downsampler_input_changed": true,
  "grounding_downsampler_input_changed": false,
  "input_image_changed": false,
  "interpretation": "DriveLoop executable_condition changed DD2 box structural conditioning while keeping baseline image and HDMap fixed."
}
```

Interpretation: the DD2 box structural branch changes while baseline image and HDMap inputs stay fixed.

## Evidence B - Official Backend Audit-Only Path

Artifact: `outputs/driveloop/dd2_backend_audit_only/paper_ch3_backend_audit_only_counts_fixed/backend_audit_only_summary.json`

```json
{
  "dd2_audit_only": true,
  "video_generated": false,
  "runtime_box_downsampler_input": {
    "available": true,
    "shape": [
      8,
      19,
      256,
      2688
    ],
    "sum": -103891048.0,
    "mean": -0.9932653903961182,
    "std": 0.10713879019021988
  },
  "override_changed_counts": {
    "boxes3d": 48,
    "image_box": 48,
    "scene_description": 48
  },
  "paper_stage_3_status": "tensor_control_ready"
}
```

Interpretation: the official `DriveDreamer2Backend -> launch.py -> DriveDreamer2_Tester -> DriveDreamer2_Transform` path applies the structural override without generating video.

## Evidence C - Two-Prompt Controlled Comparison

Artifact: `outputs/driveloop/dd2_backend_audit_compare/backend_audit_compare_summary.json`

Prompt A: `rainy night road with a traffic barrier blocking the lane`

Prompt B: `foggy night road with a bicycle cutting in from the left`

```json
{
  "audit_only": {
    "a": true,
    "b": true
  },
  "video_generated": {
    "a": false,
    "b": false
  },
  "runtime_tensor_hash_changed": {
    "prompt_embed": true,
    "box_downsampler_input": true,
    "grounding_downsampler_input": false,
    "img_cond": false
  },
  "override_changed_counts": {
    "a": {
      "boxes3d": 48,
      "image_box": 48,
      "scene_description": 48
    },
    "b": {
      "boxes3d": 48,
      "image_box": 48,
      "scene_description": 48
    }
  }
}
```

Expected controlled behavior:

- `prompt_embed` changes: `True`
- `box_downsampler_input` changes: `True`
- `grounding_downsampler_input` stays fixed: `True`
- `img_cond` stays fixed: `True`

## Current Limitations

1. This validates structural conditioning, not final video semantic correctness.
2. `image_hdmap` is intentionally kept from the mini dataset baseline because no verified HDMap override source is implemented yet.
3. Trajectory and temporal actor motion are not yet implemented as verified tensor controls.
4. Box placement uses an audited draft policy and should not be described as geometrically complete scene synthesis.
5. Full open-ended prompt-to-video generation is not established by this audit.

## Next Step

Run one short GPU smoke only after this audit is committed or otherwise preserved. The GPU smoke should be framed as qualitative output inspection plus audit artifact collection, not as the main experiment.

<!-- MOTORCYCLE_FIX_2026_06_28 -->

## Motorcycle Structural Override Fix

Recorded at: 2026-06-28T15:53:04.231663Z

### Root Cause

The previous six-prompt GPU smoke run produced valid videos, but pedestrian_rain_crossing_front and motorcycle_day_left_lane_change shared the same box_downsampler_input hash. Root-cause audit showed that the motorcycle prompt reached actors_to_synthesize, but draft_boxes3d was empty because motorcycle was missing from the audited class_default_dimensions table.

### Code Fix

Added an audited motorcycle default box template.

JSON:

{
  "category": "motorcycle",
  "box3d": [
    8.0,
    1.8,
    18.0,
    0.8,
    1.5,
    2.2,
    0.0,
    0.0,
    -0.25
  ],
  "placement_policy": "front_adjacent_lane_cut_in",
  "source": "class_default_dimensions"
}

This is still a draft geometry policy and must be reported as such. It is not a learned or dataset-retrieved 3D placement model.

### Audit-Only Verification

Audit-only compare report:

outputs/driveloop/motorcycle_fix_audit_only/backend_audit_compare_summary.json

Summary:

{
  "runtime_tensor_hash_changed": {
    "prompt_embed": true,
    "box_downsampler_input": true,
    "grounding_downsampler_input": false,
    "img_cond": false
  },
  "override_changed_counts": {
    "a": {
      "scene_description": 96
    },
    "b": {
      "boxes3d": 96,
      "image_box": 96,
      "scene_description": 96
    }
  },
  "paper_interpretation": "Different prompts changed DD2 text embedding and box structural conditioning while fixed mini baseline image and HDMap inputs stayed unchanged."
}

### GPU Smoke Verification

GPU smoke run:

/data/projects/DriveLoop/DriveDreamer2/outputs/driveloop/motorcycle_fix_gpu_smoke/20260628T035627Z_motorcycle_fix_gpu_smoke

Video:

/data/projects/DriveLoop/DriveDreamer2/outputs/driveloop/motorcycle_fix_gpu_smoke/20260628T035627Z_motorcycle_fix_gpu_smoke/motorcycle_day_left_lane_change/iteration_00.mp4

Summary:

{
  "video": {
    "path": "/data/projects/DriveLoop/DriveDreamer2/outputs/driveloop/motorcycle_fix_gpu_smoke/20260628T035627Z_motorcycle_fix_gpu_smoke/motorcycle_day_left_lane_change/iteration_00.mp4",
    "exists": true,
    "bytes": 1171354,
    "sha256": "c628456da553b7e1c147b250af8f6ecdd02dc84e2743dc2f02c34a785d18f8eb",
    "frame_count": 8,
    "fps": 4.0,
    "width": 2688,
    "height": 784,
    "contact_sheet": "/data/projects/DriveLoop/DriveDreamer2/outputs/driveloop/motorcycle_fix_gpu_smoke/20260628T035627Z_motorcycle_fix_gpu_smoke/frame_check/motorcycle_fix_contact_sheet.jpg"
  },
  "box_downsampler_sha256": "8d9f8e79977dfd2f6639502ec0962088d4d932f4492ab53e7a4a5baa1af3516b",
  "prompt_embed_sha256": "10e283c0ebfba15539c1b77394cf9e2045c35bdde2da52bbdb0128bb484635dc",
  "paper_stage_3_status": "tensor_control_ready",
  "override_changed_counts": {
    "boxes3d": 2916,
    "image_box": 2916,
    "scene_description": 2916
  }
}

### Interpretation

This verifies that DriveLoop can route a grounded motorcycle executable condition into DriveDreamer-2 boxes3d and derived image_box structural conditioning, and generate a DD2 video with the tensor override active.

This does not yet prove semantic visual correctness of the generated video. The next required research step is visual/perception-based prompt-video alignment evaluation.

