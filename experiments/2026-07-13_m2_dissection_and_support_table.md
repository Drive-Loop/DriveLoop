# 2026-07-13 m2 dissection and matrix-wide support table

Zero-GPU decomposition of the four corrected v9c arms (official
anchor, ft6322 open v2, official dims1.5, ft+dims stacked) from
evaluation.metrics in each run's attempts.jsonl. Companion to the
2026-07-13 corrected matrix and stacking records.

## J identity
J = 0.2*S_intent + 0.3*S_ctrl + 0.5*S_perc reproduces every reported
J in the 20-cell matrix to three decimals (S_intent=1.0 everywhere).
S_ctrl is 0.5 in detected cells of m1/m2/m3/m5, 1.0 in detected cells
of m4 (the only full control score), and 0.0 in every cell with zero
surviving detections, where J collapses to the 0.200 intent term. A
first surviving detection therefore pays twice: it reactivates the
control term (+0.15 or +0.30) and starts S_perc.

## m2 dissection
arm     | J     | S_perc | Q_cov | support | Q_box | Q_id
anchor  | 0.546 | 0.392  | 0.250 | 2/8     | 1.0   | 0.5
ft      | 0.424 | 0.148  | 0.125 | 1/8     | 0.0   | 0.0
dims1.5 | 0.423 | 0.147  | 0.125 | 1/8     | 0.0   | 0.0
ft+dims | 0.413 | 0.126  | 0.125 | 1/8     | 0.0   | 0.0
The anchor's m2 lead is one extra surviving detection frame: it
doubles Q_cov and activates Q_box/Q_id (computed only with >=2
detections), worth ~0.12 J in one step. No arm forms a track
(dominant_track_length=1, net motion unmeasured); baseline
subtraction removes 65-76 detections per arm. m2 is not a lever
regression; it is single-detection variance at the detector floor.

## Matrix-wide support (surviving detection frames, of 8)
case | anchor | ft | dims1.5 | ft+dims
m1   | 0 | 2 | 2 | 1
m2   | 2 | 1 | 1 | 1
m3   | 1 | 1 | 1 | 2
m4   | 0 | 1 | 0 | 1
m5   | 0 | 0 | 1 | 1
Maximum support anywhere in the 20-cell matrix is 2/8; track length
never exceeds 1; motion evidence never engages. The entire corrected
matrix sits in the differential-survivor-limited regime identified in
the J-diagnosis record, now confirmed on the correctly bound window.

## Reinterpretation of the two parent records
1. Per-case J deltas ride on 0/1/2 surviving detections (+-1
   detection ~ +-0.12 J, and up to +0.37 when it reactivates the
   control term from zero). The interaction reads (m3/m5
   superadditive, m1 sub-additive, m2 regression) are below evaluator
   resolution and are downgraded to unresolved.
2. The robust reading is binary detectability (actor detected at all
   after baseline subtraction): anchor 2/5 cases, ft 4/5 (misses m5),
   dims1.5 4/5 (misses m4), stacked 5/5. Lever complementarity holds
   at this level, and the mean-J direction survives; its magnitudes
   should not be quoted without this caveat.
3. m4 detail: ft and ft+dims are identical to three decimals, and
   dims-only equals the anchor (zero detections) - the dims lever has
   no effect on m4. The m4 lift is FT restoring detectability, which
   reactivates the case's full control term (0.200 -> 0.566 = +0.30
   S_ctrl + 0.07 S_perc).
4. Headroom: every arm is capped by the Q_track floor (0.125) and
   absent motion evidence; no generation on this window has yet
   produced a 2-frame track. Raising J beyond ~0.57 requires the
   actor to persist across frames (generation side) and/or evaluator
   v10 track/motion evidence (protocol side).
5. Promotion gate update: m2 stops gating lever promotion; the gate
   becomes multi-seed replication of binary detectability (the +-1
   detection noise floor makes single-seed J comparisons
   insufficient).

## Claim boundary
Reanalysis of existing artifacts only; no new generations. Same
window/seed limits as the parent records; detectability counts are
n=5 cases at one seed.
