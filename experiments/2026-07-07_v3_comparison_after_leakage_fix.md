# v3 three-arm comparison after target-leakage fix

Date: 2026-07-07 | tau recalibrated to 0.7 (anchored to the manually verified
48f exemplar: S_perc 0.468 -> J 0.734 under w=0.5/0.3/0.2)

## Result (targets strictly motorcycle)

| case | open loop | closed loop | saturated | 
| --- | ---: | ---: | ---: |
| m1 | 0.731 pass | 0.731 pass (1) | 0.731 pass (1) |
| m2 | 0.718 pass | 0.718 pass (1) | 0.718 pass (1) |
| m3 | 0.500 fail | 0.500 fail (3) | 0.500 fail (3) |
| m4 | 0.500 fail | 0.500 fail (3) | 0.500 fail (3) |
| m5 | 0.709 pass | 0.709 pass (1) | 0.709 pass (1) |

## Findings

1. The v2 "closed-loop recovery" of m3/m4 was entirely a target-label
   leakage artifact ("ego vehicle" added car to the target set). After the
   fix, prompt-level refinement alone does not move detector evidence for
   the failed cases: all three arms tie.
2. The evaluation is honest and deterministic: the loop refuses to accept
   failures instead of gaming the metric.
3. Conclusion: the refinement action space must include structured-condition
   escalation (Sec. 3.5 levers), not only prompt wording. Next: per-attempt
   proximity/size escalation of the injected actor track (boxes3d surface).

## Artifacts

- outputs/driveloop/exp_v3_open_loop / exp_v3_closed_loop / exp_v3_closed_loop_saturated
