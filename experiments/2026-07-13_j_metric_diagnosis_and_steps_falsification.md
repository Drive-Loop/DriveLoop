# 2026-07-13 J diagnosis: differential survivors, not detector blindness

## Decomposition (from bank0 attempts.jsonl metrics)
J floor 0.2 = S_intent only. The single 0.560 attempt (ft closed m4,
seed 6668, 50 steps) decomposes to exactly one baseline-differential
target-class survivor: view1, 1 of 8 frames, conf 0.287 -> Q_conf
0.287, Q_cov 0.125, Q_track 0.125, S_ctrl 1.0. The detector is NOT
blind at night: 267-303 detections per video are matched to the
no-injection baseline and subtracted. The bottleneck is that the
injected/reinforced target almost never yields a NEW target-class
detection. "Detector-floor-limited" in earlier records should be read
as "differential-survivor-limited".

## 50-step falsification
Official weights, open arm (1 iter, seed 6666), NUM_INF_STEPS=50,
scored against a freshly generated 50-step no-injection baseline
(parameter-matched differential): all five cases 0.200. The m4 0.560
was seed luck, not inference steps. The generation-parameter lever
alone does not move J at matched seed.
Runs: outputs/driveloop/exp_v9_official_open_50steps; baseline
v9_no_injection_baseline_50steps.

## Lever queue after diagnosis
1. Real-track reinforcement magnitude: not yet implemented. The
   real-track surface reinforces existing actors as annotated
   (heading mode real_track_annotation); a dims/proximity scaling
   knob (env-gated, default off) must be built before it can be
   tested. Mechanism target: multi-frame target detections, since
   Q_cov and Q_track scale with support frames (currently 1/8 max).
2. Window/candidate selection: windows with a nearer/larger real
   target actor.
3. Checkpoint capability / frame_num 16 (strategic lever).
4. Best-of-N seeds: works today, is sampling; report as the loop's
   search contribution, separate from conditioning improvements.
5. Evaluator v10 (track/motion evidence in J, tau re-anchor):
   protocol change, full evaluator-integrity process required.

Claim boundary: diagnosis from bank0 artifacts plus one falsification
run; single window (candidate70); no perception or semantic claims.
