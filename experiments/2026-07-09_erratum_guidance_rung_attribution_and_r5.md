# 2026-07-09 Erratum: guidance-rung attribution + closed r5 replication

## r5 (rung-2 removed; same tau/evaluator/baseline/window)
accepted 2/5. Attempt-level J: m1 0.2/0.2/0.2; m2 0.546 accepted at
attempt 1; m3 0.407/0.430/0.2; m4 0.2/0.578 accepted at attempt 2;
m5 0.2/0.438/0.2.

## Replication check (mechanism determinism)
m4 attempt 2 reproduces r4's 0.578 exactly (same seed offset, same
steps-50 parameters): the lever pipeline is deterministic given
matched seed and parameters.

## Erratum: the guidance-harm attribution was WRONG
The 0318256 record claimed max_guidance_scale 7.0 "sent both cases
back to the floor". r5 provides the matched-seed test: at seed
offset 2 with steps 50, m3 and m5 attempt 3 are 0.2 WITHOUT guidance
- identical to r4 WITH guidance and to seed-only at default
parameters. The attempt-3 floor is driven by the seed-2 draw itself;
the guidance effect is unmeasured (indistinguishable at the floor),
not measured-harmful.

## Standing decision
The single-rung ladder (steps 50 at all levels) is retained: the
guidance rung had no measured benefit and the simpler ladder is
easier to attribute. Reinstating a guidance rung would require a
matched-seed comparison on a case that is NOT at the floor.

## Claim boundary unchanged
n=1 per arm; night detector floor; single window.
