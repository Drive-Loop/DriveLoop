# 2026-07-10 DD2 fine-tune trainer shipped; trainval conversion in progress

Context: P1 from the 2026-07-10 handoff (stronger checkpoint / longer frames).
16-frame remains host-RAM infeasible on this machine; this session opens the
stronger-checkpoint branch: fine-tune DD2 on nuScenes trainval on the A10.

## Data
- Full trainval located on secondary disks: raw at
  /mnt/driveloop_full/raw/v1.0-trainval (850 scenes, samples 53G + sweeps 342G,
  maps with expansion), archives on /mnt/driveloop_data. Devkit loads clean;
  0/300 randomly sampled files missing.
- Conversion (cam_all, 12Hz) to /mnt/driveloop_full/processed/nuscenes with the
  stock converter; expected output ~220G (mini extrapolation: 2.6G / 10 scenes).

## Shipped (commit 6dfb8d8 + follow-up fix commit)
- DriveDreamer2_Trainer + DriveDreamer2TrainModule
  (dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_trainer.py):
  EDM training loss bit-matched to the inference parameterization
  (EulerDiscreteScheduler, v_prediction + continuous, sigma_data=1:
  c_in=1/sqrt(s^2+1), denoised=out*(-s/sqrt(s^2+1))+x_t/(s^2+1), t=0.25*ln s),
  sigma ~ LogNormal(pmean 1.0, pstd 1.6) env-gated; condition dropout 0.1
  mirrors the CFG negative branch (zeroed prompt + downsampler outputs, image
  condition kept). Freeze policy env-gated, defaults = temporal/time_mixer
  patterns + both downsamplers = 556.9M / 1622.5M elements (34.3%), fuser
  frozen to preserve C4-verified injection behavior. Per-checkpoint gligen
  export, strict drop-in format for load_weights.
- Configs: drivedreamer2_img_cond_mini_ft_smoke_local (1-epoch overfit smoke),
  drivedreamer2_img_cond_trainval_ft_local (1 epoch, ckpt every 10%, limit 3).
- tests/test_dd2_trainer_unit.py: 8 unit tests (EDM parameterization vs the
  scheduler formulas, panoramic reshape vs naive loop, freeze selection,
  export format + meta isolation).

## Fixes required en route (all reproduced then verified)
1. Installed diffusers ModelMixin.enable_gradient_checkpointing has a new
   callback signature incompatible with the vendored unet; fixed by setting
   block-level gradient_checkpointing flags directly (25 modules).
2. from_pretrained returns eval-mode modules and the base Trainer never calls
   train(); the vendored checkpointing branches are gated on self.training, so
   checkpointing silently no-oped. Fixed with model.train() + vae.eval().
3. Vendored TransformerSpatioTemporalModel checkpointed only the spatial block;
   temporal_block ran outside checkpoint, retaining exactly the trainable
   temporal activations (~14G). Patched all 5 byte-identical sites in
   transformer_temporal.py with a training-gated checkpoint branch (eval path
   unchanged; only the first class is instantiated by unet_3d_blocks).
4. accelerator.unwrap_model imports deepspeed, which is broken on py3.8
   (tuple[int,int] annotation); manual .module unwrap in the export path.

## Measured
- Memory diagnostic (fabricated batch, bypasses the ~19 min sampler init):
  static 4.10 GiB, forward peak 11.17 GiB, forward+backward peak 11.98 GiB on
  22.19 GiB A10; loss 0.3018 finite.
- Smoke (mini, 73 steps, 1 epoch): ~5.0 s/step, diff_loss 0.16-0.27 noisy
  without divergence (per-step sigma sampling dominates variance at this
  horizon), 3 gligen exports of 2.84G, checkpoint rolling works, Total_time
  7:42. Exported bin passes strict load_weights drop-in load.

## Ops findings
- Parallel converter + training OOM-killed the converter at 472/850 (labels
  stage, 3h20m in): accelerator.save_state has a multi-GiB host-RAM spike on
  top of the ~10G devkit residency. Jobs are now serialized; conversion
  restarted from scratch and owns the machine overnight.
- VideoSampler start-candidate resampling costs ~19 min per launch on mini and
  scales with records (~85x for trainval); mitigate before the trainval run
  (resample_num_workers, or cache the resample).

## Erratum
- The 2026-07-10 handoff states 433 tests green at e9ea593; measured base is
  432 at exactly that commit (440 with the new 8). Handoff count was off by one.

## Claim boundaries
- The smoke validates the training MECHANISM only (loss finite and stable,
  gradients flow to the intended subset, export format round-trips). No visual
  quality, no semantic, and no closed-loop claims from this session.
- Fine-tune quality claims must go through the evaluator protocol
  (yolov8x@0.20, baseline differential, tau per v9 open arm) plus human review,
  per standing conventions.

## Next
1. Conversion completes -> verify cam_all_train/v0.0.2 + cam_all_val/v0.0.2.
2. Trainval FT (1 epoch, ~21K steps, ~5 s/step -> ~29h wall; ckpt every 10%).
3. Evaluate FT checkpoints on the clean mini window and candidate70 arms at
   the evaluator level; human-review gate before any paper claim.
4. Re-run the synthetic-path three-point boundary scan under the FT checkpoint.
