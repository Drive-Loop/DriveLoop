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
