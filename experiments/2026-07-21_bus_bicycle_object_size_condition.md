# 2026-07-21 Bus and bicycle windows: the unrecoverable floor needs small size AND a degraded condition

The night note reported a detector floor for a night motorcycle and framed it as
actor-size dependent. Two more windows -- a daytime bus (large) and a daytime
bicycle (small) -- sharpen that claim: the loop's recovery depends on actor size
and condition together, and the only truly unrecoverable cell is a small actor in
a degraded condition.


## Two windows, same pipeline

candidate28 (bus, "Overtaken by taxi, construction site") and candidate41 (bicycle,
"Random scene, arrive at intersection") are daytime train bindings, each with a
single target instance present across all eight front frames. Bicycles are
transient; a broad scan of the 818 daytime bicycle candidates finds 173 with a
full-eight-frame instance, from which candidate41 is taken. Both are added to the
pool, which now spans five object classes -- motorcycle, pedestrian, truck, bus,
bicycle -- and prompt-driven selection resolves each (a bus prompt selects
candidate28, a bicycle prompt candidate41).


## Closed loop (v10b, YOLOv8x, 3 attempts, bank0)

    binding (day)      size    open S_perc   closed best   note
    candidate28 bus    large   0.634         0.634         open already high; loop keeps it
    candidate41 bike   small   0.000         0.500         recovered via rung-2 rebinding

The bus single pass already scores 0.634 (seven target detections): a large,
distinctive actor in daylight is detectable on the bound frame, so the loop has
nothing to add and simply keeps the best attempt (attempts 0.634, 0.466, 0.605; it
never regresses). The bicycle single pass floors at 0.000 (zero detections) -- the
small injected actor is not detected on the bound frame even in daylight -- but
rung-2 source rebinding recovers it to 0.500 (detections 0 -> 8).


## The floor is (small AND degraded), not small alone

Placing these next to the earlier windows gives an object-size x condition picture:

    actor (size)        condition   open    closed   recovered?
    bicycle (small)     day         0.000   0.500    yes (rung-2)
    motorcycle (small)  night       0.000   0.000    no
    bus (large)         day         0.634   0.634    n/a (already high)
    truck (large)       day         0.171   0.562    yes (rung-2)
    truck (large)       night       0.000   0.373    yes (rung-2)
    truck (large)       rain        0.000   0.417    yes (rung-2)

Every low-open cell is recovered by rung-2 rebinding except one: the night
motorcycle, which stays at zero across all attempts. So the earlier "actor-size
floor" is really a joint floor: a small actor floors at the single pass in any
condition, but rebinding recovers it in a good condition (bicycle, day) and fails
only when the condition is also degraded (motorcycle, night). A large actor either
is already detectable (bus, day) or is recovered by rebinding (truck, all three
conditions). The single unrecoverable cell -- small size and a degraded condition
together -- bounds where the loop can help.


## What this says about the loop

Two behaviors, both already claimed, are confirmed on new object classes: the loop
never regresses (bus: open 0.634 kept despite two worse refinements), and rung-2
rebinding is the workhorse that surfaces an undetected actor (bicycle: 0 -> 0.5).
The refinement is that recovery is not guaranteed -- it requires that a source
frame on which the injected actor is detectable exists, which a degraded condition
can deny for a small actor.


## Claim boundary

Two windows, one request each, seed bank0, single run, detector-level v10b offline
rescore. The object-size x condition table mixes windows of differing inherent
difficulty (the bus and truck day bindings render their actors with very different
open-loop detectability), so the table localizes the recoverability pattern, not a
controlled size sweep at fixed difficulty. The load-bearing point is qualitative:
the only unrecovered cell is small-and-degraded.
