# Per-Frame Boxes3D Transform Surface Audit

Date: 2026-07-03

## Summary

This audit verifies that DriveLoop / DriveDreamer-2 per-frame `boxes3d.per_frame_append` overrides can reach the DD2 transform path and alter frame-specific box conditioning tensors.

This is CPU-only / transform-only evidence. It does not claim GPU generation quality, temporal motion control, lane-change success, cut-in success, or semantic video success.

## Command Scope

- No GPU generation was run.
- The command used `CUDA_VISIBLE_DEVICES=""`.
- The command used the DD2 mini local test dataloader and transform path.
- The override was passed through `DRIVELOOP_DD2_OVERRIDE_JSON` as a JSON string.
- The audit path was `/tmp/driveloop_per_frame_override_probe.jsonl`.

## Verified Result

Baseline and override signatures were compared for the first four contiguous frames.

### Targeted Frames

Frame `0`:

- `targeted_frame`: `true`
- `box_downsampler_changed`: `true`
- baseline `box_sha256`: `72dcf586b1fe67ce913d0429d9f0f37fc058d8d60c7761675393f933c7b9035b`
- override `box_sha256`: `c77eb99222a677a5310887b803c8137228dd585c064bb72cdf9dacba8898f328`
- audit changed:
  - `boxes3d`: `true`
  - `image_box`: `true`
  - `image_hdmap`: `false`
  - `scene_description`: `false`
- boxes3d shape changed from `[14, 9]` to `[15, 9]`

Frame `2`:

- `targeted_frame`: `true`
- `box_downsampler_changed`: `true`
- baseline `box_sha256`: `a0900ce9038357c89eec74d86b785f93493abbf5f0127c08f8f78c03dea1ba51`
- override `box_sha256`: `ba325a4ccd51f8b8ea4118957d0eff403716d6e4fa2c863db8f2a58e7ce0c717`
- audit changed:
  - `boxes3d`: `true`
  - `image_box`: `true`
  - `image_hdmap`: `false`
  - `scene_description`: `false`
- boxes3d shape changed from `[20, 9]` to `[21, 9]`

### Non-Targeted Frames

Frame `1`:

- `targeted_frame`: `false`
- `box_downsampler_changed`: `false`
- audit reason: `no_matching_frame_idx`

Frame `3`:

- `targeted_frame`: `false`
- `box_downsampler_changed`: `false`
- audit reason: `no_matching_frame_idx`

## Audit File Evidence

- `override_audit.entry_count`: `4`
- Target frames recorded `mode: per_frame_append`
- Target frames recorded `accepted_count: 1`
- Non-target frames recorded `reason: no_matching_frame_idx`
- `image_hdmap` stayed unchanged because this probe only tested per-frame boxes3d conditioning.

## Claim Boundary

Allowed:

- Per-frame boxes3d override can be selected by `frame_idx`.
- Selected per-frame boxes3d override reaches DD2 transform.
- Selected per-frame boxes3d override changes `image_box_canvas`.
- Selected per-frame boxes3d override changes `box_downsampler_input`.

Not allowed:

- Do not claim actor trajectory control.
- Do not claim velocity-conditioned generation.
- Do not claim lane-change or cut-in temporal control.
- Do not claim true lane geometry replacement.
- Do not claim GPU video semantic success from this audit.
- Do not mark P0 complete from this evidence alone.

## P0 Interpretation

This resolves part of the structural conditioning surface question for frame-specific boxes3d/image_box control.

P0 remains incomplete because actor-level trajectory, velocity, displacement, or lane-change runtime motion control is still not verified.
