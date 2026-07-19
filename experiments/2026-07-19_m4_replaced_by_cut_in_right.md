# 2026-07-19 Replacing m4_intersection_approach with m4_cut_in_right, and the seven-arm render

m4_intersection_approach grounds to the "approaching" primitive, which by design
(c95d5f4) builds no actor_motion_surface_plan, so it is v10b-unmeasurable. Two
options were on the table: repair it (give it a surface plan and re-render) or
replace it. Repair was rejected on the archive: the candidate70 window produces
no usable track on any of its fifteen attempts (2026-07-18_m4_is_a_parse_failure_not_a_defect.md),
its S_ctrl motion channel is already scored honestly at 0.0 without a re-render,
and giving "approaching" a surface plan would reverse the deliberate
"approach is not a fabricated cut-in" caliber. So m4_intersection_approach is
retired and replaced with m4_cut_in_right.


## The new case

    m4_cut_in_right  "night urban street, a motorcycle cuts in from the right
                      toward the ego vehicle"

m1, m2, m3 and m5 are all left maneuvers. A right-side cut-in is chosen so the
new case exercises lateral_side +1.0 and the right-neighbour view restriction
(cam_front + cam_front_right + cam_back_right, indices 1/2/3), a signal absent
from the rest of the set. It grounds to cut_in and is measurable under v10b.


## The render, and the recipe validation

Rendered on all seven arms of the three-window table with a token-safe wrapper
(scripts/render_window_case.py) that reads each window's binding byte-exact from
its no-injection baseline directory; the arm recipe is set by the environment:

    DRIVELOOP_EGO_INJECTION=1
    DRIVELOOP_DD2_SEED_BANK=0                                     bank0
    DRIVELOOP_DD2_WEIGHT_PATH=<ft checkpoint gligen>             set = fine-tune arm
    DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE=1.5                       set = dims arm

The fine-tune checkpoint is loaded through the mini_local config's env gate
(DRIVELOOP_DD2_WEIGHT_PATH), which is why every arm records config_name
drivedreamer2_img_cond_mini_local. The recipe reproduces the archive exactly: a
re-rendered m1 rescored under v10b matches the archived arm's v10b S_perc to six
decimals on every combination checked -- candidate162 official 0.407593,
candidate162 ft 0.130919, candidate70 official 0.165998, candidate70 ft 0.367806
-- so generation is deterministic at bank0 and the wrapper reproduces each arm.


## m4_cut_in_right, v10b S_perc (class fidelity in parentheses)

    window         official_anchor   ft6322(_dims1p5)   official_dims1p5
    candidate162   0.393 (0.33)      0.341 (1.00)       --
    candidate2216  0.130 (0.00)      0.125 (0.00)       --
    candidate70    0.191 (0.00)      0.120 (1.00)       0.333 (0.75)

FT lever (ft minus its window's official anchor): candidate162 -0.052,
candidate2216 -0.005, candidate70 -0.071.


## Findings

1. m4_cut_in_right is measurable on all seven arms (allowed_view_count 3, a real
   S_perc), where m4_intersection_approach was perception_unmeasurable. The
   manifest-hygiene item is closed by replacement, not repair.
2. The FT arm is below the official anchor on all three windows (-0.05 to -0.07),
   consistent with the established result that the FT lever does not survive v10.
   The new case reinforces that conclusion rather than contradicting it.
3. candidate2216 floors at class fidelity 0.00 on both arms, consistent with its
   detector-floor behaviour on the left cases. candidate70's dims1.5 arm is its
   strongest here (0.333, fidelity 0.75): the larger injected box raises
   detection on this sparse window.


## Claim boundary

One seed (bank0), one attempt per arm, detector-level v10b offline rescore. The
right-side geometry uses the 3.2 / 9 defaults, which are less human-verified than
the left 3.5 / 20 profile. Values are S_perc-level and are not a video
semantic-success claim. m4_intersection_approach is retired from the case set;
its S_ctrl treatment (target_motion 0.0 from the archived measurement) is
unaffected and needed no GPU.
