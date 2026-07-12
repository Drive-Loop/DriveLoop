# 2026-07-13 Far-entry verdict: released weights vs trainval FT step_6322

Question: does the 1-epoch trainval FT checkpoint fix the far-entry
class-fidelity failure (motorcycle degrading to a person-like figure)
documented on 2026-07-09 (v4, 55 m start)? Verdict: no.

## Driver identification (closes the v3/v4/v5 question)
scripts/run_driveloop_drivedreamer2.py is the only CLI wired to
DriveDreamer2Backend; run_driveloop_mock.py is mock by construction,
run_driveloop_experiment.py defaults to --backend mock, and runner.py /
experiment_pipeline.py have no CLI. The v3/v4/v5 artifact trail
(history.jsonl + dd2_override_audit) matches this driver, and the v4
history carries --sample-token 8092909473464f80b9f791a4d31ddcb8 in its
runtime sample selector.

## Setup
Window: mini val batch 13 (--dd2-batch-skip 13), clean window scene
325cef68 frames 96-117, --sample-token 8092909473464f80b9f791a4d31ddcb8.
Profile: DRIVELOOP_EGO_INJECTION=1, DRIVELOOP_EGO_FAR_ENTRY=35 (55 m
start), tangent heading and FOV cull at defaults, seed 6666 with
SEED_OFFSET=0, --max-iterations 1, daytime base prompt with identical
long-tail suffixes in both arms.
Arms: released gligen weights vs DRIVELOOP_DD2_WEIGHT_PATH pointing at
checkpoint_epoch_1_step_6322. Dirs:
outputs/driveloop/far_entry_verdict_{official,ft6322}_v2.

## Controls verified before review
Both arms: source_sample_binding requested and ready;
actor_motion_frame_mapping available, mapped_entry_count 8; ego entries
accepted 8 on cam_front with front_left center_outside_image_culled
(measured on the official arm; FT arm identical by conditioning hash) -
the same chain as the 2026-07-09 runs. Conditioning byte-identical
across arms: img_cond c73477f5..., prompt_embed 258f223c...,
box_downsampler_input 0af11c09... Any visual difference is attributable
to weights alone.

## Verdict (human review, single reviewer, frame-stepped)
Both arms render the injected actor as a person-like figure in the
roadway; no frame in either arm shows motorcycle features (wheels,
handlebars, riding posture). Appearance reads as in-place emergence with
scale growth, consistent with the along-axis geometry noted on
2026-07-09. The released-weights arm reproduces the v4 failure mode at
HEAD; trainval FT step_6322 does not improve far-entry class fidelity.
The binding lever for synthetic-path class fidelity at distance remains
checkpoint capability / longer frame_num.
Claim boundary: one window, one seed, one reviewer; no perception or
semantic claims.

## Negative control and guardrail gap
A first arm pair ran without --sample-token: the ego surface silently
disengaged (actor_motion_frame_mapping.available=false, reason
no_source_bound_sample_identity_mapping, per_frame_append_ego empty),
yet the runner returned passed, score 0.8, with only a limitations note
(actor_motion_surface_not_applied). Those runs
(far_entry_verdict_{official,ft6322}, no _v2 suffix) are kept as a
negative control: quasi-clean windows plus the static draft box only.
Action item: hard-fail, or at least raise a top-level flag, when
DRIVELOOP_EGO_INJECTION=1 and the frame mapping is unavailable.

## Review-protocol lesson
Normal-speed playback missed the mid-road figure twice; frame stepping
found it immediately. Frame-stepped review is now required for
injection runs; earlier quick-look "no injection visible" reads are
superseded.

## Secondary observations (not claims)
- ft6322_v2 shows a cone-like artifact at the figure's base, absent in
  the released-weights arm.
- ft6322 v1 (negative control) showed end-of-clip darkening at normal
  playback.
- v1 quick-look suggested the static box rendered visibly only under FT
  weights; superseded methodology, needs a frame-stepped recheck before
  any claim.

## Queue implications
The second-epoch decision (resume=True) should not expect far-entry
class-fidelity gains from more of the same FT; its case rests on the
evaluator-scored axes (candidate70 three-arm rerun, yolov8x@0.20 with
baseline differential and the v9 open-arm tau).
