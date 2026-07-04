# DD2 Audit-only Motorcycle Cut-in Preflight

Date: 2026-07-04

## Evidence

- backend: DriveDreamer-2 audit-only
- scenario: `dd2_audit_only_motorcycle_cut_in_preflight`
- runtime audit: `outputs/driveloop/dd2_audit_only_motorcycle_cut_in_preflight/artifacts/dd2_audit_only_motorcycle_cut_in_preflight/dd2_runtime_input_audit_00.json`
- paper alignment report: `outputs/driveloop/dd2_audit_only_motorcycle_cut_in_preflight/artifacts/dd2_audit_only_motorcycle_cut_in_preflight/paper_alignment_report_00.json`
- history: `outputs/driveloop/dd2_audit_only_motorcycle_cut_in_preflight/history.jsonl`
- audit_only: `True`
- prompt_embed available: `True`
- box_downsampler_input available: `True`
- img_cond available: `True`
- stage 3 status: `text_and_plan_only`
- tensor_control_ready: `False`
- structural_control_level: `runtime_surface_contract`
- requested labels: `['motorcycle']`
- baseline labels: `['pedestrian', 'car']`
- missing requested labels: `['motorcycle']`
- override candidate available: `True`
- override control level: `tensor_override_runtime`

## Result

This run verifies that DriveLoop can reach the DriveDreamer-2 runtime audit path with an isolated baseline output directory. It records runtime prompt override and DD2 input tensor/surface audit evidence without generating video.

## Claim Boundary

This is not DD2 video semantic success evidence. The run used audit-only mode, skipped inference, produced no video, and still reports `tensor_control_ready=false`. It supports backend reachability and runtime audit evidence only.

## Safety Check

- default baseline video preserved: `/data/projects/DriveLoop/outputs/drivedreamer2_img_cond_mini/000000.mp4`
- isolated baseline video generated: false
