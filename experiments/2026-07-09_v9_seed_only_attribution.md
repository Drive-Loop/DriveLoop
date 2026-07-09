# 2026-07-09 v9 attribution: seed-only ablation isolates the parameter effect

Arm: exp_v9_seed_only = closed loop with --no-refiner-escalation under
the new per-attempt seed offset (reseed happens; generation-parameter
escalation does not). Same tau 0.45, evaluator, baseline, window as r4.
Because the seed offset is deterministic per iteration, attempt 2 in
this arm and in r4 share the SAME seed and differ only in
num_inf_steps (30 vs 50): a matched-seed controlled comparison.

## Results (attempt-level J)
m1 0.2/0.2/0.2; m2 0.546 accepted at attempt 1; m3 0.407/0.410/0.2;
m4 0.2/0.2/0.2; m5 0.2/0.408/0.2. Accepted 1/5.

## Matched-seed comparison (attempt 2: seed offset 1, default vs steps 50)
m3 0.410 -> 0.430; m4 0.200 -> 0.578; m5 0.408 -> 0.438.

## Reading
- m4's feedback-driven acceptance is attributable to the parameter
  escalation, not resampling: three reseeds at default parameters all
  stay at the floor; steps 50 at the same seed recovers to 0.578.
- Reseeding alone provides mid-level bumps (m3/m5 attempt 2) that do
  not cross tau; the parameter effect adds a consistent positive
  increment at matched seeds (+0.02 to +0.378, n=3 cases).
- Arm ranking at tau 0.45: full lever 2/5 > seed-only 1/5 = legacy
  closed r3 1/5 = open 1/5.

## Claim boundary
n=1 run per arm and n=3 matched-seed pairs; night detector floor
still caps m1; single window. Statements stronger than "the
generation-parameter feedback lever has a real, seed-controlled
effect and recovered one floor case to acceptance" require repeats.
