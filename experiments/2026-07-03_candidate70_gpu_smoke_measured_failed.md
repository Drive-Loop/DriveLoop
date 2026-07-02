# candidate70 GPU smoke measured failed

Date: 2026-07-03 server time

## Scope

Scenario: candidate70_night_cut_in_gpu_smoke

Prompt: night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.

Selected prompt id: c70_pos_001

## Result

Status: measured_failed

The GPU smoke produced a candidate video, but manual review found:

- no visible motorcycle
- no visible lane change
- no visible left-to-ego cut-in
- inconsistent top/bottom visual style and color
- generated scene appears dominated by DD2 mini baseline/sample-conditioned assets

## Evidence

Candidate video:

outputs/driveloop/candidate70_night_cut_in_gpu_smoke/artifacts/candidate70_night_cut_in_gpu_smoke/iteration_00.mp4

Manual review report:

outputs/driveloop/post_gpu_review_gate/candidate70_night_cut_in_gpu_smoke/manual_review_pack/manual_alignment_report.json

Prompt-video alignment evaluation:

outputs/driveloop/prompt_video_alignment_eval/candidate70_night_cut_in_gpu_smoke_manual_review/prompt_video_alignment_evaluation.json

Alignment evaluation summary:

- score: 0.0
- video_semantic_claim: measured_failed
- failed object_presence.motorcycle
- failed spatial_relation.left_lane_change
- failed lighting/color consistency
- failed required prompt alignment

## Runtime / routing observation

The run did not provide verified evidence that candidate70 source sample was bound into DD2 runtime.

Observed concerns:

- script entrypoint accepts prompt, scenario id, config, and batch skip, but no candidate70 source candidate id, scene token, sample token, or instance token
- DD2 backend baseline video path is fixed to outputs/drivedreamer2_img_cond_mini/000000.mp4
- backend structural summary reads the first label sample from the configured mini dataset
- runtime used mini baseline HDMap
- trajectory control remains not_runtime_connected
- true lane geometry replacement remains unavailable

This supports the failure interpretation that the output was dominated by DD2 mini baseline/sample-conditioned assets rather than verified candidate70 motorcycle cut-in control.

## Claim boundary

This result only supports:

- GPU smoke produced a candidate video
- manual review measured prompt-video semantic failure
- candidate70 motorcycle cut-in semantic success is not supported
- runtime motion control connected is not supported
- lane-change / cut-in control verified is not supported
- generated video must not be used as paper-level success evidence

semantic_success_claim_allowed: false

## Next recommended action

Do not run another GPU candidate until candidate70 source-sample binding is audited and readiness-gated.

Recommended next technical gate:

candidate70_source_sample_binding_readiness

It should verify whether DD2 runtime can target the actual candidate70 source sample / scene / frame sequence, rather than the default mini baseline sample.
