# 2026-07-18 Window expansion: the fidelity lever effect is window-conditional

Two new source-bound windows built with the committed tooling
(scan -> identity probe with double anchor -> runtime subset builder;
enumeration source cam_all_train/v0.0.2, binding indices 162 and 2216
match the scan): candidate162 (near, real motorcycle at 4-6 m, scene
1d4db80d) and candidate2216 (mid, 6-18 m dynamic, scene 90d616aa,
described as a tricycle-and-parked-cars narrow road). Per window:
per-weight no-injection baselines plus official-anchor and
ft6322+dims1.5 arms on the v10 manifest (m1/m2/m3/m5), bank0 seed,
one attempt. All gates verified: binding ready, real-track engaged
(9-10 audit entries per case), dims_scale 1.5 in the ftdims mapping,
perception_baseline_available 1.0. Scored offline under v10b.

## v10b S_perc (class fidelity / support)
candidate162          | anchor            | ftdims
m1                    | .408 (.67/3)      | .131 (1.0/1)
m2                    | .397 (.67/3)      | .000 (-/0)
m3                    | .459 (.75/4) trk2 | .408 (1.0/2)
m5                    | .415 (.75/4)      | .523 (1.0/3) trk3
mean                  | .420              | .266
candidate2216         | anchor            | ftdims
m1                    | .160 (0.0/1)      | .127 (0.0/1)
m2                    | .000 (-/0)        | .127 (0.0/1)
m3                    | .116 (0.0/1)      | .000 (-/0)
m5                    | .000 (-/0)        | .149 (0.0/1)
mean                  | .069              | .101

## Findings
1. The candidate70 fidelity pattern (anchor renders the actor
   person-like, FT restores the motorcycle label) does NOT
   generalize: on candidate162 the official anchor already renders a
   motorcycle-majority actor (fidelity .67-.75 at 3-4 support
   frames), and on candidate2216 both arms sit at the detector floor
   with fidelity 0.0 everywhere. The lever effect measured on
   candidate70 is a property of that window, not of the weights.
2. On candidate162 the ft+dims arm trades evidence volume for label
   purity: fidelity 1.0 in every detected cell, but support drops
   (3-4 -> 0-3) and m2 loses all detections. Mean S_perc favors the
   anchor (.420 vs .266).
3. Window difficulty dominates all lever effects observed so far.
   The near window produces the project's first multi-frame tracks in
   maneuver cases (anchor m3 track 2; ftdims m5 track 3 with S_perc
   .523, the highest maneuver-case value in the project); the mid
   window's tricycle-like instance in a cluttered scene is nearly
   undetectable in either arm.
4. Unexplained single cell: candidate162 ftdims m2 has zero
   superclass detections where the anchor has three; consistent with
   single-seed variance and not further interpreted.
5. Claim discipline going forward: no lever claim may be promoted
   from a single window. The minimum reporting unit is the
   three-window matrix (candidate70, candidate162, candidate2216),
   and fidelity remains the right axis with its lever sensitivity
   reported per window.

## Claim boundary
One seed, one attempt, n=4 cases per window, two new windows;
detector-level only, v10b offline protocol (v9 remains protocol of
record). The candidate2216 actor is annotated motorcycle but reads as
a tricycle in the scene description; its floor result may reflect
actor type as much as distance. New-window videos have not yet had
frame-stepped human review.
