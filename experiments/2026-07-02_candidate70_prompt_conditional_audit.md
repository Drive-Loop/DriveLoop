# Candidate70 Prompt-Conditional Candidate Audit

Date: 2026-07-02

## Scope

This note records non-GPU prompt-conditional candidate audits for candidate70.

It does not claim prompt-to-video semantic success, runtime motion control, HDMap lane geometry override, lane-change semantic success, or paper-level success.

## Candidate

- candidate: candidate70
- candidate_id: nuscenes_train_candidate70_cam_front_9935
- split: train
- front_start_index: 9935
- scene: scene-1100
- map: singapore-hollandvillage
- selected_view: cam_front
- contact sheet: outputs/driveloop/source_visibility_audit/motorcycle_lane_change_train_candidate_70_images/candidate_70_source_cam_front_contact_sheet.jpg

## Candidate Metadata

Candidate70 was represented with:

- object_tags: motorcycle, scooter
- motion_tags: cut_in, lane_related
- environment_tags: night, dark
- scene_tags: urban, street, intersection
- selection_reason_tags: motorcycle, cut_in

Source evidence from the prior visibility audit:

- same raw instance token across all audited CAM_FRONT frames
- raw_instance_token: 21cdc9f24c614a6197fd044379697197
- category: vehicle.motorcycle
- all_frames_have_raw_target: true
- all_frames_project_raw_box: true
- processed_delta_x: 9.9201
- processed_delta_z: -15.3396

## Audit 1: Old Daytime Accepted Prompt

Prompt:

- daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.

Result:

- status: blocked
- allowed: false
- missing_requested_support: daytime
- unrequested_selection_bias: cut_in

Interpretation:

Candidate70 must not be used for the old daytime accepted prompt. It is a night candidate and adds cut-in selection bias not explicitly requested by that prompt.

This is the desired guardrail behavior.

## Audit 2: Candidate-Compatible Suggested Prompt

Suggested prompt:

- night urban street with a motorcycle or scooter making a visible lane-change / cut-in from the left toward the ego vehicle, panoramic multi-view video.

Result:

- status: allowed
- allowed: true
- missing_requested_support: none
- unrequested_selection_bias: none
- requested_rules: motorcycle, vehicle, lane_change, cut_in, night, urban
- candidate_supported_rules: motorcycle, vehicle, lane_change, cut_in, night, urban

Interpretation:

Candidate70 is prompt-conditional for the candidate-compatible night lane-change / cut-in suggested prompt.

This prompt is only a suggestion. It cannot enter Generate unless the user explicitly accepts or edits it.

## Claim Boundary

Allowed claims:

- Candidate70 is blocked for the old daytime prompt.
- Candidate70 is allowed for the explicit night lane-change / cut-in suggested prompt.
- Candidate70 preserves accepted-prompt-driven candidate selection behavior.
- Candidate70 provides source candidate support for the suggested prompt.

Disallowed claims:

- Candidate70 proves prompt-to-video semantic success.
- Candidate70 proves runtime motion control.
- Candidate70 proves HDMap lane geometry override.
- Candidate70 proves a true lane-change into the ego lane.
- Candidate70 proves trajectory, velocity, or displacement is consumed by DD2 runtime.
- The suggested prompt has been accepted by the user for Generate.
- Candidate-support audit output proves video semantics.

## Recommended Status

- old_daytime_prompt_candidate70_status: blocked
- night_lane_change_cut_in_suggested_prompt_candidate70_status: allowed
- candidate70_candidate_support: prompt_conditional_for_suggested_prompt_only
- accepted_prompt_required_before_generate: true
- runtime_motion_control_connected: false
- semantic_success_claim_allowed: false

## Next Step

Preserve the candidate metadata and audit outputs.

Before any GPU run, audit whether DD2 runtime consumes trajectory, velocity, displacement, or HDMap controls for this candidate-compatible prompt. Only after runtime-surface evidence exists should a short GPU candidate be considered.
