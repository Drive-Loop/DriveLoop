# Candidate70 Boxes3D Probe Audit-Only Result

Date: 2026-07-03 server time

## Scope

This note records the candidate70 non-GPU boxes3d probe audit-only result after adding an explicit DriveDreamer-2 backend probe switch.

The goal was to verify the structural runtime chain:

boxes3d target append -> derived image_box canvas -> DD2 audit input path

No GPU inference was run and no video was generated.

## Command Surface Added

New non-GPU / audit-only controls:

- DriveDreamer2Backend(force_boxes3d_probe=True)
- DriveDreamer2Backend(boxes3d_probe_category="motorcycle")
- scripts/run_driveloop_drivedreamer2.py --force-boxes3d-probe
- scripts/run_driveloop_drivedreamer2.py --boxes3d-probe-category
- scripts/run_driveloop_experiment.py --force-boxes3d-probe
- scripts/run_driveloop_experiment.py --boxes3d-probe-category
- ExperimentPipelineConfig.dd2_force_boxes3d_probe
- ExperimentPipelineConfig.dd2_boxes3d_probe_category

## Run

Output directory:

- outputs/driveloop/experiment_pipeline_candidate70_boxes3d_probe_audit_only/

Source-bound runtime dataset:

- /mnt/driveloop_full/processed/nuscenes/v1.0-trainval/candidate70_source_bound/cam_all_train/v0.0.1

Source binding:

- source_candidate_id: candidate70
- instance_token: 21cdc9f24c614a6197fd044379697197
- dd2_batch_skip: 0
- identity_summary_path: outputs/driveloop/candidate70_converter_identity_probe/cam_front_8/v0.0.1/labels/summary.json

## Evidence

Primary artifacts:

- outputs/driveloop/experiment_pipeline_candidate70_boxes3d_probe_audit_only/run/candidate70-boxes3d-probe-audit-only/result.json
- outputs/driveloop/experiment_pipeline_candidate70_boxes3d_probe_audit_only/run/candidate70-boxes3d-probe-audit-only/case_summary.json
- outputs/driveloop/experiment_pipeline_candidate70_boxes3d_probe_audit_only/run/candidate70-boxes3d-probe-audit-only/artifacts/dd2_runtime_input_audit_00.json
- outputs/driveloop/experiment_pipeline_candidate70_boxes3d_probe_audit_only/run/candidate70-boxes3d-probe-audit-only/artifacts/paper_alignment_report_00.json
- outputs/driveloop/experiment_pipeline_candidate70_boxes3d_probe_audit_only/run/candidate70-boxes3d-probe-audit-only/artifacts/dd2_override_audit_00.jsonl

Observed evidence:

- override_candidate_plan.force_boxes3d_probe: true
- override_candidate_plan.boxes3d_probe_category: motorcycle
- override_candidate_plan.requires_box_synthesis: true
- override_json.boxes3d.mode: append
- override_json.image_box.mode: derive_from_boxes3d_after_override
- dd2_override_audit.changed_counts.boxes3d: 48
- dd2_override_audit.changed_counts.image_box: 48
- override audit line count: 48
- override audit entries append one motorcycle boxes3d entry
- override audit entries mark image_box_expected_changed: true
- no mp4 artifact was produced

## What This Proves

This proves a candidate70 source-bound DD2 audit-only runtime path can apply a target motorcycle boxes3d append and produce changed derived image_box conditioning.

It upgrades the previous status from runtime surface observation to a verified audit-only structural tensor override for boxes3d/image_box.

## What This Does Not Prove

This does not prove:

- GPU generation success
- generated video semantic success
- motorcycle cut-in success in video
- temporal trajectory control
- runtime motion control
- true lane geometry replacement
- HDMap override success
- paper experiment success

The inserted box uses a draft placement policy and still requires manual/geometric review before any stronger claim.

## Claim Boundary

semantic_success_claim_allowed: false
gpu_smoke_allowed: false
does_not_generate_video: true
does_not_run_gpu: true
runtime_motion_control_connected: false
trajectory_runtime_surface_connected: false

## Next Work

1. Keep this result as structural control evidence only.
2. Add or update readiness/status gates so candidate70 can distinguish:
   - source binding ready
   - boxes3d/image_box structural override ready
   - trajectory/motion still not connected
   - semantic success still disallowed
3. Do not run GPU until a new readiness gate explicitly clears remaining blockers and the user approves.
