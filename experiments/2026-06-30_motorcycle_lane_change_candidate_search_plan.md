# Motorcycle Lane-Change Candidate Search Plan

Date: 2026-06-30

## Goal

Align DriveLoop with the paper-level goal: given a reasonable free-form prompt, generate a video that satisfies the prompt requirements and passes explicit review scoring.

This plan does not lower the prompt requirement. It makes implicit physical and road-topology requirements explicit so the generator has a better chance to satisfy them.

## Target Prompt Family

Original prompt:

`daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video.`

Refined search prompt:

`daytime urban multi-lane road with dashed lane markings, a motorcycle in the left adjacent lane performs a visible lane change into the ego lane, panoramic multi-view video.`

Rationale:

- A visible lane change requires multiple lanes.
- A lane change should not occur across double solid center lines.
- The motorcycle should start in the left adjacent lane and visibly move into the ego lane.
- The prompt requirement remains lane-change generation; the refinement makes feasibility constraints explicit.

## Required Semantic Checks

A candidate passes only if all required checks pass:

| Check | Required | Pass Condition |
|---|---:|---|
| `object_presence.motorcycle` | yes | A motorcycle or clearly motorcycle-like rider/vehicle is visible. |
| `road_topology.multi_lane` | yes | The road visibly supports multiple lanes in the relevant direction or scene context. |
| `road_marking.lane_change_allowed` | yes | Lane marking does not visibly prohibit the requested lane change. Dashed lane marking is preferred. |
| `spatial_relation.left_adjacent_start` | yes | The motorcycle starts or is first visible in the left adjacent lane/left side context. |
| `motion.visible_lane_change_into_ego_lane` | yes | The motorcycle visibly changes lateral position into the ego lane across frames. |
| `lighting.daytime` | yes | The scene is visibly daytime. |
| `scene_type.urban_road` | yes | The scene is a road/urban driving scene. |

A candidate fails if any required check fails.

## Candidate Budget

Run at most two additional GPU candidates before reassessing.

Candidate IDs:

1. `motorcycle_lane_change_search_00`
2. `motorcycle_lane_change_search_01`

Each candidate must preserve:

- video artifact
- DD2 runtime input audit
- DD2 override audit
- post-GPU review gate output
- manual review report
- prompt-video alignment evaluation

## Review Policy

Do not claim semantic success from video generation alone.

For each candidate:

1. Generate candidate video.
2. Run post-GPU review gate.
3. Inspect video/contact sheet manually.
4. Fill explicit manual review report.
5. Run prompt-video alignment evaluation.
6. Record `measured_failed` or `measured_passed`.
7. Preserve negative results.

## Stop Criteria

Stop early if one candidate reaches `measured_passed`.

If both candidates fail, do not continue blindly. Analyze failure reasons first:

- object absent/ambiguous
- road topology wrong
- lane marking conflict
- no lateral motion
- baseline HDMap/sample mismatch
- trajectory control missing

## Known Limitations

Current system limitations remain:

- trajectory tensor control is `not_runtime_connected`
- temporal lane-change motion control is `not_verified`
- HDMap override is not verified
- static `boxes3d` / `image_box` control does not guarantee temporal motion
- runtime tensor changes do not prove video semantics

## Paper Alignment Intent

This search is intended to move toward the paper requirement: generated videos should satisfy prompt-level semantic requirements under explicit scoring.

It is not sufficient by itself unless a candidate passes the explicit semantic review.
