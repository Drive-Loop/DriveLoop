# 2026-07-10 Session handoff: C4 shipped + full day of loop/injection work

## State (all pushed; 433 tests green; ~30 commits since 216b7a3)
Read this file plus the 2026-07-09/10 records for full detail.

## Shipped today (all env-gated, defaults = best-known config)
1. C4 ego-frame injection surface (boxes3d.per_frame_append_ego,
   DRIVELOOP_EGO_INJECTION=1): one ego entry per frame, per-camera
   conversion via record calib, behind-camera + FOV culls
   (DRIVELOOP_EGO_FOV_CULL), end-surface verified (audit-only, GPU,
   human review). Ego math lives in driveloop/ego_injection.py.
2. Real-track mode (DRIVELOOP_EGO_REAL_TRACK, default on): windows
   already containing the requested actor reinforce the REAL track;
   synthetic stand-in suppressed (measured overlap 3.7 m otherwise).
3. Trajectory-tangent heading for synthetic entries
   (DRIVELOOP_EGO_TANGENT_HEADING); far-entry profile
   (DRIVELOOP_EGO_FAR_ENTRY, numeric = frame-0 longitudinal offset).
4. Closed-loop generation lever: per-attempt seed offset
   (+DRIVELOOP_DD2_SEED_BANK for run repeats), refiner
   generation-parameter escalation (steps 50 single rung; guidance
   rung removed - see erratum), DD2 tester env overrides
   (NUM_INF_STEPS / MIN_GUIDANCE / MAX_GUIDANCE / SEED_OFFSET).
5. Evaluator GPU release after each evaluation (fixes CUDA OOM from
   detector-held 1.5 GiB).

## Key measured findings (records dated 2026-07-09/10)
- v9 three arms at tau 0.45 (yolov8x@0.20, baseline differential):
  without the generation lever, closed == open bit-identically
  (levers disconnected); with it, closed weakly dominates open,
  uplift in 2 of 3 seed banks, m4 floor->0.578 acceptance is
  seed-controlled attributable to steps-50 (matched-seed ablation)
  and human-verified, but its perception support is thin (1 frame;
  J carried by control/intent/utility terms).
- Synthetic path at mini config is bounded: near start pops in
  (img_cond frame-0 anchor, confirmed by wo_img intervention), far
  start loses actor class; img_cond near profile is the optimum.
- 16-frame config is host-RAM infeasible (28 GiB host, OOM killer).
- Detector upgrade (YOLO-World) evaluated and REJECTED at the
  evaluator level; full-frame probes are a resolution artifact.

## Next queue (in rough priority)
1. Stronger checkpoint / longer frames: needs bigger host+GPU or
   DD2 fine-tuning on trainval (days on A10). The only remaining
   lever for synthetic-path visual quality.
2. First-frame condition editing research (kills pop-in in img_cond).
3. More seed banks / more cases for tighter arm comparisons; consider
   windows beyond candidate70.
4. Paper writing: the loop-mechanism story (lever wiring, matched-seed
   attribution, weak dominance) and limitations (checkpoint ceiling,
   detector sensitivity, thin perception support at tau) are fully
   evidenced in the records.

## Conventions (unchanged)
No Chinese in code; anchored /tmp patches (abort if anchor not
unique); full pytest before commit; English commit messages; push per
milestone; perception acceptance != semantic success; human spot
checks gate paper claims; detector claims only at evaluator level.
