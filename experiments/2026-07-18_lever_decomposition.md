# 2026-07-18 What the +38 percent lever is made of: two cases, one binary flag, and a defect that doubles its own weight

The FT lift of 0.118425 on candidate70 decomposes exactly. 76 percent of it is
S_ctrl and 24 percent is S_perc. All of the S_ctrl part is one binary channel,
object_presence, flipping on two of five cases. On one of those two cases the
flip is worth twice as much as on the other, because that case is missing its
motion plan and therefore has one fewer channel to divide by. The evidence for
the FT lever is real and was established elsewhere; the +38 percent is that
evidence after it passes through a denominator that nobody chose.

## Decomposition, checked against the measured lift
J = 0.5*S_perc + 0.3*S_ctrl + 0.2*S_intent, means over the five cases of
exp_v9c_official_open_anchor and exp_v9c_ft6322_open_loop_bank0_v2.

    case   dS_perc    dS_ctrl   contrib_perc  contrib_ctrl  contrib_total   share
    m1     0.367806   0.500000    0.036781      0.030000      0.066781      56.4%
    m2    -0.243847   0.000000   -0.024385      0.000000     -0.024385     -20.6%
    m3     0.028491   0.000000    0.002849      0.000000      0.002849       2.4%
    m4     0.131804   1.000000    0.013180      0.060000      0.073180      61.8%
    m5     0.000000   0.000000    0.000000      0.000000      0.000000       0.0%

    term       contribution   share
    S_ctrl       +0.090000    76.0%
    S_perc       +0.028425    24.0%
    S_intent     +0.000000     0.0%

    measured lift        0.118425
    decomposition sum    0.118425   OK

dS_intent is zero on every case, so the intent term plays no part.

## Two channels of three carry no arm signal on this window
Per case, per arm, with the lighting channel restored:

    channel           behaviour across the two arms on candidate70
    lighting_night    1.0 on both arms, identical on 5 of 5 cases
    target_motion     0.0 on both arms, identical on 4 of 4 cases that have it
    object_presence   differs on 2 of 5 cases: m1 and m4

target_motion is worse than uninformative. It is 0.0 for every arm on every case,
meaning no usable track was ever found, so it contributes nothing to the numerator
while adding one to the denominator. It halves S_ctrl unconditionally on this
window. lighting_night, once restored, contributes 1.0 to every arm and dilutes
by the same mechanism in the other direction.

## The m4 defect doubles its own contribution
m1 and m4 record the same physical event: the FT arm is detected where the anchor
is not, object_presence going 0.0 to 1.0. m1 scores dS_ctrl 0.5 and m4 scores
1.0. The difference is not in the generation. m4 has no motion primitives, so it
has no target_motion channel, so its S_ctrl averages over one channel instead of
two and a single binary flip swings it the full range. m4 contributes 0.060000 of
S_ctrl against m1's 0.030000, and 61.8 percent of the whole lever against m1's
56.4 percent.

m4 is already on the repair list for a missing surface plan. Repairing it would
add its target_motion channel, halve its S_ctrl swing, and reduce the lever. The
defect is currently the single largest contributor to the headline result.

## What should be reported
2026-07-18_c70_subtraction_probe.md established the FT lever independently and in
the right shape: the FT arm renders six motorcycle detections against the anchor's
three, and every one survives baseline subtraction. 2026-07-13_bank1_seed_
replication_detectability.md reports detectability 2/5 against 0/5 at bank0. That
is the finding. It is a statement about detections, it does not pass through a
channel mean, and no denominator can move it.

The +38 percent is the same two detections after multiplication by 0.3 and
division by a channel count that varies with which channels happen to fire. It
moves to +20 percent if the dead lighting block is revived, and it would move
again if m4 were repaired. Reporting it as an effect size implies a precision the
construction does not have.

## Claim boundary
This decomposition is arithmetic on archived metrics. It re-derives the archived
lift to nine decimals, which is what licenses it. It says nothing about whether FT
is a better model: the detection evidence for that is elsewhere and is unaffected.

The channel behaviour is measured on candidate70 v9c and candidate162 v10w only.
The stacked arm of 2026-07-13_ft_dims_stacking_probe.md and the bank1 arms were
not decomposed. NOT MEASURED.

Whether repairing m4 would raise or lower the lever overall is NOT MEASURED. The
S_ctrl swing would halve, but a repaired m4 might also change S_perc, and the
direction of that is unknown without running it.

## Method note
The per-case shares in this record were first computed by hand from the channel
table and were wrong: m4 was put at 51 percent against a true 61.8, and m1 at
25.3 against a true 56.4. The error was counting only each case's S_ctrl term and
dropping its S_perc term. The term-level split, 76 and 24 percent, was right by
hand. A decomposition that does not sum back to the measured quantity is not a
decomposition, and checking the sum is one line.
