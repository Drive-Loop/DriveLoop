# 2026-07-20 Night windows: condition-aware selection, and an actor-size-dependent detector floor

Extending the source pool from object diversity (motorcycle/pedestrian/truck) to
condition diversity required first correcting a labelling error, then building a
real night window and measuring the closed loop on it. The result: prompt-driven
selection now separates day from night, and the night generation exposes a clean,
honest boundary -- the yolov8x detector floor at night is actor-size-dependent.


## A correction: the existing windows were mislabelled night

The pool tagged candidate70/162/2216/1409 (and implicitly 1677) "night".
Ground-truthing lighting against raw nuScenes scene.json (850 scenes, 99 contain
"night") shows all of them are daytime scenes -- e.g. candidate162 is "Delivery
motorcycle turns left, veh turn right", candidate1409 "Peds waiting to cross the
road". The processed enumeration's abbreviated descriptions carry no lighting term,
so the earlier tags were assumptions. They are corrected to daytime here.


## A real night window, from the val enumeration

The train enumeration (cam_all_train v0.0.2, 334 unique scenes) contains zero of
the 99 night scenes; they are all in val. So the night windows are built from the
val enumeration (cam_all_val v0.0.2) with the same category-neutral pipeline:

- candidate1300, "Night, wait at intersection, motorcycle, turn left" -- one
  motorcycle instance across all eight front frames.
- candidate1313, "Night, truck, congestion" -- one truck instance across all eight.


## Selection now spans object x condition

With both in the pool (night tags), prompt -> source selection resolves the full
2x2:

    prompt                              selected
    night ... a truck cuts in           candidate1313  (truck, night)
    daytime ... a truck cuts in         candidate1677  (truck, day)
    night ... a motorcycle cuts in      candidate1300  (motorcycle, night)
    daytime ... a motorcycle cuts in    candidate162   (motorcycle, day)

Same object, different lighting -> different window: the condition tag is
load-bearing, not decorative.


## Night generation: the detector floor is actor-size-dependent

Closed loop, v10b (yolov8x, --use-task-utility, 3 attempts, bank0), same protocol
as the day tables:

    window (night)   actor        open S_perc   closed best     det (open->best)
    candidate1300    motorcycle   0.000         0.000           0 -> 0
    candidate1313    truck        0.000         0.373 [best@2]   0 -> 3

The night motorcycle floors on every attempt -- injection is fine (maneuver=cut_in,
tensor_control_ready, perception_measured=1, 8-9 background detections subtracted)
but zero of them fall in the motorcycle super-class at the target: yolov8x cannot
see a night motorcycle, and rung-1 size escalation and rung-2 rebinding both leave
it at zero. The night truck floors on the single pass (attempt 0/1: det 0) but
rung-2 source rebinding surfaces it (det 0 -> 3, S_perc 0 -> 0.373). So the floor
is not "night is unmeasurable"; it is "a small actor at night is below the
detector, a large one is not".


## Consistent mechanism, now at night

The night-truck gain is carried by the same rung-2 source rebinding that carried
the day-truck (+0.39) and candidate2216 gains. "Open-loop floor is not closed-loop
floor" holds at night for a detectable-size actor: the single pass reads 0.000, the
loop lifts it to 0.373 by rebinding to a source frame where the injected truck is
detectable. The night motorcycle bounds the claim -- when the actor is below the
detector in all attempts, the loop has no signal to climb.


## Claim boundary

Two night windows, one case each, seed bank0, single run, detector-level v10b
offline rescore. The night-truck +0.373 is an open-versus-closed uplift, not a
semantic-success claim (diagnosis would still fail the strict quality bar). The
load-bearing points: (1) condition-aware selection works; (2) the night floor is
actor-size-dependent, not a night-wide failure; (3) rung-2 rebinding surfaces night
detections for a large actor, reproducing the day mechanism.
