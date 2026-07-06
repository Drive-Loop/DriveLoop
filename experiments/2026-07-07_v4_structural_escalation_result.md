# v4: structured-condition escalation closes the loop where prompts cannot

Date: 2026-07-07 | Same setup as v3 (tau=0.7, strict motorcycle targets)

## Result

| case | open loop | prompt-only loop (v3) | +structural (v4) | attempts |
| --- | ---: | ---: | ---: | ---: |
| m1 | 0.731 pass | 0.731 pass | 0.731 pass | 1 |
| m2 | 0.718 pass | 0.718 pass | 0.718 pass | 1 |
| m3 | 0.500 fail | 0.500 fail | 0.768 pass | 2 |
| m4 | 0.500 fail | 0.500 fail | 0.500 fail | 3 |
| m5 | 0.709 pass | 0.709 pass | 0.709 pass | 1 |

- acceptance: 3/5 -> 3/5 -> 4/5; mean best J: 0.632 -> 0.632 -> 0.685
- m3 trajectory: attempt0 S_perc=0.000 -> attempt1 (esc level 1: injected
  track 18m -> 13.5m, size x1.25) S_perc=0.536, Q_cov=0.38 -> accepted.
- m4 resists escalation up to level 2 (S_perc stays 0): honest hard case;
  likely requires source rebinding or stronger structural response study.

## Interpretation

Deterministic backend + identical evaluator isolate the mechanism chain:
(1) v3 saturated tie shows retry count alone adds nothing;
(2) v3 prompt-escalation tie shows wording alone cannot create detector
    evidence in this regime;
(3) v4 recovery of m3 shows per-frame boxes3d structural escalation is a
    real pixel-level lever, exactly the "refine the structured condition"
    branch of the paper's Sec. 3.

## Claim boundary

Perception-level acceptance only; m3's video still requires manual
alignment review before any semantic-success claim.
