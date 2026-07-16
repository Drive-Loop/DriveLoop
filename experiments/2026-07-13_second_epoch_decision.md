# 2026-07-13 Second-epoch decision: declined; budget goes to window expansion

Decision on TODO item 5 (resume trainval FT for a second epoch):
DECLINED for now. The GPU budget goes to expanding the window set
instead.

## Rationale
1. After the v10 rescore, the only measurable FT value is class
   fidelity at near and mid range; S_perc and binary detectability
   show no FT gain under the superclass protocol.
2. The far-entry probe shows distant-actor fidelity untouched at
   epoch 1 (person-labeled in both arms, FT more confidently so);
   nothing in the evidence predicts a second epoch changes that.
3. The fidelity and range-dependence claims currently rest on two
   windows. Multi-window generalization evidence dominates deeper
   training on a single behavior, both scientifically and for any
   paper claim.
4. Cost: trainval FT on the 22G A10 is slow and OOM-prone (see the
   2026-07-12 OOM pathology record).

## Revisit condition
If multi-window results confirm the fidelity effect and a stronger
lever is needed, the second epoch returns as a fidelity-endpoint
hypothesis test: endpoints are candidate-window class fidelity via
the rescoring harness and the far-entry front-view label. Before any
resume, raise checkpoint_total_limit (epoch-1 checkpoints were
deleted at limit 3).

## Claim boundary
Decision record only; no new measurements.
