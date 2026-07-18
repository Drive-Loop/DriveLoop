# 2026-07-18 Landing three decided changes: construction D (+28.5%), the lighting removal, and the "approaching" primitive

Three questions that the S_ctrl construction record (34e3d12) and the m4 parse-failure
record (b604a4c) left open were decided and landed this segment. None of the three
moves a number in the paper; all three are settled by arithmetic on the archived
metrics plus a re-grounding of the archived requests, with no GPU and no run
re-executed. Two commits:

    809fd1f  construction D (+28.5%) and the lighting-channel removal
    c95d5f4  the "approaching" motion primitive

Full suite green after each: 490 passed at 809fd1f, 492 at c95d5f4.


## 1. What landed

### 809fd1f -- control_visibility.py

**target_motion is scored whenever perception was measured** (construction D), not
only when the grounder parsed a motion word. The `if scene_spec.motion_primitives:`
guard is removed. An empty motion_primitives is almost always a parse failure -- m4's
prompt requests a motion the keyword table cannot read -- and sparing such a case the
channel gave it a single channel to divide by, which is the entire mechanism of the
+38.1 percent lever. Scoring m4 from the measurement its run already archived moves the
candidate70 FT lever to +28.5 percent.

**The lighting channel is removed**, listed as unmeasured like weather. Under
source-bound generation illumination is locked to the source scene, so the brightness
threshold on the selected view (`_NIGHT_BRIGHTNESS_MAX = 90.0`, now deleted) scored the
source's light, not the arm's. The dead brightness-emission code in
composite_perception.py (after the `return` in `_maneuver_direction_check`, 99ee69a4)
is kept, as it is the evidence behind the finding.

### c95d5f4 -- grounding.py

A sixth motion primitive, `"approaching": ["approaches", "approaching"]`, matched on the
verb forms only, not the bare noun. It is deliberately not cut_in: actor_motion and
condition_adapter gate trajectory and maneuver-suffix construction on cut_in/lane_change,
so "approaching" builds no boxes3d trajectory, no maneuver suffix, and no prompt rewrite.
It records that a motion was requested without asserting which maneuver.


## 2. The evidence, per gate

**D equals C3, per case, to 1e-9 (block 217, all seven arms replayed).** The three
candidate70 arms' C1 S_ctrl reproduces the archived S_ctrl on all attempts (0
mismatches). Under D the only cell that moves is m4 on the ft6322 arm, from 1.0 to 0.5;
the other fourteen cells are unchanged. Recomposed J from the archived weights:

    construction   anchor       ft6322       lever
    C1             0.310479     0.428905     +0.118425  (+38.1%)
    D              0.310479     0.398905     +0.088425  (+28.5%)

**The lighting removal is score-inert on the paper's numbers (block 217).** Block 216
found 86 archived attempts across 9 runs still carrying perception_best_view_brightness
(the channel was live before 99ee69a4, 2026-07-07). Block 217 confirmed those 9 carrier
runs -- exp_geometry_sweep{,_v2}, exp_v5_*, exp_v6_* -- are disjoint from the three
candidate70 arms, and that the four exp_v10w candidate162/2216 arms carry no brightness.
So removal changes no arm's archived S_ctrl.

**The "approaching" primitive changes m4's grounding and nothing else on the archive
(block 218 section 4).** Replaying m4's real archived request under three keyword
surfaces:

- surface A (approach -> cut_in) builds an 8-frame boxes3d trajectory (lateral offset
  -1.6 -> +0.8 across the ego lane), adds motorcycle_cut_in and left_lane_relation tags,
  flips actor_motion_plan.available and tensor_control_ready to True, and rewrites the
  DD2 text prompt with two appended suffixes ("a motorcycle performs a visible cut-in
  maneuver near the ego vehicle, the target actor starts from the left adjacent lane").
  That is a different video on two axes: structural conditioning and prompt text.
- surface C (a new "approaching" primitive) propagates the name into six fields and
  changes nothing structural: no trajectory, no tags, no coverage change, no prompt
  rewrite. The archived videos are unchanged.

C was chosen. An intersection approach toward the ego path need not be a lateral
maneuver, so fabricating a cut-in trajectory (A) would assert a maneuver the prompt does
not state, and would require a re-render.

**source_ranking is not in play (block 218 section 3).** All 15 arm attempts ran
selector_type=none (NoOpSourceSelector), 0 missing. source_ranking.py reads
motion_primitives and could otherwise let a primitive's name move the bound source
window; it cannot here, so section 4's diff is complete.


## 3. The five candidate70 cases are not duplicates (block 218 section 5)

    case  motion        weather/visibility     generation-prompt maneuver suffix
    m1    cut_in        clear night            "performs a visible cut-in maneuver"
    m2    cut_in        rainy night            "performs a visible cut-in maneuver"
    m3    lane_change   clear night            "performs a visible lane change"
    m4    (unparsed)    clear night            NONE
    m5    cut_in        foggy night, low vis   "performs a visible cut-in maneuver"

The three cut_in cases differ on the weather/visibility axis, not the maneuver. All five
bind one source window (block 204), so the requested weather and lighting are
prompt-level requests, not properties of the bound source clip. m4 is the only case
whose generation prompt carries no maneuver suffix, because its empty motion_primitives
suppressed the suffix. After c95d5f4 it grounds to ['approaching'] but still receives no
suffix, because "approaching" is not a lateral maneuver -- which is the honest outcome
for an under-specified "approach" prompt.


## 4. New findings

**The candidate70 anchor is three-fifths detector floor.** m1, m4 and m5 each archive
J = 0.200000 exactly, which under the weights (0.5, 0.3, 0.2) and S_intent = 1.0 forces
S_perc = 0 and S_ctrl = 0: the detector found nothing on those cases. The +38.1 / +28.5
percent denominator is 60 percent floor, not a weak baseline. This should be stated as a
detector-floor property in the paper, not read as "the anchor performs poorly".

**The utility weights were recovered, not read.** task_utility is absent from every
archived attempt in these runs, so the weights were not stored. A least-squares fit to
the anchor's five (S_perc, S_ctrl, S_intent, J) rows gives [0.500002, 0.299999, 0.2],
residual 6.6e-33, rank 3 -- a unique solution equal to UtilityWeights' source default
(0.5, 0.3, 0.2), which runner.py:156 falls back to when config passes none. The
current code does archive task_utility with weights (test_control_visibility_provenance
asserts it); these older runs predate that. The lever recomposition in block 217
hardcodes the default and gates it: each archived J is recomposed from these weights and
required to equal the stored J to 1e-9, so any attempt run under different weights would
fail rather than be silently rescored.


## Corrections

**34e3d12 is wrong that the arms are "identified by recomputing the archived means
against the record, not by the run name".** For the anchor this is false: mean J
0.310479 nominates seven runs (exp_v9_closed_loop_r3, _r4_lever, _r5, _no_escalation,
_open_loop, _seed_only, exp_v9c_official_open_anchor). Block 217a resolved it by the
per-case J vector: all seven carry one identical vector, so they are duplicates of a
single generation recorded under several run names (iteration 0 of a closed-loop run is
the open-loop generation), not different runs. The record's numbers stand; only its
identity method needs the correction that the mean nominates a class and the recorded
name selects within it. ft6322 and dims1p5 each resolve uniquely, so the sentence was
true for two of the three arms and over-generalised from them.


## Method note

Predictions this segment, recorded win or lose. Wrong four times: that a bare "approach"
keyword would ground beyond m4 (it moved exactly the 108 m4 attempts, nothing else);
that removing the lighting channel would be score-inert everywhere (86 attempts across 9
runs carried a live brightness, though none in the arms); that m1 and m4 were two scenes
(one bound source); that source_ranking needed guarding (NoOp, never wired). Right twice:
that each recorded mean hides one per-case vector, and that D reproduces C3 at the lever
+0.088425.

Four self-inflicted truncations, each caught by a gate rather than by judgement. `find
-maxdepth 8` undercounted the archive at 339 where rglob found 346. `wc -l` on a grep
missed the motion_controls read site, reporting 43 of 44. A heredoc paste dropped two
lines (302 to 300); the patch sha caught it. A base64 blob acquired homoglyph corruption
in transcription; the sha caught that too. The delivery lesson is settled: content that
passes through a hand-typed message can be corrupted, and the only byte-exact channel to
the server is `scp -i` of a file that was never retyped. Every code landing this segment
was gated on a sha computed before transfer and a `git apply --check` before apply.


## Claim boundary

Arithmetic on archived metrics plus a re-grounding of archived requests. No run was
re-executed, no GPU, no video read. "m4 repaired" means one thing: score its
target_motion channel from the measurement the run already archived. It says nothing
about whether the actor moved in the video -- the tracker read
perception_dominant_motion_over_width = -1.0 window-wide, so target_motion is 0.0 by
measurement, not by assumption. The weights are inferred by least squares, not read from
these attempts. The source-bound lighting argument rests on the source-binding
architecture and the six-view brightness invariance measured earlier, re-confirmed here
only as arm-disjointness. "approaching" changes future grounding only; re-grounding the
108 archived m4 attempts now yields ['approaching'] rather than [], so block 216's
"grounder reproduces the archive on all 579 attempts" intentionally no longer holds for
those 108, and it inherits the keyword grounder's existing ego-subject false positive
("the ego vehicle approaches" grounds a motion for the ego), which no archived prompt
triggers.
