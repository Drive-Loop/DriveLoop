# 2026-07-13 v9-protocol three arms under trainval FT step_6322 (bank0)

Protocol: v9 evaluator (yolov8x@0.20, per-window no-injection baseline
differential, task utility on, tau 0.45 applied at the record level),
candidate70 window via source binding (source_candidate_id candidate70,
instance_token 21cdc9f24c614a6197fd044379697197, converter identity
probe summary), cases m1-m5 from experiments/manifests/v9_cases.json,
seed bank0. Per-weight baselines: the FT arms score against a freshly
generated FT no-injection baseline (v9_no_injection_baseline_ft6322,
same prompt and selector as the official baseline, ego injection
disabled, verified enabled=false); the official anchor scores against
the stored official baseline. Mixing baselines across weights would
fold the FT rendering shift into the injection uplift, so each arm
uses its own checkpoint's baseline.

Arms: FT open (1 iter), FT closed (3 iters), FT no-escalation (3 iters,
--no-refiner-escalation), plus a same-day official-weights open anchor.
Post-v9 closed-loop levers are active and visible in the logs:
per-attempt reseed (SEED_OFFSET 0/1/2) in both 3-iter arms, and refiner
escalation driving DRIVELOOP_DD2_NUM_INF_STEPS=50 on closed attempts
2-3 only.

## Best J per case
case | official open | ft open | ft closed | ft no-esc | v9 archive (ref)
m1   | 0.200 | 0.200 | 0.200 | 0.422 | 0.200
m2   | 0.200 | 0.200 | 0.552 | 0.532 | 0.546
m3   | 0.200 | 0.200 | 0.200 | 0.422 | 0.407
m4   | 0.200 | 0.200 | 0.560 | 0.560 | 0.200
m5   | 0.200 | 0.200 | 0.411 | 0.200 | 0.200
mean | 0.200 | 0.200 | 0.385 | 0.427 | 0.310
tau-0.45 acceptances: 0 / 0 / 2 (m2, m4) / 2 (m2, m4) / 1 (m2).

## Findings
1. No FT uplift at matched seed: FT open equals the official open
   anchor at the 0.2 detector floor on all five cases. The 1-epoch
   trainval FT checkpoint does not move the evaluator metric on this
   benchmark.
2. Seed variance dominates: within FT, best-of-3 reseeding lifts 2-3
   cases per arm by 0.2-0.36 J. Closed (with inf-steps escalation) vs
   no-escalation means (0.385 vs 0.427) differ by less than case-level
   seed swings; n=5, no ordering claim.
3. The same-day official anchor does NOT reproduce the archived v9
   open numbers (m2 0.546 / m3 0.407 there; all 0.200 today).
   Cross-period comparability is broken somewhere in the post-v9
   commits (the sampler resample rewrite is the prime suspect;
   unproven). Archived v9 numbers are demoted to reference-only;
   same-day anchors are mandatory for any cross-checkpoint claim.

## Reading for the second-epoch decision
Combined with the same-night far-entry human-review verdict (FT does
not fix far-distance class fidelity), there is no evaluator-level or
review-level evidence that a second epoch of the same FT recipe buys
anything on these axes. The binding lever remains checkpoint
capability / longer frame_num; the closed loop's working levers are
seed resampling and inference-step escalation (best-of-N effects, not
conditioning improvements).

Runs: outputs/driveloop/exp_v9_ft6322_{open_loop,closed_loop,
no_escalation}_bank0, exp_v9_official_open_anchor_rerun; FT baseline
at outputs/driveloop/v9_no_injection_baseline_ft6322.

Claim boundary: single window (candidate70), five cases, bank0 seeds
only; night cases are detector-floor-limited; no perception or
semantic success claims; "failed" in the summaries refers to the 0.8
runner target, not tau.
