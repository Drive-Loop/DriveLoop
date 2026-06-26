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

## 2026-06-27 Structural Request Diff

Added a backend-side requested-vs-baseline structural diff.

The backend now records `dd2_structural_request_diff`, comparing:
- requested labels from `structural_input_plan.labels.values`
- baseline labels from the mini dataset label snapshot
- requested scene description from `structural_input_plan.scene_description.value`
- baseline scene description from the mini dataset label snapshot
- tensor override readiness from trace metadata

Observed mini validation diff for requested labels `pedestrian, bicycle`:
- baseline labels: `pedestrian, car`
- missing requested labels: `bicycle`
- extra baseline labels: `car`
- scene description changed: `true`
- tensor override ready: `false`

Validation:
- Added `test_drivedreamer2_backend_records_requested_vs_baseline_structural_diff`.
- Full unit test suite result: `42 passed`.

Interpretation:
This diff makes the gap between DriveLoop semantic intent and the reused mini baseline structural inputs explicit before implementing tensor-level overrides.

## 2026-06-27 Override Candidate Plan

Added a backend-side override candidate plan.

The backend now records `dd2_override_candidate_plan`, translating the requested-vs-baseline structural diff into candidate actions:
- replace text prompt when scene descriptions differ
- add requested actor labels missing from the baseline
- mark extra baseline actor labels
- decide whether box synthesis is required
- decide whether HDMap override is required
- preserve baseline sources for `image_hdmap`, `image_box`, and `boxes3d`

Observed mini validation candidate plan:
- scene description action: `replace_text_prompt`
- add actor label: `bicycle`
- mark extra baseline label: `car`
- requires box synthesis: `true`
- requires HDMap override: `false`
- control level: `candidate_plan_only`

Validation:
- Added `test_drivedreamer2_backend_records_override_candidate_plan`.
- Full unit test suite result: `43 passed`.

Interpretation:
This is the last audit layer before tensor-level structural control. It identifies what should change without yet writing boxes, image-box canvases, or HDMap tensors.

## 2026-06-27 Box Synthesis Plan

Added a plan-only `box_synthesis_plan` under `dd2_override_candidate_plan`.

The plan records:
- target tensor: `boxes3d`
- derived tensor: `image_box`
- placement policy: `front_adjacent_lane_cut_in`
- box template source: `class_default_dimensions`
- actors to synthesize from missing requested labels
- whether manual review is required
- current limitations before tensor generation

Observed mini validation plan:
- actor to synthesize: `bicycle`
- source action: `add_actor_label`
- confidence: `low`
- reason: `missing_requested_label`
- requires manual review: `true`

Validation:
- Added `test_override_candidate_plan_includes_box_synthesis_plan_for_missing_actor`.
- Full unit test suite result: `44 passed`.

Interpretation:
This is still plan-only. It prepares the exact contract needed before implementing `boxes3d` synthesis and `image_box` canvas rendering.

## 2026-06-27 Box Synthesis Draft

Added a draft-only `box_synthesis_draft` under `box_synthesis_plan`.

The draft records:
- coordinate frame: `dd2_dataset_frame_unverified`
- coordinate frame verified: `false`
- units: `meters`
- boxes3d format: `x_y_z_width_height_depth_rotX_rotY_rotZ`
- class default dimensions for bicycle, pedestrian, car, truck, and bus
- draft boxes3d entries for actors that need synthesis
- whether projection into `image_box` is still required

Observed bicycle draft:
- category: `bicycle`
- box3d: `[8.0, 1.8, 18.0, 0.6, 1.6, 1.8, 0.0, 0.0, -0.25]`
- placement policy: `front_adjacent_lane_cut_in`
- source: `class_default_dimensions`
- requires projection: `true`

Validation:
- Added `test_box_synthesis_plan_includes_draft_box_for_bicycle`.
- Full unit test suite result: `45 passed`.

Interpretation:
The project now has a concrete, auditable draft for actor-box synthesis, but it still does not write boxes into the mini dataset or render image-box canvases.

## 2026-06-27 DD2 Boxes3D Projection Contract Probe

Inspected the first sample from the DriveDreamer-2 mini validation labels.

Observed sample:
- boxes3d shape: `[14, 9]`
- boxes3d dtype: `float32`
- boxes3d format: `x_y_z_width_height_depth_rotX_rotY_rotZ`
- first box: `[-7.5167, 1.5012, 36.5252, 0.6470, 1.7780, 0.6210, 0.0, 1.7943, 0.0]`
- cam_intrinsic shape: `[4, 4]`
- all projected box mean z values are positive: `true`
- projected 2D corner min: `[181.65, 450.00]`
- projected 2D corner max: `[1425.06, 606.32]`

Interpretation:
The DD2 mini transform consumes `boxes3d` by converting them with `boxes3d_to_corners3d(..., rot_axis=1)`, cropping in 3D, projecting with `cam_intrinsic`, drawing a class-channel box canvas, and feeding the transformed canvas into `box_downsampler_input`.

This supports treating the draft frame as a DD2 processed camera-projection frame, but tensor override is still not connected. The next safe step is a validator-only check for candidate draft boxes before any dataset writing or image-box canvas rendering.

## 2026-06-27 Box Synthesis Draft Validator

Added a validator-only check under `box_synthesis_draft.validation`.

The validator checks:
- each draft box has 9 scalar values
- values are convertible to floating point
- width, height, and depth are positive
- the depth coordinate is positive
- projection validation is still pending

Current safety boundary:
- no dataset write
- no image-box canvas rendering
- no DriveDreamer-2 tensor override
- no projection execution inside the backend validator

Validation:
- Full unit test suite result: `45 passed`.

Interpretation:
The draft is now structurally auditable before any tensor-level override work. The next safe step is projection-only validation using the baseline mini sample camera intrinsic, without writing modified boxes into the dataset.

## 2026-06-27 Box Draft Projection Validator

Added projection-only validation for `box_synthesis_draft`.

The validator now propagates the baseline mini sample `cam_intrinsic` into the draft validator and performs a lightweight projection check for draft boxes.

Current validated bicycle draft:
- projection control level: `validator_only`
- projection finite: `true`
- projected 2D range min: `[1336.99, 536.27]`
- projected 2D range max: `[1434.68, 660.47]`
- projection method: axis-aligned draft corners with baseline `cam_intrinsic`

Current safety boundary:
- no dataset write
- no image-box canvas rendering
- no DriveDreamer-2 tensor override
- projection validator only checks geometry feasibility

Validation:
- Full unit test suite result: `46 passed`.

Interpretation:
The draft box is now structurally valid and projection-feasible under the baseline mini camera intrinsic. The next safe step is an image-box canvas dry run that renders only an in-memory validation artifact or summary, without replacing DD2 dataset inputs.
