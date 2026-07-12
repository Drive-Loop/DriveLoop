# 2026-07-12 Trainval FT run: execution, OOM pathology, weight-effect evidence

Compiled from the 2026-07-11/12 session handoff notes; figures as recorded
during that session. Code state at write time: main at 65ffa42, all pushed;
full suite 447 passed.

## Run
Config drivedreamer2_img_cond_trainval_ft_local: 1 epoch = 6322 steps,
about 12.5 h on the A10-22G / 28G-host box. diff_loss held in 0.16-0.27
with no divergence. Surviving checkpoints
checkpoint_epoch_1_step_{5688,6320,6322} under
/data/projects/DriveLoop/exp/drivedreamer2_img_cond_trainval_ft_local/models/,
each with a per-checkpoint gligen export (pytorch_gligen_weights.bin),
injectable via DRIVELOOP_DD2_WEIGHT_PATH.
Lesson: checkpoint_total_limit=3 silently deleted every earlier
checkpoint; raise the limit before a second epoch.

## Data
Trainval LMDB complete:
/mnt/driveloop_full/processed/nuscenes/v1.0-trainval/cam_all_{train,val}/v0.0.2,
train 975256 / val 208534 records. Sampler resample cache enabled via
DRIVELOOP_SAMPLER_CACHE_DIR=/data/projects/DriveLoop/exp/sampler_cache.

## OOM pathology (six host-RAM kills)
- LMDB writer held one long write txn across the conversion; fixed with
  periodic commits (e8dc5ed).
- Fork copy-on-write blowups (three separate kills): forked children
  duplicating the parent's resident pages; mitigated by capping fork
  workers at 1 and single-process sampler resample (9038445).
- accelerate save_state resident peak at checkpoint save (one kill).
- STEP2 label-adjust worker pool too large for the host (one kill);
  worker count made env-configurable (6ecd8a7).
Operating rule on this host: fork workers <= 1.

## Parallel hdmap conversion
Serial converter projected about 73 h for trainval hdmaps; the parallel
converter finished in about 2 h and was byte-level verified against the
serial path before adoption (498c29a). Converter skip gates extended to
images/hdmaps; LmdbWriter.write_image_bytes added.

## Weight-effect evidence (no perception or semantic claims)
- FT safety: clean window batch13 seed6666, three arms (released /
  step_5688 / step_6322) visually indistinguishable at normal playback.
  Caveat: reviewed before the frame-stepping protocol adopted on
  2026-07-13; small-actor differences would not have been caught.
- Weights load and only alter temporal behavior: arm1 vs arm3 per-frame
  pixel diff rises monotonically 1.0 -> 8.38 over the 8 frames, first
  frame near zero (img_cond anchor).
- Videos at /data/projects/DriveLoop/outputs/ft_eval/ (produced via the
  direct tester path; there is no runner history.jsonl for them).

## Errata
- outputs/ft_eval lives at /data/projects/DriveLoop/outputs/ft_eval, not
  repo-relative outputs/ft_eval.
- FT checkpoint directories are named checkpoint_epoch_1_step_*, not
  step_*.
- An earlier handoff cited 433 passing tests; the correct count at that
  point was 432 (447 after the FT-era commits).
- mini_local weight_path env-gating (DRIVELOOP_DD2_WEIGHT_PATH) was an
  uncommitted working-tree edit during the FT session; committed as
  65ffa42.
