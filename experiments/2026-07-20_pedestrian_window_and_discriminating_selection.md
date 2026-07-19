# 2026-07-20 A pedestrian-crossing source window, and source selection that discriminates by prompt

The prompt-driven source selector (2026-07-19, select_source_from_prompt) ranked a
pool of three windows that were a homogeneous night-motorcycle-cut-in family, so
it barely separated them. This note adds the first genuinely different window -- a
night pedestrian crossing -- built with the existing, category-neutral window
pipeline, and shows selection now turns "prompt -> which source scene" from a tie
into a real choice.


## The window (candidate1409), built with no code change

The build pipeline (scan -> identity probe -> runtime subset -> no-injection
baseline) is category-neutral; the actor category is only a manual read of the
scan's label_counts and scene_description. Steps:

1. Scanned the trainval enumeration source (cam_all_train/v0.0.2, 3001 candidate
   windows) with run_dd2_batch_sampler_audit; 2519 carry pedestrians.
2. find_candidate_actor.py (new, reusable) reported candidate1409 -- scene
   "Peds waiting to cross the road, peds crossing, close-up peds" -- with fifteen
   pedestrian.adult instances present in all eight front frames. Bound the first,
   instance 08c2b79c...b6b6b, f0 sample 35fbc8a1...58279, scene 1977a1c9...9b0f.
3. run_candidate_identity_probe verified it (all_frames_have_target true).
4. build_candidate70_runtime_subset (generic; --source-candidate-id candidate1409
   --instance-token ...) built the source-bound subset (144 records, binding
   ready, batch_skip 0) from the raw trainval nuScenes at
   /mnt/driveloop_full/raw/nuscenes.
5. Rendered its no-injection baseline (official weights, bank0):
   candidate1409_baseline_official/no_injection_baseline/artifacts/iteration_00.mp4,
   binding ready, candidate candidate1409.


## Selection now discriminates

With candidate1409 in source_window_pool.json:

    prompt                                          selected        off-target
    "a pedestrian crossing ... toward the ego"      candidate1409   moto windows 0.15
                                                    (0.75)
    "night ... a motorcycle cuts in from the left"  candidate162    candidate1409 0.18
                                                    (0.78)

The requested object drives the choice: a pedestrian prompt lands on the pedestrian
window, a motorcycle prompt on a motorcycle window, and the off-target windows fall
to the object-miss floor. This is the prompt -> scene step working on real windows.


## Claim boundary and next

The window and the discriminating selection are done. Generating a *measurable
injected* pedestrian crossing is a separate step: "crossing" grounds to a motion
but is not cut_in / lane_change, so build_actor_motion_plan builds no
actor_motion_surface_plan and v10b scores it unmeasurable -- the same gate that
retired m4_intersection_approach. The no-injection baseline is a real pedestrian
scene render; a measurable injected crossing needs crossing to build a surface
plan (a lateral crossing trajectory), which is a follow-on. Next windows to widen
the pool: truck cut-in (a different actor that does cut_in, so measurable),
daytime, and fog.
