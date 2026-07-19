# 2026-07-20 Cross-class closed loop: a truck window's S_perc lifts +0.39, again via rung-2 rebinding

The seven-arm table (2026-07-19) showed the closed loop beats the open loop on a
three-window motorcycle-cut-in family. This note reproduces that result on a
different actor class -- a heavy truck -- built with the same category-neutral
window pipeline and scored under the same v10b protocol, and finds the same
mechanism carries the gain.


## The window and the run

candidate1677 is a trainval overtake scene ("Overtake heavy truck ... arrive at
intersection") whose truck instance 018db3f9 is present in all eight front frames;
built scan -> find_candidate_actor -> identity probe -> runtime subset -> baseline,
and added to source_window_pool.json. With it in the pool, prompt -> source
selection separates three classes: a truck prompt selects candidate1677, a
motorcycle prompt candidate162, a pedestrian prompt candidate1409.

Closed loop: prompt "urban street, a truck cuts in from the left toward the ego
vehicle" -> select candidate1677 -> render_window_case --max-iterations 3
--perception-weights yolov8x.pt --use-task-utility, DRIVELOOP_EGO_INJECTION=1,
seed bank0. The injected cut_in is v10b-measurable (actor_motion_surface_plan,
eight per-frame boxes, maneuver=cut_in; perception_measured=1, view restriction
active, super-class pooling on).


## Result: S_perc 0.171 -> 0.562 (+0.391), best at attempt 2

    attempt  rung                         S_perc    J       detections
    0 open   single pass                  0.171     0.435   1
    1        size1.5 + steps50 + reseed   0.158     0.429   1
    2        source rebinding             0.562     0.681   12

The single pass is near floor (one detection, dominant net motion -1px: the
maneuver is not resolvable). Rung 1 (reseed + size/steps) does not help here.
Rung 2 -- source rebinding to a neighbouring frame -- surfaces a detectable truck:
detection_count 1 -> 12, target-support 1 -> 6 frames, dominant net motion
-1 -> +16.1px with maneuver_direction_consistent=1. The loop keeps attempt 2, so
open -> best is 0.171 -> 0.562, an uplift of +0.391 in S_perc (J 0.435 -> 0.681).


## Same mechanism as the motorcycle table, now cross-class

The largest gain again lands where the single pass was worst, and again it is the
rung-2 rebinding -- not the reseed/size rung -- that carries it (the candidate2216
story, on a new class). "Open-loop floor is not closed-loop floor" reproduces on
the truck: a single pass that looks like a detector floor is lifted +0.39 once the
loop is allowed to rebind the source. The escalation ladder is not redundant:
rung 1 alone would have left this window at floor.


## Claim boundary

diagnosis passed=false: absolute quality is still below the strict bar
(low_detection_coverage, low_detector_confidence, unstable_track). This is an
open-versus-closed *uplift* result -- one window, one case, seed bank0, single run,
detector-level v10b offline rescore -- not a video semantic-success claim. The
load-bearing points are the positive sign and the cross-class reproduction of the
rung-2 mechanism. (A default prompt-coverage evaluator scored the same chain
0.60 -> 0.95 and accepted; the v10b S_perc figures above are the number comparable
to the motorcycle table.)
