# Correction: rung-2 source rebinding is a modulo no-op (2026-07-21)

## Finding (binding audit, block 317)
Every closed-loop run binds through the 144-record runtime subset, which
contains exactly one candidate window (candidate_start_count = 1). In
build_source_sample_binding, candidate_index = (index + offset) % len(starts),
so any candidate_offset maps back to the same window. Audit of
candidate1677/1313/2751 v10b runs and the offset sweep shows skip=0,
front_record identical (fidx/token constant) on every attempt, including
attempts that requested offset 1 or 3. Rung-2 never shifted the source frame.

## Attribution correction
Attempt 1 and attempt 2 differ only in the per-attempt seed offset
(same size_scale 1.5, same num_inf_steps 50, offset no-op). Therefore the
attempt-2 recoveries previously attributed to source rebinding
(truck day 0.171->0.562, night 0->0.373, rain 0->0.417, bicycle 0->0.500)
are reseeding draws under the escalated recipe. Unaffected: the headline
closed>=open protocol claim, all measured scores, the never-regress
property, and the night-motorcycle floor. The Table 4 seed-only control
remains valid but covers candidate162 rung-1 requests only; reseed
contribution is window-dependent and must not be generalized.

## Invalidated artifacts
outputs/driveloop/*_rebind_sweep_off* (12 runs): offset no-op AND a recipe
bug (DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE=1.5 stacked multiplicatively on
structural size_scale 1.5 -> 2.25x actor dims). Do not cite.

## Next
1. Rung-2 seed distribution: render the escalated recipe at seed banks 3/4/5
   on candidate1677/1313/2751/41 (no dims env, no offset); together with the
   existing a1/a2 this gives 5 seeds per window.
2. Rewrite the Sec. 4.3/4.5 rebinding narrative as escalated reseeding.
3. Implement true rebinding (bind against the full source enumeration, not
   the one-window subset) as a generation-improvement item; re-measure.
