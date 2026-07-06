# DriveLoop / DriveDreamer-2 Handoff

Last updated: 2026-07-03

This is the main server handoff for the DriveLoop / DriveDreamer-2 research project. It supersedes the older handoff that still described the project as blocked on processed nuScenes setup and before the P0 runtime-surface work.

## Project Goal

Build DriveLoop on top of DriveDreamer-2. DriveDreamer-2 is treated as a fixed video-generation backend. DriveLoop adds a research loop around it: prompt / structured condition -> generation -> perception or semantic evaluation -> diagnosis -> prompt / condition refinement -> regeneration.

Current engineering priority is not training DriveDreamer-2. The priority is inference-time conditioning, auditability, and rigorous claim boundaries.

## Server Location

- SSH host: root@47.245.169.139
- Project root: /data/projects/DriveLoop
- Code root: /data/projects/DriveLoop/DriveDreamer2
- Conda env: driveloop
- Work branch: main, unless the user explicitly asks for another branch

Useful environment setup:

- cd /data/projects/DriveLoop
- source /data/miniconda3/bin/activate
- conda activate driveloop
- cd /data/projects/DriveLoop/DriveDreamer2
- export PYTHONPATH="$PWD:$PWD/dreamer-datasets:$PWD/dreamer-train:$PWD/dreamer-models:${PYTHONPATH:-}"

## Current P0 Status

P0 is not a final semantic-success result. The accurate status is:

- Candidate70 structural runtime/input readiness is addressed.
- Candidate70 semantic/alignment review protocol is defined and wired into the readiness gate.
- A short candidate70 GPU smoke was run with explicit approval.
- The generated candidate video was reviewed with the 9-check candidate70 semantic protocol.
- The measured prompt-video semantic result is `measured_failed`.
- `semantic_success_claim_allowed` remains false.

The correct short claim is: P0 engineering and evaluation loop is closed end-to-end, but candidate70 semantic success failed under measured review.

Latest post-GPU semantic review evidence:

- scenario_id: `candidate70_night_cut_in_gpu_smoke`
- candidate video: generated and decodable
- review pack: generated with 9 candidate70 semantic checks
- alignment score: `0.361111`
- alignment passed: `false`
- video_semantic_claim: `measured_failed`
- failed semantic checks include target motorcycle/scooter visibility, target actor tracking, visible cut-in from left, temporal lateral displacement, left/adjacent-lane-to-ego relation, and HDMap/visual maneuver alignment.

Tracked detailed snapshot:

- /data/projects/DriveLoop/DriveDreamer2/experiments/2026-07-04_current_p0_status_after_candidate70_gpu_smoke_measured_failed.md

## Latest Non-GPU Verification

Latest pasted terminal evidence:

- Full non-GPU tests: 245 passed, 1 warning
- Default readiness_status: blocked
- Default gpu_smoke_allowed: false
- Default blocker list: semantic_success_claim_not_allowed only
- runtime_motion_control_connected: true
- true_lane_geometry_replacement_available: true
- local_map_vector_hdmap_reaches_grounding_surface: true
- local_map_vector_hdmap_lane_geometry_override_verified: true
- semantic_alignment_protocol_defined: true
- semantic_alignment_required_check_count: 9
- semantic_success_claim_allowed: false

The warning is a TensorFlow / NumPy np.bool8 deprecation warning, not DriveLoop logic.

## What Changed In The Current P0 Work

### Source-bound actor motion

The previous actor-motion path could show a structural surface, but the stronger requirement was to bind the motion to the selected DD2 source samples instead of relying on relative frame indices alone.

Current evidence:

- DD2 source-bound dataset subset is used for audit-only execution.
- Relative actor-motion frame ids are mapped to source-bound sample identities.
- The mapping records cam_type, frame_idx, sample_token, scene_token, and source_record_index.
- actor_motion_frame_mapping mode is source_bound_relative_step_to_sample_identity.
- source_identity_count is 48.
- input_per_frame_count is 4.
- mapped_entry_count is 24.
- unmapped_relative_frame_idx is empty.
- Override changed counts: boxes3d 24, image_box 24, scene_description 48.

This supports a structural runtime-conditioning claim only. It is not video semantic evidence.

### Local-map-vector HDMap lane geometry replacement

The previous dry-run HDMap path only proved that a raster replacement could reach grounding_downsampler_input. That was not enough to claim true lane-geometry replacement.

Current evidence:

- A candidate HDMap replacement is built by modifying lane_divider geometry in the ego_aligned_local_map_patch coordinate frame.
- The modification occurs before camera extrinsic and intrinsic projection.
- The operation is offset_lane_divider_local_map_vector_before_camera_projection.
- Default offset is local_x_offset_m 0.0 and local_y_offset_m -1.5.
- The surface audit observes image_hdmap_override_changed true and grounding_downsampler_input_changed true.
- input_image_changed remains false.
- box_downsampler_input_changed remains false.
- The gate now treats true_lane_geometry_replacement_available as true through this local-map-vector evidence.

This supports an HDMap geometry-conditioning claim only. It is not lane-change visual-success evidence.

### Semantic/alignment protocol

The semantic-success gap is now defined as an explicit review protocol rather than an undefined next step.

Current evidence:

- candidate70 semantic/alignment protocol exists.
- The readiness gate records semantic_alignment_protocol_defined true.
- The protocol has 9 required checks covering candidate video availability, target actor visibility, actor consistency, cut-in/lane-change visibility, lateral displacement, spatial relation, road context, HDMap visual consistency, and control-binding claim boundaries.
- The generated manual report template defaults to status not_measured.
- semantic_success_claim_allowed remains false.

This supports only a protocol-definition claim. It is not measured semantic success.

## Important Files

Main handoff file:

- /data/projects/DriveLoop/DriveDreamer2/HANDOFF_DRIVELOOP.md

Current detailed status snapshot:

- /data/projects/DriveLoop/DriveDreamer2/experiments/2026-07-03_current_p0_status_after_semantic_alignment_protocol_gate.md
- /data/projects/DriveLoop/DriveDreamer2/experiments/2026-07-03_current_p0_status_after_local_map_vector_hdmap_replacement_gate.md

Experiment records:

- /data/projects/DriveLoop/DriveDreamer2/experiments/2026-07-03_p0_candidate70_source_bound_actor_motion_identity_fix.md
- /data/projects/DriveLoop/DriveDreamer2/experiments/2026-07-03_p0_candidate70_local_map_vector_hdmap_replacement_gate.md

Key implementation and test files in the current working tree:

- dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_tester.py
- driveloop/backends/drivedreamer2.py
- driveloop/dd2_override.py
- scripts/run_candidate70_gpu_readiness_gate.py
- scripts/run_candidate70_hdmap_lane_geometry_replacement_builder.py
- scripts/run_candidate70_hdmap_lane_geometry_replacement_surface_audit.py
- scripts/run_candidate70_semantic_alignment_protocol.py
- tests/test_actor_motion_surface.py
- tests/test_candidate70_gpu_readiness_gate.py
- tests/test_candidate70_hdmap_lane_geometry_replacement_builder.py
- tests/test_candidate70_hdmap_lane_geometry_replacement_surface_audit.py
- tests/test_candidate70_semantic_alignment_protocol.py
- tests/test_dd2_override.py

## Current Claim Boundary

Allowed claims:

- Candidate70 source-bound actor motion is connected to the DD2 runtime tensor surface via sample-identity matched per-frame boxes3d append.
- Candidate70 local-map-vector HDMap lane-geometry replacement reaches the DD2 grounding surface.
- Runtime motion and true lane-geometry structural blockers are no longer the active default gate blockers.
- The default gate is blocked only by semantic_success_claim_not_allowed.

Not allowed claims:

- Do not claim GPU approval.
- Do not claim generated video semantic success.
- Do not claim that lane-change or cut-in behavior is visually successful.
- Do not claim velocity tensor or displacement tensor control.
- Do not claim physically verified trajectory dynamics.
- Do not set semantic_success_claim_allowed to true without measured semantic / alignment evaluation.

## Next Recommended Work

1. Request explicit user approval before any short GPU smoke.
2. After a candidate video exists, run the post-GPU review gate and complete the semantic/alignment report.
3. Keep structural tensor evidence separate from video-generation evidence and semantic-success evidence.
3. If a GPU smoke is desired, request explicit user approval first.
4. If GPU smoke is approved and runs, initially claim only candidate video generated, then run review before any semantic-success claim.
5. Before commit, inspect git status and diff carefully because the current working tree contains intentional tracked modifications and untracked new scripts / tests / experiment records.

## Do Not Commit

Do not commit pretrained models, hf_cache, data, exp outputs, pem files, HuggingFace tokens, or downloaded model weights.

## Update 2026-07-07 (closed-loop comparison milestone)

- Perception zero-detection root cause fixed (ultralytics API + composite
  layout); candidate70 perception score 0.0 -> 0.468 measured.
- Eq.(10) control coverage and Eq.(5) task utility implemented and wired
  (opt-in via DriveLoopConfig.use_task_utility).
- Refiner escalation ladder guarantees a novel prompt per retry round.
- Mini baseline-vs-closed-loop comparison completed on GPU:
  acceptance 3/5 -> 5/5, mean J 0.783 -> 0.971; see
  experiments/2026-07-07_baseline_vs_closed_loop_mini_comparison.md
- Manual alignment review of m3/m4 accepted videos is still required before
  any semantic-success claim.

## Update 2026-07-07 (paper-formula completion)

All Sec. 3 formulas now have implementations: Eq.5 utility, Eq.10 control
coverage, Eq.14 post-processing (fog_overlay, opt-in), Eq.18 intent guard.
BoT-SORT tracking path added (detector-provided track ids, per-view reset).
BLIP captioning wired for image/sketch/video grounding (audio was already
Whisper). Full suite 350 passed. Paper Sec. 4 draft written from the mini
comparison; Sec. 3 wording on BoT-SORT is now backed by implementation.
Remaining: manual alignment review of m3/m4 accepted videos, scenario-family
expansion beyond candidate70.

## Update 2026-07-07 (final for this session)

- Target-label leakage found and fixed (ego references no longer expand the
  detection target set); v2 comparison numbers are invalid.
- v3 (post-fix, tau=0.7): open loop = prompt-only closed loop = saturated
  ablation (3/5). Prompt refinement alone cannot move detector evidence here.
- v4: structured-condition escalation (per-frame boxes3d proximity/size,
  levels 1-3) recovers m3 (S_perc 0 -> 0.536, accepted at attempt 2);
  final 4/5 vs open-loop 3/5, mean J 0.632 -> 0.685. m4 remains failed.
- Full suite 361 passed. Paper Sec. 4 numbers should come from
  experiments/2026-07-07_v4_structural_escalation_result.md.
- Open problems: m4 recovery (source rebinding), scenario-family expansion,
  manual review of the new m3 attempt-1 video.

## Session handoff 2026-07-07 (quality-improvement phase, IN PROGRESS)

### Current state
- Full test suite: 369 passed. All paper Sec.3 formulas implemented
  (Eq.5 with video-derived auto S_ctrl, Eq.10, Eq.14, Eq.18), refiner has
  three escalation levers: prompt ladder -> structural (boxes3d
  proximity/size, absolute geometry bases) -> source rebinding
  (candidate window offset). Target-label leakage fixed (ego references).
- Valid experiment data (strict motorcycle targets, tau=0.7):
  - exp_v5_open_loop: 0/5 accepted, best J 0.300-0.631
  - exp_v5_closed_loop: 4/5 accepted at attempt 2 (structural level 1),
    J 0.746-0.851; m4 fails (S_perc 0 even with rebind offset 1)
  - exp_v5_closed_loop_saturated (rerun after ablation gate fix f4d7035):
    0/5, identical to open loop -> gains come from feedback content.
  - exp_v5_closed_loop_saturated_INVALID: discard (pre-gate-fix run).
  - v1/v2/v4 comparison numbers are INVALID (leakage / superseded).

### Decision by user
- Do NOT write paper Section 4 yet. Absolute video quality is not
  acceptable (S_perc 0.6-0.7, maneuvers unverified). Goal: metric-passing,
  research-grade videos first.

### Running right now
- Geometry calibration sweep (PID 304142, log /tmp/exp_geo_sweep.log):
  9 combos lateral_base {3.2,4.5,6.0} x longitudinal_base {9,12,16} on the
  m1 prompt, single-pass each, output outputs/driveloop/exp_geometry_sweep.
  Hypothesis: current default (8m lateral / 18m ahead) places the injected
  motorcycle two lanes away at frame edge; adjacent-lane geometry should
  raise S_perc substantially.

### Next steps (in order)
1. Read exp_geometry_sweep/summary.md, pick argmax-S_perc geometry, set it
   as the default in build_actor_motion_surface_plan (and rebase the
   escalation ladder around it).
2. Rerun three arms (v6) with calibrated geometry; target S_perc >= 0.85
   on accepted cases.
3. Manual 9-check alignment review of best videos (maneuver visibility is
   the open semantic gap; ego is stationary in candidate70 source scene,
   consider source scenes with moving ego).
4. m4 remains failed: try larger rebinding offsets / different windows.
5. Scenario-family expansion beyond candidate70 (accident / fog / obstacle)
   for paper-scale experiments.
6. Only then rewrite paper Section 4 from v6+ numbers
   (outputs/section4_experiments.tex draft exists locally with user).

### Working agreements
- No Chinese anywhere in code or comments (enforced; scan with the CJK
  regex over git ls-files *.py).
- Anchored-patch workflow via /tmp/*.py scripts; run full pytest before
  every commit; commit messages in English; push after each milestone.
- GPU is free to use (monthly billing), but keep claim boundaries:
  perception acceptance is never semantic success; manual review gates
  semantic claims.
