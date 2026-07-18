# 2026-07-18 m4 is a parse failure, not a data defect: ten of the +38 percent are one unread English sentence

The candidate70 FT lever is +38.1 percent under the archived construction and
+28.5 percent once m4 is repaired. The ten points between them are not a
measurement. They are the grounder failing to read m4's prompt.

Repairing it needs no GPU, and it produces exactly the number C3 already
produces, so the construction gate is one choice and not two.

## m4 asks for a motion. The keyword table has no word for it.
    m1  "night urban street, a motorcycle cuts in from the left toward the
         ego vehicle"                                            -> ['cut_in']
    m4  "night urban intersection, a motorcycle approaches from the left
         adjacent lane toward the ego path"                      -> []

The two prompts describe the same event: something comes out of the left
adjacent lane toward the ego path. m1 says "cuts in" and m4 says "approaches".
driveloop.grounding._MOTION_KEYWORDS holds five entries, cut_in, lane_change,
crossing, stopped and turning, and none of them matches "approaches". No case
carries a structured_intent, so all five take the keyword path, and m4's
motion_primitives are empty because a sentence was not parsed, not because the
case declines to request a motion.

This is licensed by a gate: today's RuleBasedGrounder, re-grounding the archived
requests, reproduces the archived motion_primitives on all 15 attempts. The
grounder has not changed since these runs, so the empty list is the same empty
list they were scored with.

## The repair is a rescore, and it is C3
perception_dominant_motion_over_width is archived on all fifteen attempts. The
channel is missing from the score, not from the run. Restoring it by
control_visibility's own rule:

    construction    anchor S_ctrl              ft6322 S_ctrl              lever
    C1 archived     0, .5, .5,  0, 0           .5, .5, .5, 1.0, 0     +0.118425 +38.1%
    C3 fixed set    0, .5, .5,  0, 0           .5, .5, .5,  .5, 0     +0.088425 +28.5%
    m4 repaired     0, .5, .5,  0, 0           .5, .5, .5,  .5, 0     +0.088425 +28.5%

m4 repaired and C3 are identical per case to 1e-9, on every arm. The dims1p5
lever is +0.089034 under all three, because m4 scores object_presence 0.0 on both
the anchor and the dims arm and only the FT arm flips it.

C1 reproduces the recorded lever at +0.118425 against 0.118425, which is what
licenses the other two rows.

## The tracker never produced a track on this window, on any case or any arm
    perception_dominant_motion_over_width = -1.0 on 15 of 15 attempts

Not only on m4. On m1, m2, m3 and m5 too, which do carry motion primitives.
-1.0 is control_visibility's sentinel for no usable track, so target_motion
scores 0.0 across the whole window by construction, and it enters every
denominator without ever entering a numerator.

That closes the generation-side repair as well. The handoff proposes fixing m4 by
adding its missing surface plan and re-rendering, at the cost of a GPU run. It
would not move target_motion: the four cases that already have motion primitives
score -1.0 anyway. There is nothing for that GPU to measure on this channel.

## Corrections to 2026-07-18_s_ctrl_construction_comparison.md (34e3d12)
Two sentences in that record are wrong, and they were wrong in the same way:
both were reasoned from the handoff's phrase "m4 fix (add the surface plan)"
without reading either the prompt or the archived metric.

    "Repairing m4 (adding the missing surface plan and re-running it) ...
     It needs GPU."

It does not. The measurement is archived; the repair is arithmetic.

    "C3 ... Its cost is that 'a missing channel scores 0' is itself a choice,
     and an unkind one: m4 never requested a motion primitive, and C3 penalises
     it for not showing what it never asked for."

m4 did request a motion. C3 scores its target_motion 0.0, and 0.0 is what the
archived measurement says: no usable track, the motion was not visible. That was
the main argument against C3 in that record and it does not survive. C3 is not
charging m4 for a channel it never asked for; it is charging it for a motion it
asked for and did not demonstrate, on the same terms as the other four cases.

## What the gate now looks like
    C1  +38.1%   keeps an unparsed sentence in the arm comparison
    C3  +28.5%   identical to repairing m4

There is no third position and no GPU dependency. The remaining question is only
what to call it: adopt C3 as a construction, or fix the keyword table so that C1
becomes 28.5 percent on its own. The second is the more honest description of
what happened, because the ten points removed were never a property of the
models.

Whether to change _MOTION_KEYWORDS is a separate decision with its own cost: it
alters grounding for every future run and for every case whose prompt contains
"approach", it changes the condition plan those runs would build, and it needs
its own tests. It does not change any number in this record, which is computed
from the archive as it stands.

## Claim boundary
Arithmetic on archived metrics plus a re-grounding of the archived requests. No
run was re-executed, no GPU, no video read. candidate70 only; the v10w windows
have no case missing a channel, so C1 and C3 already coincide there (block 198).

"m4 repaired" means one thing here: score the target_motion channel from the
measurement the run already archived. It says nothing about whether the actor
moved in the video, and it does not touch the actor motion plan the backend
built. Whether m4 has such a plan at all was NOT checked.

That m4's prompt and m1's prompt describe the same event is a reading of two
English sentences, not a measurement. What is measured is narrower: m4's prompt
contains a motion verb, the keyword table contains no entry that matches it, and
the resulting empty list is what removed the channel.

Which primitive m4 should ground to, if the table were extended, is not settled
here. "approaches from the left adjacent lane toward the ego path" at an
intersection could reasonably be cut_in or a new primitive, and that is a
benchmark question.

## Method note
The block that produced this nearly failed on the same defect it documents. Its
predecessor read driveloop/grounding.py with grep piped into head -25, saw the
first two of five _MOTION_KEYWORDS entries, and asserted the table held two. The
conclusion happened to survive, because "approaches" matches none of the five
either, but the reasoning was again built on a truncated read, three blocks after
2026-07-18_weights_brightness_pump_and_the_entries_preview_trap.md was committed
with the rule "before drawing anything from a field named preview, read what it
is a preview of". A head is a preview. This time the truncation was self-inflicted.

Section 2 of the probe therefore imports _MOTION_KEYWORDS and prints its length
rather than transcribing it, and section 4's C1-versus-record check exits
non-zero rather than printing a verdict nobody enforces.
