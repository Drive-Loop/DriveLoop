# 2026-07-18 Window-admission probe (C1/C2/C3 gates, C4 diagnostic), and why C4 is not a collision gate

A pre-generation, read-only probe that decides, before spending a GPU render,
whether a (window, case) is worth generating. It runs the real no-GPU assembly
chain and reuses the adopted v10b evaluator, so its answers cannot drift from the
runtime pipeline. `scripts/run_window_admission_probe.py` with
`tests/test_window_admission_probe.py`.


## The four checks

    C1  binding readiness   build_source_sample_binding(...).ready on the window's
                            source config -- the same call the DD2 backend makes
                            before its GPU subprocess. A property of the window.
    C2  v10b measurability  the case grounds to a lateral maneuver whose
                            actor_motion_surface_plan resolves target cams and a
                            lateral side, so v10b _views_to_evaluate is non-empty.
                            The "approaching" primitive (m4 class) builds no plan
                            and is unmeasurable.
    C3  baseline sanity     the no-injection baseline that will be subtracted
                            exists, lives under a no-injection directory (not a
                            per-run staging video, the block-220 trap), and belongs
                            to the intended window. Reports the source-row (top
                            band) fingerprint.
    C4  super-class presence  DIAGNOSTIC ONLY. super-class detections of the
                            no-injection baseline in the case's restricted views.

Verdict: REJECT (C1) / BASELINE_SUSPECT (C3) / WARN (C2 unmeasurable) / ADMIT.
C4 is reported, never gated.

Source config and the baseline video are read byte-exact from a baseline run
directory (`--source-from-baseline-dir`), reading both result.json (v10w windows)
and history.jsonl (older v9 runs).


## Three-window admission table

Run over the v10 case manifest (m1, m2, m3, m5) on all three windows, config read
from each window's no-injection baseline directory:

    window         C1.ready   C2 (all cases)   verdict
    candidate70    True       measurable       ADMIT x4
    candidate162   True       measurable       ADMIT x4
    candidate2216  True       measurable       ADMIT x4

C1 and C2 do not distinguish window quality: every window binds and every left
maneuver is measurable. The window-quality signal (candidate162's subtraction
behaviour, candidate2216's detector floor) is not in the binding/measurability
gates. C3 passes on all six per-window-per-weight baselines. The source-row
fingerprint reproduces the archived values and is weight-invariant per window:
candidate162 official and ft6322 both give [96.4, 101.8, 101.6, 107.5, 96.8,
109.4] (mean 102.2, matching the archived 102.199); candidate70 both give
[45.9, 55.8, 63.8, 32.1, 52.8, 37.2] (matching the archived [46.3, 56.4, 63.3,
32.9, 53.8, 39.2]).


## C4 reconciliation: super-class presence is not the collision signal

A first C4 attempt scored "collision" as baseline super-class detections in the
restricted views. It reads 0 on all four tested baselines (candidate162 and
candidate70, official and ft6322). Reconciled against the archive:

- `perception_baseline_subtracted_count` is large and common: 0 on runs without a
  baseline, otherwise clustered at 63-74 per case, up to 294. The subtraction is
  class-agnostic (`_baseline_view_detections` is unfiltered; `_subtract_baseline`
  matches boxes by IoU regardless of label), so it is driven by scene objects such
  as cars, not by a super-class actor.
- `perception_superclass_detection_count` does not appear in the archive at all;
  it is an offline v10 metric, not a stored runtime one.
- candidate70's baseline carries more detections (84) than candidate162's (52),
  yet candidate70's injected motorcycle survives subtraction (moto_raw = moto_kept,
  2026-07-18_c70_subtraction_probe.md) while candidate162's is removed. Raw
  detection count therefore does not rank the two windows; box overlap at the
  injected actor does.

So a zero super-class C4 does not mean the arm's actor survives, and a raw
class-agnostic count over-warns and mis-ranks. The correct pre-generation
collision predictor is: project the injected actor's box3d to pixels (DD2's
projection with camera intrinsics) and test IoU against the baseline detections
at that box. That is left as separate future work. C4 was demoted to a diagnostic
("baseline super-class presence in the maneuver views") that is reported but never
affects the verdict.


## Claim boundary

The probe is a pure pre-generation tool. It changes no paper number, no
acceptance behaviour, and no protocol; it is not wired into the runner. The
three-window ADMIT result is C1/C2/C3 only. C4 needs YOLO (opt-in via
`--baseline-superclass-check`) and is diagnostic. A precise collision gate is not
delivered here.
