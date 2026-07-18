# 2026-07-18 The weights are a brightness pump, the source row is a usable fingerprint, and entries_preview is a trap that cost four blocks

Three results and four dead hypotheses, from six read-only probes over the same
seven arms and six no-injection baselines. The most useful of the three is the
trap, because without it written down the next person walks the same four blocks.

## 1. The weights move brightness on their own, on every window
2026-07-18_night_is_a_prompt_not_a_window.md measured one instance: the same
candidate162 source renders at 101.522 under ft6322 and 88.410 under official,
with no injection in either, and called it a confound. It is general, and 13.1
points was the smallest reading available.

Measured on the six no-injection baselines, the evaluator's own layout and
reader, mean over eight frames of each 448x256 view:

    window   source row cam_front      generated row cam_front
             official   ft6322   gap   official   ft6322    gap
    c70       56.361    56.357  -0.004  44.634    66.549  +21.915
    c162     102.199   102.199  +0.000  88.410   101.522  +13.112
    c2216    105.081   105.081  +0.000  55.925    79.353  +23.428

Over all six views of all three windows, the generated row moves between +11.75
and +39.98 and ft6322 is brighter in 18 of 18. The source row moves by exactly
0.000 on candidate162 and candidate2216 and by at most 0.011 on candidate70.

Same source, no injection, one thing varied: the weights. So an absolute
brightness threshold applied to the generated row is a weights detector. The
weights are the arm axis. Its arm signal is structural, not incidental, which is
the mechanism behind the candidate2216 result in
2026-07-18_lighting_revival_imports_view_mismatch_and_threshold.md rather than a
coincidence beside it.

At the current threshold of 90.0 only candidate162's baselines straddle it
(88.410 against 101.522). candidate70 (44.6/66.5) and candidate2216 (55.9/79.4)
sit on one side. That is luck, not design: the constant was never calibrated.

Licensed by reproducing five values from the night record exactly: the source row
at 102.199 under both weight sets, 105.081, and the generated row at 88.410 and
101.522.

## 2. The source row is a fingerprint, and every arm is bound to the window its name claims
The top band's invariance under injection and under a change of weights is what
makes it usable, and section 1 measures that invariance rather than assuming it.
Applied to all 32 arm cases against the three baseline fingerprints:

    claimed window   distance to c70   to c162   to c2216
    candidate70          0.011-0.024    74.8      73.3
    candidate162         74.8           0.000-0.028  15.5
    candidate2216        73.3           15.5      0.001-0.004

Between-window distances are 15.5 to 74.8. Within-source distances are at most
0.028. The fingerprint separates by three orders of magnitude more than it needs
to, and nothing sits near the boundary. Every case of every run matches its own
window, and every run is single-source.

The handoff's per-view source fingerprints reproduce: candidate70 recomputes to
[46.286, 56.357, 63.268, 32.903, 53.841, 39.247] against the quoted [46.3, 56.4,
63.3, 32.9, 53.8, 39.2], candidate162 to 102.199 against 102.2, candidate2216 to
105.081 against 105.1. They came from these six baseline videos.

This closes a caveat. 2026-07-18_c70_subtraction_probe.md records that "both
candidate baselines yield 84 detections ... the fingerprint does not separate
them". Brightness does: their generated rows differ by up to 21.915 while their
source rows differ by 0.011. They are distinct videos. This does NOT say which
baseline belongs to which arm.

## 3. candidate2216's baseline renders dark, and it does not matter
    window   source   its own baseline   its own arm    baseline/source  arm/source
    c70      56.361   44.634             52.8 - 55.7    0.79             0.94-0.99
    c162    102.199   88.410             92.4 - 95.0    0.87             0.90-0.93
    c2216   105.081   55.925             90.5 - 94.9    0.53             0.86

candidate2216's arm renders at 86 percent of its source, in line with the other
two. Its baseline renders at 53 percent. Nothing in the archive explains it.

It does not touch any conclusion. candidate2216's arms record moto_raw 0 on 8 of
8 before any subtraction (2026-07-18_three_window_metric_regimes.md finding 1),
so S_perc 0, S_ctrl 0 and J 0.200000 do not pass through the baseline. The
baseline is used for detection subtraction, and on this window there is nothing
to subtract.

It does touch one inference. That record's finding 3 reads the baselines' 12 and
9 detections, against 52/54 on candidate162 and 84 on candidate70, as evidence
that the window is nearly empty to the detector. A baseline rendering at 53
percent of its source suppresses detections on its own. The counts are right; the
inference from them to a property of the window is not safe.

## 4. Four hypotheses, all dead
    the candidate2216 arms are bound to another window
        dead: fingerprint distance 0.001-0.004 to their own window
    the render parameters differ
        dead: no archived parameter distinguishes the pair on candidate2216 that
        does not also differ on candidate162. All four blobs carry
        DRIVELOOP_DD2_SEED_OFFSET '0'
    the conditioning tensors are identical, so identical inputs rendered
    differently, so something is badly wrong
        dead: img_cond's sha256 is equal baseline-to-arm on BOTH windows, which
        is correct, because injection changes boxes and not the source image.
        The mean and sum that suggested otherwise disagree at 8.1e-8 relative,
        which is float32 reduction noise. The archive stores the hash next to
        the mean and the hash is the one that settles it
    candidate2216 was rendered from an empty box condition
        dead: 19 of its 48 audit entries carry a non-empty boxes3d, and its
        cam_front entries go from one box to two under injection

## 5. entries_preview is three of forty-eight, and they are the wrong three
dd2_override_audit.entries_preview holds 3 entries against an entry_count of 48.
In all thirteen runs those 3 are the same: cam_front_left at frame_idx 0, 3, 6.
It is not a sample. It is the head of a fixed enumeration.

Two things follow, and both bit:

The injection targets cam_front. The preview shows cam_front_left. So the preview
cannot see the injection on any window, and any statement about where the
injection landed that is drawn from it is drawn from a view selected to miss it.

Worse, the windows sit at different frame offsets. candidate162's sample is at
frame_idx 0. candidate2216's is at 96. So on candidate2216 the preview's three
entries are not merely the wrong view, they are outside the window entirely, and
they are empty because there is nothing there. The SHA-256 of empty input that
they carry is the correct hash of an empty array, not a defect.

Read from the full file instead. dd2_override_audit_path points at it, and the
file's line count can be checked against the archived entry_count. Doing that:

    window   entries gaining a box, of 48        cam types receiving boxes3d
    c70      11   cam_front 8, cam_front_left 3  cam_front, cam_front_left
    c162      9   cam_front 8, cam_front_left 1  cam_front, cam_front_left
    c2216    10   cam_front 8, cam_front_left 2  cam_front, cam_front_left

All three windows behave the same way. Every baseline gains a box on 0 of 48 and
skips with no_per_frame_append_ego_entries 48 times, which is what a run with no
injection plan should record. Every arm skips with
no_matching_or_convertible_entries on exactly 48 minus its applied count.

## Claim boundary
Arithmetic on archived metrics, the archived override audits, and a brightness
recompute from the archived videos by the evaluator's own layout and reader. No
run was re-executed. No GPU.

The brightness recompute is gated on candidate70 only, where 15 of 15 per-case
values reproduce 2026-07-18_lever_effect_size_is_channel_set_dependent.md to
three decimals, plus the five baseline values named in section 1. candidate162
and candidate2216 brightness beyond those five has no recorded counterpart and is
NOT independently gated.

Brightness is the mean of a 448x256 band. It is not a photometric night detector.
It supports the size of the weights gap relative to the threshold, and nothing
about any single frame.

Calling the top band the source row rests on its invariance under injection and
weights, now measured at 0.000 across six views on two windows. It is still NOT
verified against the DD2 tester's mosaic specification.

Section 3's 53 percent is unexplained, not explained away. Four hypotheses died;
that is not the same as the fifth being absent.

Only the first case of each run was read for the override audits: 13 runs, one
attempt each.

## Method note
Blocks 205 and 207 both read entries_preview and both concluded from it that
candidate2216's structural condition was empty. Block 207 then built a hypothesis
on that: an empty box condition renders degenerately, which would have named the
35 points. All of it was an artifact of three entries that sit outside the
window.

The refutation was already in block 205's own output. It printed
dd2_baseline_structural_snapshot.sample.frame_idx as 0 for candidate162 and 96
for candidate2216, two blocks before the hypothesis was formed, in the same
section that produced the evidence for it. The number was on the screen and was
not used. Block 208's own preamble worried that the preview showed the wrong
camera and still did not notice it showed the wrong frames.

A truncated field is worth less than an untruncated one, and a preview is worth
less than a file. Both were available the whole time. The rule that would have
prevented four blocks of this is: before drawing anything from a field named
preview, read what it is a preview of.
