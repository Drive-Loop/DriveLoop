# 2026-07-09 Tangent heading + real-track ego injection (post-C4)

## Shipped (after C4 end-surface verification)
1. Trajectory-tangent heading for synthetic ego entries
   (apply_trajectory_tangent_heading; disable via
   DRIVELOOP_EGO_TANGENT_HEADING=0; audit heading_mode). Replaces the
   plan's constant yaw with the tangent of the GLOBAL trajectory (ego
   motion + relative motion) per frame.
2. DD2 generation env overrides for sweeps:
   DRIVELOOP_DD2_NUM_INF_STEPS / DRIVELOOP_DD2_MIN_GUIDANCE /
   DRIVELOOP_DD2_MAX_GUIDANCE (not yet exercised on GPU).
3. Real-track ego injection mode (default within
   DRIVELOOP_EGO_INJECTION=1; disable via DRIVELOOP_EGO_REAL_TRACK=0):
   when the source-bound window already contains a real actor of the
   requested category, its per-frame cam_front annotation is lifted to
   the ego frame (binding instance_token preferred, then track
   continuity) and emitted on the per_frame_append_ego surface; the
   synthetic stand-in is suppressed. Real heading/dims preserved.

## Measured findings driving change 3
- The candidate70 window CONTAINS a real motorcycle performing a left
  cut-in (cam_front x -10.8 -> -0.9, z 24.4 -> 9.1 over the 8-frame
  window) - the reason this window was source-bound in the first place.
- The synthetic stand-in overlapped it: min center gap 3.74 m with
  crossing trajectories (probe over emitted entries vs record labels).
- Tangent heading on the synthetic plan pointed at the camera
  (cam yaw ~2.35 rad) because the ego is near-stationary in this scene:
  the synthetic plan assumes a moving ego; the heading fix faithfully
  exposed that scene mismatch rather than causing it.

## GPU replays (human review, single reviewer)
- Tangent-heading run (c4_tangent_heading_gpu): actor turns along the
  cut-in arc (constant-yaw slide fixed); scale grows small->large,
  consistent with approach; overlap with the real motorcycle visible.
- Real-track run (c4_real_track_gpu): single motorcycle following the
  real cut-in trajectory, no duplicate actor. Reviewer confirmed.

## Claim boundary
Human review is single-reviewer and gates nothing beyond mechanism
claims; no S_perc numbers; perception acceptance != semantic success.
The synthetic path remains UNVALIDATED in a clean window that lacks
the requested actor (its actual use case); the steps/guidance sweep
and v9 three arms (handoff step 4) remain open.
