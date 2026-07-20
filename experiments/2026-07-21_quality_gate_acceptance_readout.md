# Quality gate: acceptance readout and contact-sheet review (2026-07-21)

## Context
Quality-acceptance line. Block 311 read S_perc / direction metrics across the
six v10b closed-loop pool runs; scripts/quality_gate.py formalizes the gate;
contact sheets (8-frame 4x2 tiles) were reviewed by eye.

## Gate readout (tau = 0.3, bank0, best-by-S_perc attempt)
| run | S_perc | dir | delta_x | gate |
|---|---|---|---|---|
| candidate1677_truck_cut_in_v10b | 0.562 | 1.0 | +16.1 | PASS |
| candidate1313_night_truck_v10b | 0.373 | - | - | UNMEASURED |
| candidate2751_rain_truck_v10b | 0.417 | - | - | UNMEASURED |
| candidate1300_night_cut_in_v10b | 0.000 | - | - | LOW_SPERC |
| candidate28_bus_v10b | 0.634 | 0.0 | -23.6 | DIR_FAIL |
| candidate41_bicycle_v10b | 0.500 | - | - | UNMEASURED |

No hidden gate-passing attempt exists in any run (attempt scan).

## Findings
1. Three-state gate is required. Direction is UNMEASURED (metric absent), not
   failed, when the selected view has < 3 frames with a target-class detection
   (composite_perception._maneuver_direction_check). det=3/5/8 for the three
   UNMEASURED runs did not satisfy the per-frame requirement.
2. Direction measurability is itself gated by detection density: across all six
   runs every attempt 0/1 is unmeasured; only truck-day attempt 2 (rung-2
   rebinding) reaches measurability. Rebinding is a precondition for direction
   evidence, not just for detection recovery.
3. Bus is the quantified perception-vs-semantics counterexample: best S_perc of
   the pool (0.634, det=7) with the measured direction wrong (delta_x = -23.6).
   Consistent with the stationary-ego-at-intersection analysis in Sec. 4.5.
4. Contact sheets: truck-day cut-in is clearly visible (matches dir=1.0);
   night motorcycle is invisible to the eye (floor claim holds visually);
   night/rain trucks are recognizable at very low contrast; one moving
   orange blob artifact in the intersection window suggests an injection
   fidelity issue worth a follow-up.

## Decisions
- tau = 0.3 (non-floor S_perc range 0.37-0.63; the binding constraint is the
  direction gate, not the threshold).
- UNMEASURED routes to human contact-sheet review, not to auto-fail.
- Next: offline rung-2 offset sweep (offsets 1-4) on the three UNMEASURED
  windows to test whether a neighboring source frame makes direction
  measurable; loop protocol (T=3) unchanged.

Scope: detector-level v10b offline protocol, single runs, seed bank 0.
