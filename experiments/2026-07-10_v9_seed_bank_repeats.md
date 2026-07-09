# 2026-07-10 v9 repeats across three seed banks

Setup: DRIVELOOP_DD2_SEED_BANK (bank*100 + iteration seed offsets;
bank 0 = original runs). Banks 1-2: open (1 iter) + closed (3 iters,
tau 0.45, generation lever with single-rung steps-50 ladder) on the
same five cases, evaluator and baseline unchanged. Uniform recount at
J >= 0.45 (the bank-0 open arm originally ran at target 0.7, so its
recorded accepted_count is not comparable).

## Results (best J per case, open -> closed)
bank0: open [0.2, 0.546, 0.407, 0.2, 0.2] -> closed [0.2, 0.546,
0.430, 0.578, 0.438]; acceptances 1 -> 2.
bank1: open [0.2, 0.2, 0.2, 0.564, 0.2] -> closed [0.2, 0.2, 0.2,
0.564, 0.441]; acceptances 1 -> 1.
bank2: open [0.442, 0.446, 0.431, 0.2, 0.2] -> closed identical;
acceptances 0 -> 0.

## Reading
- Closed is never below open per case (attempt 1 shares the bank's
  seed; best-of is monotone by construction).
- Uplift materialized in 2 of 3 banks (4 of 15 case-slots, +0.02 to
  +0.38); aggregate acceptances closed 3/15 vs open 2/15.
- The steps-50 lever is not a universal gain: in bank2 no retry beat
  attempt 1 in any case. The m4 recovery (bank0, +0.378) is a
  seed-by-parameter interaction, not a guaranteed effect.
- Cross-bank case variance is large (e.g. m1 0.2/0.2/0.442): J at
  n=5 cases is seed-sensitive; single-run comparisons between arms
  should not be over-read.

## Claim boundary
Three banks, five cases each; detector night floor still pins several
cells at 0.2; single window (candidate70). Supported claim: the
closed loop weakly dominates the open loop under a shared first
attempt and sometimes recovers floor cases to acceptance; magnitude
is seed-dependent. No semantic success claims.
