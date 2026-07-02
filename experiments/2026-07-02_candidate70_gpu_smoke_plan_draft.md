# GPU Smoke Runbook v0

## Scope

This runbook is a candidate70 GPU smoke command plan draft. It must not be executed while the candidate70 readiness gate is blocked.

- Scenario: `candidate70_night_cut_in_gpu_smoke`
- Expected video: `outputs/driveloop/candidate70_night_cut_in_gpu_smoke/artifacts/candidate70_night_cut_in_gpu_smoke/iteration_00.mp4`
- Prompt: night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.

## Claim Boundary

- GPU output claim: `candidate_video_only`
- Semantic success allowed after GPU alone: `False`
- Lane-change control claim allowed: `False`
- Required before semantic claim: explicit manual/perception/VLM review report followed by prompt-video alignment evaluation

Do not claim prompt-to-video semantic success from GPU generation alone.
Do not claim visible lane change unless explicit manual, perception, or VLM review supports it.

## Step 1: Readiness Gate

Run this first. Continue only if the output reports `gpu_smoke_allowed: true`.

```bash
python scripts/run_candidate70_gpu_readiness_gate.py --accepted-prompt-selection outputs/driveloop/accepted_prompt/candidate70_accepted_prompt_v0.json --output outputs/driveloop/gpu_smoke_readiness/candidate70_gpu_readiness_gate.json
```

## Step 2: Candidate GPU Smoke

Run this only after Step 1 passes. The result is still only a candidate video.

```bash
python scripts/run_driveloop_drivedreamer2.py --prompt 'night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.' --scenario-id candidate70_night_cut_in_gpu_smoke --max-iterations 1 --target-score 0.9 --output-dir outputs/driveloop/candidate70_night_cut_in_gpu_smoke --config-name drivedreamer2_img_cond_mini_local
```

## Step 3: Post-GPU Review Gate

Run this immediately after the candidate video exists. This keeps the video status as `not_measured` and creates the review pack.

```bash
python scripts/run_post_gpu_review_gate.py --prompt 'night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.' --scenario-id candidate70_night_cut_in_gpu_smoke --video-path outputs/driveloop/candidate70_night_cut_in_gpu_smoke/artifacts/candidate70_night_cut_in_gpu_smoke/iteration_00.mp4 --output-dir outputs/driveloop/post_gpu_review_gate/candidate70_night_cut_in_gpu_smoke
```

## Step 4: Complete Review Report

Manually inspect the review pack or attach perception/VLM evidence. Edit the generated manual alignment report with explicit pass/fail evidence.

## Step 5: Alignment Evaluation

Run this only after the explicit review report has been completed.

```bash
python scripts/run_prompt_video_alignment_eval.py --prompt 'night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.' --scenario-id candidate70_night_cut_in_gpu_smoke_manual_review --video-path outputs/driveloop/candidate70_night_cut_in_gpu_smoke/artifacts/candidate70_night_cut_in_gpu_smoke/iteration_00.mp4 --alignment-report outputs/driveloop/post_gpu_review_gate/candidate70_night_cut_in_gpu_smoke/manual_review_pack/manual_alignment_report.json --output-dir outputs/driveloop/prompt_video_alignment_eval
```

## Notes

- This is a command plan draft only; it does not run GPU inference or generate video.
- Do not run gpu_smoke_candidate_generation while candidate70 gpu_smoke_allowed is false.
- The accepted prompt is selected for readiness tracking only and is not accepted_for_generate.
- Runtime motion control, trajectory runtime surface, true lane geometry replacement, and semantic success remain blocked.
- Short GPU smoke still requires explicit user approval in a separate step.

## Negative Result Policy

If the generated candidate does not show the requested behavior, record `measured_failed`. Do not hide or re-label negative results.

## Candidate70 Blockers

- `runtime_motion_control_not_connected`
- `trajectory_runtime_surface_not_connected`
- `true_lane_geometry_replacement_not_available`
- `runtime_motion_control_claim_not_allowed`
- `semantic_success_claim_not_allowed`

## Approval Boundary

- This draft is not GPU approval.
- Do not run the GPU candidate generation command until explicit user approval is given.
- Do not claim semantic success from GPU generation alone.
