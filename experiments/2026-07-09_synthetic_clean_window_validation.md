# 2026-07-09 Synthetic-path clean-window validation (3 findings)

Window: mini val scene 325cef68 frames 96-117 (moto-free span 94-239),
sample_token 8092909473464f80b9f791a4d31ddcb8. Audit-only first
confirmed the real-track fallback chain: mode
ego_frame_one_entry_per_video_frame, fallback reason
no_real_track_boxes_for_category, tangent heading, front cams 8/8
accepted, rear cams 8/8 behind_camera_culled, per-frame trajectory.
An earlier window pick (batch 12, frames 72-93) landed on moto-bearing
frames and correctly engaged real-track mode with the 88-92 gap
skipped - selection works; the pick was ours.

## Finding 1: overlap-view junk conditioning (fixed, commit 00d5743)
GPU run 1 (night prompt): human review saw the motorcycle teleporting
between composite tiles. Cause: the actor at ~10 deg bearing also fell
into cam_front_left's FOV edge, where its CENTER projects outside the
image - the canvas received only clipped corner fragments. Fix: FOV
cull at consumption (center outside image + 10 percent margin ->
center_outside_image_culled; DRIVELOOP_EGO_FOV_CULL=0 for A/B).
Post-fix audit: cam_front accepted 8/8, front_left/right culled.

## Finding 2: prompt style leaks onto mismatched sources
The reused candidate70 night prompt re-lit the daytime parking-lot
window to night (canned-prompt scene_description replacement working
as designed). Validation runs must match prompt style to the source
window; v3 used a daytime prompt and lighting was consistent.

## Finding 3 (open): img_cond first-frame anchor makes synthetic
actors pop into existence
v3 human review: lighting consistent, single-tile rendering, correct
left cut-in trajectory - but the motorcycle appears suddenly in a
parking spot that was visibly empty moments earlier. Structural cause:
img_cond anchors frame 0 to the REAL source image, which contains no
motorcycle in a clean window; the injected conditioning only takes
effect afterwards. Real-track mode is immune (the actor exists in
frame 0). Mitigation directions for the synthetic path: far-start
trajectories that enter the FOV during the clip (subpixel at frame 0),
or first-frame condition editing (out of scope for now).

## Claim boundary
Mechanism-level validation of the synthetic path: emission, fallback,
per-view projection, culling, and per-frame motion verified on a clean
window; visual insertion quality is limited by the img_cond anchor
(finding 3) and the mini checkpoint. No perception scores run (the v9
baseline video belongs to the candidate70 window). Single reviewer.

## Finding 3 follow-up: far-entry trades pop-in for small-actor failure
Far-entry profile (commit with DRIVELOOP_EGO_FAR_ENTRY, start ~55 m):
human review of v4 shows the motorcycle class is lost - a person-like
figure grows in place from small to large. Consistent with the
2026-07-08 regression record (person-like blob at weak conditioning):
at ~55 m the actor spans tens of pixels and the mini checkpoint cannot
render it class-correctly; scale-growth-in-place is the correct
geometry of an along-axis approach. Synthetic-path appearance is
therefore bounded on both ends: near start pops into existence
(img_cond frame-0 anchor), far start fails class rendering. Trajectory
design moves between failure modes; the binding constraints are
checkpoint capability and the first-frame anchor. This closes the
synthetic-path exploration at the mini config; next levers are the
stronger checkpoint / longer frame_num, or first-frame condition
editing.
