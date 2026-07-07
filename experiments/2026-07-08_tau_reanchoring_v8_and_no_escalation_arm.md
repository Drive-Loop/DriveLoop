# 2026-07-08 Tau re-anchoring on v8; "saturated" arm is actually no-escalation

Tool: driveloop/tau_reanchoring.py + scripts/run_tau_reanchoring_analysis.py
(commit "Add transparent tau re-anchoring tool"). Manifest:
experiments/manifests/tau_reanchoring_v8.json. All numbers below are
measured on exp_v8_{open_loop,closed_loop,closed_loop_r2,closed_loop_saturated}.

## 1. Tau re-anchoring (rule fixed before seeing data)

Anchor = open-loop per-case best-J distribution; primary rule mean + 1 std.
- open_loop: n=5, mean 0.412445, std 0.195407, max 0.580806
- proposed tau = 0.607852 (0.05 grid: 0.6); old tau 0.7 confirmed as
  inflation-era artifact (clean distribution shifted down as predicted).
- Sensitivity: excluding m4 (structurally floored, no injection path)
  gives mean 0.465556, std 0.179186, mean+1std 0.644742 (grid 0.65).
  Primary rule stays the all-cases version (pre-registered; the m4
  exclusion is reported for sensitivity only, not selected post hoc).
- NO candidate tau separates closed arms from open beyond 1 case at
  n=5 (0.607852: 1/5 vs 0/5; p75 0.565425: 2/5 vs 2/5). Threshold
  recalibration cannot rescue the v8 comparison; the capability lever
  (v9, 48 frames) is the path. tau_v8 = 0.6 (grid) is recorded for
  bookkeeping; any closed-vs-open claim requires fresh runs at a
  frozen tau.

## 2. Finding: --no-refiner-escalation does not saturate the refiner

The flag disables the escalation ladder and source rebinding, but the
refiner still injects `perception_feedback` into request.condition
(schema driveloop_perception_feedback.v0: diagnosis_reasons,
failed_checks, requested_visual_constraints, suggested_actions,
control_level=text_and_condition_feedback). Verified on
exp_v8_closed_loop_saturated/m5: attempt conditions differ ONLY in
perception_feedback (non-pf keys byte-identical across attempts).

Consequence: the v8 "closed_loop_saturated" arm must be read as
"closed_loop_no_escalation" (feedback conditioning active, ladder
off). It is NOT a retry-without-feedback control. The
2026-07-08_v8_honest_baseline.md arm labels are superseded by this
record. TODO: re-audit v7 attempt requests for perception_feedback
presence before citing "saturated == open" again.

## 3. Determinism and feedback-content mechanism evidence

- First attempts are deterministic: attempt-1 J in the no-escalation
  arm equals open-loop J bit-for-bit on all five cases (0.580806,
  0.565425, 0.515992, 0.2, 0.2).
- m5_low_visibility_cut_in: attempt 1 (condition {}) J=0.2; attempt 2
  (only perception_feedback added, prompt unchanged) J=0.571543;
  attempt 3 identical request content -> identical J. Deterministic
  recovery caused by feedback content alone.
- Insensitivity note: pf details differ between attempts 2 and 3
  requests (diagnosis evolved) yet J is unchanged; the effective
  signal is currently pf presence, not its fine content.

## 4. Corrected arm decomposition (8-frame capability config)

- closed vs no-escalation: ~0 (escalation ladder adds nothing at 8f;
  consistent with v8 baseline conclusion).
- no-escalation vs open: +0.097 mean, m5 recovered 0.2 -> 0.571543
  (feedback conditioning + retry budget).
- retry-only control arm is unnecessary: generation is deterministic,
  identical request implies identical J (proven by attempt-1
  equality), so retry-without-feedback == open by construction.

## 5. Claim boundaries

- Perception acceptance != semantic success; the m5 recovery is
  metric-level evidence and requires manual video spot check before
  any paper claim. Direction consistency necessary, not sufficient.
- Tau re-anchoring is threshold bookkeeping, not semantic success.
- n=5 per arm; all deltas above are single-config, single-run.

## 6. Next (v9)

- Lever: frame_num 8 -> 48 (--dd2-frame-num 48, plumbed and tested).
  Motivation incl. 2026-07-04 48f measured-passed retry (pre-cleanup,
  source-bound path: motivation only, not clean evidence).
- Arms: open_loop, closed_loop, closed_loop_no_escalation.
- Derive tau_v9 from the v9 open arm with the same pre-registered
  rule BEFORE reading closed-arm acceptance; do not reuse anchoring
  runs as comparison evidence.
- m4 stays floored until the intersection-approach primitive exists
  (plan step 3).
