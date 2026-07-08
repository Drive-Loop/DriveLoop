# 2026-07-08 Erratum: the 07-04 "48f" retry video is 8 frames; v9 lever redefined

## Measured evidence
- ffprobe nb_read_frames = 8 on the 2026-07-04 measured-passed retry
  video (candidate70_night_cut_in_gpu_retry_48f_20260704T142723Z).
- git log -S "frame_num = 48" across all history: zero hits. Every DD2
  config hardcodes frame_num = 8. No 48-frame generation has ever
  happened in this project.
- Archived GPU smoke command plan: config drivedreamer2_img_cond_mini_local
  (frame_num 8) + baseline dataset
  /mnt/driveloop_full/processed/nuscenes/v1.0-trainval/candidate70_source_bound/cam_all_train/v0.0.1.

## Corrections
- "48f" in the 2026-07-04 record refers to the source-bound
  window/override surface (48 rows), not video length. The manual
  review verdict itself stands (it reviewed the actual video), but all
  later citations of "48-frame generation" — including Section 6 of
  2026-07-08_tau_reanchoring_v8_and_no_escalation_arm.md and today's
  v9 plan — were based on this mislabel.
- Today's exp_v9 runs with --dd2-frame-num 48 were invalid twice over
  (48-frame source window feeding 8-frame generation); renamed to
  exp_v9_INVALID_win48_gen8_*. The dd2_frame_num plumb reaches only the
  source selector; generation length is config test.frame_num.

## v9 lever redefinition
- v9 = conditioning-dataset switch at 8 frames: mini val ->
  candidate70 source-bound trainval subset (capability configuration
  candidate70_sb_trainval_8f). This reproduces the only
  measured-passed configuration. tau re-derived from the v9 open arm.
- frame_num 8 -> 48 is an UNTESTED axis: requires a new committed
  config plus an end-surface frame-count check. Do not cite as proven.

## Process lessons
- Capability-lever verification must reach the end surface (ffprobe
  the video, not the plumbing). Backend should fail loudly when
  requested frame_num != config test.frame_num (guard TODO).
- Measured-passed artifacts must archive a reproducible config; the
  07-04 exact config state was never committed.
- Geometry side calibration was measured on mini val; re-verify both
  sides on the source-bound dataset before reading v9 arm numbers.
