# DriveLoop Multimodal Smoke Validation - 2026-06-27

## Code State

Branch: main

Latest scope:
- Multimodal input bundle and intent adapter interface
- Placeholder image and voice understanding providers
- Rule-based multimodal intent fusion
- Intent backend tracing in API request/summary records
- DriveLoop smoke suite runner with single-scenario selection

Test command:

PYTHONPATH=. python -m pytest -q tests

Result:

32 passed

## Mock Smoke Suite

Command:

PYTHONPATH=. python scripts/run_driveloop_smoke_suite.py \
  --backend mock \
  --output-dir outputs/driveloop/smoke_suite_mock

Result:
- backend: mock
- num_scenarios: 5
- accepted: 5

Scenario summaries:
- smoke_rainy_cut_in: best_score 0.95, iterations 2
- smoke_foggy_cyclist: best_score 0.95, iterations 2
- smoke_stopped_vehicle: best_score 0.95, iterations 2
- smoke_highway_lane_change: best_score 0.95, iterations 2
- smoke_low_visibility_hazard: best_score 0.95, iterations 2

## DriveDreamer-2 Mini Smoke: Rainy Cut-in

Command:

PYTHONPATH=. python scripts/run_driveloop_smoke_suite.py \
  --backend drivedreamer2 \
  --scenario-id smoke_rainy_cut_in \
  --output-dir outputs/driveloop/smoke_suite_dd2_single \
  --max-iterations 1 \
  --target-score 0.5 \
  --config-name drivedreamer2_img_cond_mini_local

Result:
- scenario_id: smoke_rainy_cut_in
- backend: drivedreamer2
- config: drivedreamer2_img_cond_mini_local
- returncode: 0
- best_score: 0.70
- iterations: 1
- artifact: outputs/driveloop/smoke_suite_dd2_single/smoke_rainy_cut_in/artifacts/iteration_00.mp4
- artifact size: 1.2M

Condition trace:
- weather: rain
- lighting: night
- actors: car, pedestrian
- motions: crossing, cut_in
- dd2 prompt suffix: heavy rain with wet road surface and visible rain streaks

## DriveDreamer-2 Mini Smoke: Foggy Cyclist Multimodal

Command:

PYTHONPATH=. python scripts/run_driveloop_smoke_suite.py \
  --backend drivedreamer2 \
  --scenario-id smoke_foggy_cyclist \
  --output-dir outputs/driveloop/smoke_suite_dd2_foggy_cyclist \
  --max-iterations 1 \
  --target-score 0.5 \
  --config-name drivedreamer2_img_cond_mini_local

Input:
- text: urban road with unusual hazard
- image placeholder filename: foggy_night_pedestrian_crossing.png
- voice transcript placeholder: a cyclist cuts in from the left near an intersection

Result:
- scenario_id: smoke_foggy_cyclist
- backend: drivedreamer2
- config: drivedreamer2_img_cond_mini_local
- returncode: 0
- best_score: 0.55
- iterations: 1
- artifact: outputs/driveloop/smoke_suite_dd2_foggy_cyclist/smoke_foggy_cyclist/artifacts/iteration_00.mp4
- artifact size: 1.2M

Condition trace:
- weather: fog
- lighting: night
- visibility: low
- actors: pedestrian, cyclist
- relations: intersection, left
- motions: crossing, cut_in
- dd2 prompt suffixes:
  - dense fog with low visibility and reduced contrast
  - low visibility conditions with difficult object perception

## Interpretation

The mock suite verifies that the complete DriveLoop control path is stable across five representative scenarios.

The two DriveDreamer-2 mini smoke runs verify that real video artifacts can be generated from DriveLoop conditions. The second run is the key multimodal validation: placeholder image and voice inputs are converted into structured intent, grounded into scene specification, mapped into DriveDreamer-2 condition trace, and passed through the real mini backend to produce an artifact.

The current mini backend still depends on the fixed DriveDreamer-2 mini baseline structural inputs. Structured intent is recorded and mapped into condition traces, but it is not yet fully converted into tensor-level DriveDreamer-2 controls.

## 2026-06-27 ConditionControlAdapter / DD2ExecutableCondition update

Implemented a first schema-level executable condition trace inside `DriveDreamer2ConditionAdapter`.

New condition trace path:
`structured_intent -> SceneSpecification -> LongTailConditionPlan -> DriveDreamer2Condition -> executable_condition`

The new `executable_condition` payload includes:
- `schema_version`: `dd2_executable_condition.v0`
- `target_backend`: `drivedreamer2_mini`
- `text_control.prompt`
- `environment_controls`: weather, lighting, visibility
- `actor_controls`: actor id, category, attributes, source
- `relation_controls`
- `motion_controls`
- `risk_controls`: long-tail tags and executable controls
- `trace_metadata`: current structural-control readiness and limitations

Validation:
- Added `test_condition_adapter_builds_executable_condition_schema`.
- Full unit test suite result: `35 passed`.

Current limitation:
This is still schema-level structural control. It does not yet drive DriveDreamer-2 actor boxes, trajectories, or HDMap tensors. The mini backend still depends on mini dataset structural inputs.

## 2026-06-27 Executable Condition Logging Follow-up

Added explicit executable-condition logging for experiment inspection.

Updates:
- DriveDreamer-2 backend metadata now records:
  - `dd2_prompt`
  - `dd2_executable_condition`
  - `dd2_condition_schema_version`
  - `dd2_tensor_control_ready`
- Smoke suite summaries now expose top-level:
  - `condition_trace`
  - `executable_condition`
- Executable actor controls now canonicalize actor labels for backend-facing control:
  - `cyclist` -> `bicycle`
  - original category is preserved as `source_category`

Validation:
- Added DriveDreamer-2 backend metadata coverage.
- Added smoke-suite summary condition trace coverage.
- Added executable actor category canonicalization coverage.
- Full unit test suite result: `38 passed`.

Interpretation:
The DriveLoop trace is now easier to audit from both API-style summaries and smoke-suite experiment files. The executable condition remains schema-level only; tensor-level actor box, trajectory, and HDMap conditioning are still future work.

## 2026-06-27 Mini Structural Input Plan

Added a plan-only mapping from `executable_condition` to DriveDreamer-2 mini structural inputs.

New field:
`executable_condition.structural_input_plan`

The plan records:
- `target_dataset`: `drivedreamer2_mini`
- `control_level`: `plan_only`
- `scene_description`: sourced from `text_control.prompt`
- `labels`: sourced from canonical `actor_controls.category`
- `image_hdmap`: currently reused from the mini dataset baseline
- `image_box`: currently reused from the mini dataset baseline
- `boxes3d`: currently reused from the mini dataset baseline

Validation:
- Added `test_executable_condition_includes_mini_structural_input_plan`.
- Full unit test suite result: `39 passed`.

Interpretation:
This adds an auditable bridge from semantic DriveLoop controls to the concrete structural input names used by the mini DriveDreamer-2 backend. It is still plan-only and does not yet override tensors.

## 2026-06-27 Backend Structural Plan Metadata

Added backend-side metadata for the mini structural input plan.

DriveDreamer-2 backend generation metadata now records:
- `dd2_structural_input_plan`
- `dd2_structural_control_level`

Validation:
- Added `test_drivedreamer2_backend_records_structural_input_plan_metadata`.
- Full unit test suite result: `40 passed`.

Interpretation:
The mini backend still does not override structural tensors. This update only makes the plan visible at the backend boundary, so future tensor-control work can compare requested semantic controls against the exact baseline structural inputs being reused.

## 2026-06-27 Baseline Structural Snapshot

Added a lightweight DriveDreamer-2 mini baseline structural snapshot at the backend boundary.

The backend now records `dd2_baseline_structural_snapshot`, including:
- mini dataset directory
- top-level dataset config summary
- labels config summary
- images LMDB config summary
- HDMap LMDB config summary
- first label sample summary:
  - `scene_description`
  - `boxes3d_shape`
  - `boxes3d_dtype`
  - `ori_labels3d_count`
  - `ori_labels3d_preview`
  - `labels3d_count`
  - `labels3d_preview`

Observed mini validation snapshot:
- dataset: `/data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_val/v0.0.2`
- labels data size: 2820
- images data size: 2820
- hdmaps data size: 2820
- first sample boxes3d shape: `[14, 9]`
- first sample boxes3d dtype: `float32`

Validation:
- Added `test_drivedreamer2_backend_records_baseline_structural_snapshot`.
- Full unit test suite result: `41 passed`.

Interpretation:
This snapshot does not read or rewrite LMDB image/HDMap payloads. It records enough baseline structure to compare future DriveLoop tensor overrides against the current mini dataset inputs.
