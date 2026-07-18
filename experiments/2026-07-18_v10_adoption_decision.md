# 2026-07-18 Adopting v10b as the perception protocol of record

The 2026-07-13 v10a/v10b records left adoption as "a separate recorded decision
(replacing v9 as the protocol of record, tau re-anchor, J recomposition)". The
three-window rescore on recovered baselines (2026-07-18_v10_three_window_sperc_on_recovered_baselines.md)
supplied the missing evidence: the v9 FT lever is a single-class detection-count
artifact that does not survive super-class pooling. This note records the
decision to adopt v10b and the five commits that land it, and it corrects the
premise that a tau re-anchor was required.


## The decision

v10b -- super-class evidence, class fidelity, and the maneuver view restriction --
is the perception protocol of record. The experiment pipeline defaults to it. A
run that reproduces the archived v9 numbers must set perception_protocol="v9"
explicitly; the flag exists precisely so the archive stays reproducible.

The evidence is in the S_perc record: the FT S_perc lever is +0.057 under v9 on
candidate70 and flips to -0.036 under v10b, is negative on candidate162 under
every protocol, and is detector-floor on candidate2216. At the J level the same
holds under all three S_ctrl calibers (-0.054 to +0.021 on candidate70 ft6322,
none near the v9 +0.088). The FT advantage v9 reported was quantity of detections,
not rendered actor evidence; v10b measures the latter through class fidelity.


## What landed (five commits, each with tests, full suite green)

    1c6a565  caliber C: object_presence is fidelity-weighted when the super-class
             evaluator reports class fidelity; falls back to binary target-class
             detection under v9 metrics.
    c75e2c1  perception_protocol flag: v9 / v10a / v10b selectable via a
             detector-free class resolver; default was v9 at this point.
    ba25a6f  a view-restriction-unresolved case (no actor_motion_surface_plan, so
             v10b resolves no scorable view) is recorded as "perception_unmeasurable"
             and stops the loop, instead of churning refinements against a case that
             cannot be measured and recording it as a low-score failure.
    7245c64  the pipeline default flips to v10b: the adoption.

The S_ctrl caliber is C (fidelity-weighted object_presence). Caliber B (raw
super-class object_presence) reintroduces the exact non-target over-count v10
exists to remove; caliber A (v9 target-class) ignores mislabelled target
detections. C weights presence by the share of super-class detections that read
as the requested class, and the J-level conclusion is caliber-robust regardless.


## There was no tau to re-anchor

The 07-13 records listed tau re-anchor as an adoption prerequisite. The archive
shows it is not one.

Acceptance in the runner is `score >= target_score or diagnosis.passed`. Across
50 accepted attempts in the archive, diagnosis.passed drove acceptance zero times;
acceptance is entirely `score >= target_score`. And target_score is a
per-experiment configuration knob, not a global calibrated threshold: the default
0.8 is unreachable under both v9 and v10 (the maximum archived J across the seven
three-window arms is 0.57), so under either protocol the loop runs to
max_iterations and records every attempt for offline analysis. Flipping the
protocol changes no acceptance behaviour on the default.

A principled global tau would need a systematic human accept/reject annotation set
to anchor against. There is none -- only ten scattered manual alignment
evaluations on unrelated smoke-test cases -- so even the v9 tau was an
uncalibrated default. Re-anchoring an uncalibrated per-experiment knob to match an
uncalibrated per-experiment knob is not a meaningful operation. Experiments that
set a low target_score should account for v10's lower J range when they choose it;
that is the experimenter's calibration, made per run, not a global constant this
adoption can fix.


## Claim boundary

What is adopted is the S_perc/S_ctrl protocol (v10b + caliber C), not a global
acceptance threshold. J recomposition under v10 (2026-07-18 J recomposition,
block 223) is arithmetic on the rescored S_perc plus construction D's S_ctrl plus
the recovered weights; it is not a runtime change and is not re-run per attempt.
v10b scores a case with no actor_motion_surface_plan as unmeasurable, which is
correct for an under-specified prompt but means such cases contribute no S_perc:
the manifest hygiene item from the 07-13 v10b record (m4 should be repaired or
replaced) is still open and is now enforced by the runner flagging it rather than
scoring it 0. The adoption is inert until an experiment enables perception
(sets perception_weights); the default pipeline with no perception weights is
unchanged.
