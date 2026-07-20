# 2026-07-20 A rain truck window completes a same-object, three-condition closed-loop series

The night note built a night truck (candidate1313) and showed the closed loop lifts
it +0.373 via rung-2 rebinding. This note adds the third condition -- a daytime
rain truck (candidate2751) -- so the same actor class, truck, now has a closed-loop
reading in day, night, and rain. It is the cleanest evidence yet that DriveLoop's
loop is condition-robust and that one mechanism carries it.


## The rain window

candidate2751, train enumeration, scene "Rain, cross intersection, lane change,
parking lot" -- a single truck instance (9276cce6...055f) present across all eight
front frames, ground-truthed as rain (not night) from raw nuScenes scene.json (165
rain scenes, 149 of them daytime). Built with the category-neutral pipeline and
added to the pool with a rain tag; prompt -> source selection now resolves the
truck across all three conditions:

    rainy ... a truck cuts in       candidate2751  (rain)
    daytime ... a truck cuts in     candidate1677  (day)
    night ... a truck cuts in       candidate1313  (night)


## The three-condition truck series (v10b, yolov8x, 3 attempts, bank0)

    condition  window         open S_perc   closed best     uplift    best
    day        candidate1677  0.171         0.562           +0.391    @2 rebinding
    night      candidate1313  0.000         0.373           +0.373    @2 rebinding
    rain       candidate2751  0.000         0.417           +0.417    @2 rebinding

Same object, three conditions, one mechanism. In every case the single pass floors
or near-floors (target detections 1, 0, 0) and rung-2 source rebinding surfaces the
truck (detections -> 12, 3, 5) for an uplift of +0.37 to +0.42 in S_perc. Rung-1
(reseed + size/steps) does not move any of the three; the gain is rung-2 rebinding
throughout. Night and rain start the single pass at exact zero (the degraded
condition puts the injected truck below the detector on the bound frame), yet the
loop still recovers +0.37 / +0.42 by rebinding to a frame where it is detectable.


## Why this matters

The motorcycle table (grand mean +0.098 over seven arms) and the day-truck (+0.39)
established that closing the loop beats the single pass. This series shows the
effect is not a daytime artifact: it holds under night and rain, the two conditions
that most degrade a detector, and it holds for the same actor. It also localises the
mechanism -- across object (motorcycle, truck) and condition (day/night/rain), the
load-bearing rung is source rebinding, which shifts to a neighbouring source frame
where the injected actor is resolvable. "Open-loop floor is not closed-loop floor"
is now shown across three conditions on one actor.


## Claim boundary

Three windows, one case each, seed bank0, single run, detector-level v10b offline
rescore; open-versus-closed uplift, not a semantic-success claim (the strict quality
bar is not passed). The night motorcycle (candidate1300) remains a genuine floor: a
small actor stays below the detector at night even after rebinding, so the loop has
no signal to climb -- the recovery here depends on the actor being large enough to
resurface once the source is rebound. The load-bearing points are the consistent
positive sign across conditions and the single mechanism (rung-2) that carries all
three.
