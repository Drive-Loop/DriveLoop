# Frame-wise FID, v10f returned vs open videos (2026-08-07)

Protocol: same clip sets as the FVD record. REAL = 128 real 8-frame
cam_front windows from the train enumeration (seed 0, 1024 frames).
OPEN = attempt-0 videos of the v10f pool + seven arms (41 clips, 328
frames). CLOSED = best-attempt (returned) videos of the same runs
(41 clips, 328 frames). Generated frames are the cam_front crop of
the composite canvas. Features: InceptionV3 pool3, pytorch-fid
weights (pt_inception-2015-12-05). Command: python -m scripts.run_fid

Results:
- FID open   vs real: 166.4
- FID closed vs real: 156.7

Reading: closed-loop returned videos are closer to the real frame
distribution than the single passes, consistent with FVD
(1752 vs 2103). Small-N caveat: 41 clips per generated set; absolute
values are not comparable to published numbers under other protocols.
Paper: Sec 5.1 Measurements (metric definition) + Sec 5.2.4 Realism.
