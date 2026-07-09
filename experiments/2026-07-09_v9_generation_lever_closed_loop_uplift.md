# 2026-07-09 v9 generation lever: first feedback-driven acceptance

## Shipped (commit 3765d27; 427 tests green)
Per-attempt seed offset (DRIVELOOP_DD2_SEED_OFFSET=iteration; attempt 0
byte-identical to before) and refiner generation-parameter escalation
(level 1: num_inf_steps 50; level 2: + max_guidance_scale 7.0) flowing
through the DD2 tester env overrides. Applied parameters recorded in
generation metadata.

## Closed arm r4 (same tau 0.45, same evaluator/baseline as r3)
accepted 2/5 (open arm equivalent: 1/5; r3 closed without lever: 1/5).
Attempt-level J:
- m1 0.2, 0.2, 0.2 (night detector floor unchanged)
- m2 0.546 accepted at attempt 1
- m3 0.407, 0.430, 0.2
- m4 0.2, 0.578 ACCEPTED at attempt 2 - first feedback-driven
  recovery from the floor across v8/v9; the case was 0.2 in every
  prior arm and version
- m5 0.2, 0.438, 0.2

## Readings
- The loop is no longer a replicator: attempt-level variance exists
  and acceptance improved exactly where iterations ran.
- Escalation rung 2 (max guidance 7.0) DEGRADED both cases that
  reached it (m3, m5 attempt 3 back to 0.2); next tuning: keep steps
  50 at rung 2, leave guidance at config default.
- Attribution unresolved: attempt-2 gains combine reseed + steps 50.
  A seed-offset-only ablation arm would separate sampling luck from
  the parameter effect; required before any paper claim stronger than
  "closed-loop feedback recovers cases the open loop leaves at floor".

## Claim boundary
No semantic success claims; scores are detector-based with the night
floor caveat; single window (candidate70), n=5 cases, single closed
run (run-to-run variance now exists BY DESIGN and needs repeats for
intervals). Human review of the m4 accepted video is pending and
gates any paper use of that case.
