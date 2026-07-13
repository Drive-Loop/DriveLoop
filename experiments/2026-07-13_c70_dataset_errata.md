# 2026-07-13 Errata: v9-protocol reruns used the wrong dataset

Root cause of the anchor-vs-archive break and of every candidate70
binding failure in today's reruns: the v9 protocol runs against the
source-bound candidate70 subset dataset at
/mnt/driveloop_full/processed/nuscenes/v1.0-trainval/candidate70_source_bound/cam_all_train/v0.0.1
(144 records, candidate_start_count 1), passed via
--baseline-dataset-dir. Today's reruns omitted that flag, so they ran
on the full mini val dataset (2820 records): the binding could not
match the candidate70 tokens
(no_dd2_candidate_contains_requested_source_tokens), real-track mode
never engaged, and injection fell back to the synthetic path on an
unrelated window (batch 0).

Corrections:
1. 2026-07-13_v9_protocol_ft6322_three_arms_bank0.md, finding 3: the
   attribution of the archive break to post-v9 code drift (sampler
   resample rewrite) is RETRACTED. git diff a84bf0e..9038445 shows no
   changes under driveloop/; the break was the missing dataset flag
   in the rerun commands. The FT-vs-official same-day comparison
   remains internally controlled (both arms equally misconfigured),
   but all absolute J values in that record belong to the wrong
   window and must not be compared to v9 archive numbers.
2. 2026-07-13_j_metric_diagnosis_and_steps_falsification.md: the J
   decomposition mechanism reading stands, but the 50-step
   falsification and all numbers were measured on the wrong window
   via the synthetic path; downgraded to pending re-measurement under
   the corrected dataset.
3. The real-track dims-scale knob (6efcb35) has not been exercised
   yet: with the wrong dataset, real-track never ran. To be tested in
   the corrected rerun.
4. Process rule going forward: reproduction commands for source-bound
   runs MUST carry --baseline-dataset-dir taken from the original
   run's binding block (dataset_dir), and binding ready=true plus the
   real-track marker are mandatory preflight gates before spending
   GPU on candidate70 protocol arms.

Claim boundary: errata only; no new measurements.
