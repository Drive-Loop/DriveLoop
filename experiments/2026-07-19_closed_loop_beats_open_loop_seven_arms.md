# 2026-07-19 The closed loop beats the open loop on every arm: v10b S_perc uplift

DriveLoop's central claim is that closing the loop -- generate, evaluate, refine,
regenerate -- beats the single-pass DD2 baseline. This note measures it directly:
the v10b-driven closed loop (up to 3 attempts, refiner escalation on) versus the
open-loop single pass (attempt 0), on all seven arms of the three-window table,
five cases each. Rendered with scripts/render_window_case.py --max-iterations 3
--perception-weights yolov8x.pt --use-task-utility; summarized per case with
scripts/summarize_closed_loop.py (attempt 0 versus the best attempt by S_perc).


## Result: positive on all seven arms, never negative

    arm                        mean S_perc uplift (closed best - open)
    candidate162  official      +0.032
    candidate162  ft6322_dims   +0.066
    candidate2216 official      +0.080
    candidate2216 ft6322_dims   +0.224
    candidate70   official      +0.048
    candidate70   ft6322        +0.123
    candidate70   official_dims1p5  +0.111
    -----------------------------------------
    grand mean over 7 arms      +0.098

Across 35 case comparisons (7 arms x 5 cases) the closed loop improved 20 and left
15 unchanged; none regressed, because the loop keeps the best attempt, so its
worst case is the open-loop pass.


## Per-case S_perc (open -> closed best; best attempt in brackets)

    case   c162off      c162ft       c2216off     c2216ft      c70off       c70ft        c70dims
    m1     .408->.460[1].131->.413[1].160->.160   .127->.452[2].166->.166   .368->.368   .352->.384[1]
    m2     .397->.397   .000->.000   .000->.000   .127->.400[1].392->.392   .148->.148   .138->.400[1]
    m3     .460->.460   .408->.408   .116->.369[2].000->.193[1].123->.362[1].142->.512[1].170->.367[1]
    m4     .393->.467[1].341->.387[1].130->.130   .125->.453[2].191->.191   .120->.363[2].333->.396[1]
    m5     .415->.447[1].523->.523   .000->.147[2].149->.149   .157->.158[1].000->.000   .357->.362[2]


## The loop helps most where the open loop was worst

The largest gains land on the arms and windows the single pass scored lowest.
candidate2216 -- the window an earlier open-loop reading called a detector floor
"the loop cannot help" -- gains +0.080 (official) and +0.224 (ft): its m1/m2/m3/m4
climb from 0.00-0.13 to 0.19-0.45. That earlier reading was wrong: open-loop floor
is not closed-loop floor. The refiner's source rebinding (attempt 2) shifts to a
neighbouring source frame, and its size/step escalation (attempt 1) enlarges and
sharpens the injected actor; both surface detectable actor evidence the single
pass missed. candidate70's dims1.5 arm improves on all five cases.


## The escalation ladder is not redundant

Wins appear at both rungs. Rung 1 (size_scale 1.5, num_inf_steps 50, per-attempt
reseed) carries the candidate162 and candidate70-dims gains (best@1); rung 2
(source rebinding to a neighbouring frame) carries the candidate2216 and
candidate70-ft gains (best@2). A single-rung loop would leave the rung-2 windows
near floor.


## Rigor and claim boundary

The comparison is the DD2 single pass (attempt 0) versus DriveLoop's closed loop
(up to 3 attempts) -- the paper's open-versus-closed comparison. One seed bank
(bank0), one closed-loop run per arm, detector-level v10b offline rescore; not a
video semantic-success claim.

Confound to decompose next: attempt 1 both reseeds and escalates (size / steps),
so its uplift mixes a best-of-seeds effect with the escalation. A seed-only
control (three seeds, no escalation) would isolate them. The rung-2 (rebinding)
wins are not a reseed effect, so the escalation ladder demonstrably contributes
beyond seed variance, but the rung-1 split is not yet separated. These are
single-seed per-arm figures and the per-case magnitudes carry seed variance
(2026-07-13 bank1 record); the load-bearing claim is the sign -- positive on every
arm -- and the aggregate, not any single cell. A bank1 replication of this table
would harden the magnitudes.
