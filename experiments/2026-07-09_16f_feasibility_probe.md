# 2026-07-09 16-frame feasibility probe: host-RAM bound

drivedreamer2_img_cond_mini_local_16f (frame_num 16, all else equal)
on the clean mini window: the DD2 subprocess was SIGKILLed by the
Linux OOM killer at anon-rss ~29.4 GiB on a 28 GiB host (dmesg
confirmed; zero CUDA OOM lines - the GPU never became the constraint).
Longer frame_num on this machine is host-memory bound before it is
GPU bound; 48 f is excluded a fortiori. The frame-count lever for
synthetic-path quality requires a larger host (and likely GPU).
Claim boundary: single probe, one config; no video produced.
