# 2026-07-18 v10 across three windows: the FT S_perc lever does not survive, and the baselines were never lost

The 2026-07-13 v10a/v10b records established, on candidate70's bank0/bank1 arms,
that super-class detection saturates and the v9 FT lever relocates from
detection quantity to class fidelity. This note extends that to all three
windows of the current table (candidate70, candidate162, candidate2216) on
baselines that were validated by exact v9 reproduction, and reaches the same
conclusion with a sharper edge: the FT lever at S_perc does not merely collapse,
it reverses on candidate70 and is negative on candidate162.

No arm was re-rendered. The rescore re-runs YOLO on the stored arm videos
against the stored no-injection baselines; it is deterministic in weights and
confidence, so GPU and CPU give the same numbers.


## The three-window S_perc table (all seven arms reproduce v9 exactly)

Means over each arm's cases. candidate70 has five cases (m1-m5); candidate162
and candidate2216 have four (m1, m2, m3, m5). Every arm's v9 rescore reproduces
its archived S_perc to six decimals: candidate70 3/3, candidate162 2/2,
candidate2216 2/2.

    window        arm                        v9        v10a      v10b
    candidate70   official_anchor            0.100959  0.268522  0.167542
                  ft6322 (bank0_v2)          0.157810  0.240998  0.131449
                  official_dims1p5           0.159026  0.304484  0.203504
    candidate162  official_anchor            0.421911  0.419724  0.419724
                  ft6322_dims1p5             0.265479  0.265479  0.265479
    candidate2216 official_anchor            0.000000  0.069057  0.069057
                  ft6322_dims1p5             0.000000  0.100851  0.100851

FT lever (ft arm minus its window's official anchor):

    window        arm         v9         v10a       v10b
    candidate70   ft6322      +0.056851  -0.027524  -0.036093
    candidate70   dims1p5     +0.058067  +0.035962  +0.035962
    candidate162  ft6322_dims -0.156432  -0.154245  -0.154245
    candidate2216 ft6322_dims  0.000000  +0.031794  +0.031794


## What the table says

**The v9 FT lever does not survive v10, and on two windows it is not even
positive.** candidate70's ft6322 lever is +0.057 under v9 and flips to -0.028 /
-0.036 under v10a / v10b: the single-class detection count that made the FT arm
look ahead was counting evidence the super-class pooling then attributes to the
anchor as well. candidate162's FT arm is below its anchor under every protocol
(-0.15), so on the one window with non-floor signal on both arms, the fine-tuned
arm produces less perception evidence, not more. candidate2216 is detector-floor
under v9 (both arms 0.0); its small positive v10 lever is non-target super-class
residue, not actor evidence (see fidelity below).

**Class fidelity, not detection quantity, is where the arms differ.** The FT
arms detect fewer objects but a higher share of them read as the target class.
On candidate70 the ft6322 arm scores class fidelity 1.0 on its three detected
maneuver cases while the anchor scores 0.0 on three of five (its detections are
predominantly pedestrian). On candidate162 the anchor carries 0.667-0.75
fidelity (mixed target and non-target) against the FT arm's 1.0-where-present.
The v9 lever conflated "how much was detected" with "was the requested actor
rendered"; the fine-tuning changes what the detected object reads as, not how
much is detected.

**m4 is a v10a false-positive that v10b removes, on all three candidate70 arms.**
Every arm scores m4 at 0.50-0.55 under v10a with class fidelity 0.0 -- back-camera
pedestrian residue on a case whose real-track mapping is empty -- and v10b zeroes
it (perception_view_restriction_unresolved=1, because m4 has no
actor_motion_surface_plan; the "approaching" primitive from c95d5f4 builds none).
This confirms across three windows the 2026-07-13 finding that the maneuver view
restriction is a precondition for any v10 adoption, not an optional refinement.


## The baselines were never lost

Block 220 ran this rescore reading the baseline from metadata['baseline_video']
and failed v9 reproduction on candidate162 (0/8, some cells off by 0.3-0.5).
d0f8f22's own commit message states why: metadata['baseline_video'] is the DD2
tester's staging output, overwritten on every run, not the no-injection support
video, and "an auditor who read it as the baseline would subtract an arm against
its own render". Block 220 made exactly that mistake; the warning was in the git
log, and the field was used instead of it.

The real per-window, per-weight baselines were on disk the whole time, in
dedicated directories timestamped minutes before scoring:

    candidate162 official  outputs/driveloop/v10w_candidate162_baseline_official/...   00:43
    candidate162 ft6322    outputs/driveloop/v10w_candidate162_baseline_ft6322/...     00:45
    candidate2216 official outputs/driveloop/v10w_candidate2216_baseline_official/...  00:47
    candidate2216 ft6322   outputs/driveloop/v10w_candidate2216_baseline_ft6322/...    00:49

Block 221 rescored against these and reproduced candidate162 2/2 and
candidate2216 2/2. candidate70's anchor and dims1p5 reproduced under
v9_no_injection_baseline; its ft6322 baseline is the contested one (d0f8f22: two
candidates both gave 84 detections), so block 222 swept every candidate70
baseline on disk and let reproduction adjudicate: v9_no_injection_baseline_ft6322_c70sub
reproduces 5/5, while the plain ft6322 render misses m2 (0.132011 vs the archived
0.147711). m2 is the only case the baseline choice moves; every other case is
baseline-insensitive. The c70sub baseline post-dates the anchor's scoring
timestamp, so the archive adjudicated over the timestamp guess, not the other
way round.


## Corrections

An earlier conclusion in this investigation -- that the no-injection baselines
were unrecoverable and that reproducing them required a GPU re-render from the
source datasets -- was wrong. The baselines were persisted in dedicated
directories all along. The error was reasoning from the archive defect (d0f8f22
fixed baseline persistence, so pre-fix runs lack perception_baseline_video_resolved)
to "the baseline artifact does not exist", without searching for the baseline
render outputs by name. Searching for *no_injection_baseline* surfaced them
immediately. The arms differ by weights (the ft6322 checkpoint,
exp/drivedreamer2_img_cond_trainval_ft_local/models/checkpoint_epoch_1_step_6322),
not by config: all seven share config_name drivedreamer2_img_cond_mini_local, so
the arm identity is carried entirely by the loaded checkpoint, which the
generation metadata does not record.


## Method note

The v9-reproduction preflight is the load-bearing gate. It failed loudly on
candidate162 under the wrong baseline (block 220), which is what forced the
baseline audit rather than letting a plausible-but-wrong number through. When the
gate was turned from abort-on-first-miss to report-per-arm (block 221), it
localised the failure to candidate70 ft6322 alone, which block 222 then resolved
by sweep. A gate that reproduces the archive is worth more than a gate that
merely runs.


## Claim boundary

S_perc level only. J is not recomposed here, and doing so raises a caliber
question left open: v10's super-class detection changes perception_detection_count,
which feeds S_ctrl's object_presence channel, so adopting v10 for S_perc forces a
decision on whether object_presence counts the super-class or stays target-class.
That decision is not made here.

candidate2216 is detector-floor at v9 on both arms; its v10 lift is non-target
super-class residue (class fidelity 0.0 on every case), so its positive v10 lever
is not a fine-tuning effect and must not be read as one. The rescore is
deterministic in weights and confidence (yolov8x.pt, 0.20); GPU and CPU agree.
The v10 numbers use the fine-tuned checkpoint for the FT arms and the base SVD
weights for the official arms; the reproduction of the archived v9 S_perc on all
seven arms is the evidence that the correct weights and baselines were paired.
