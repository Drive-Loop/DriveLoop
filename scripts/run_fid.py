"""Frame-wise FID of DriveLoop videos vs real nuScenes cam_front frames.

Reuses the clip collection of scripts/run_fvd.py: REAL = 128 real
8-frame cam_front windows (1024 frames), OPEN = attempt-0 videos of
the v10f pool and seven-arm runs (41 clips, 328 frames), CLOSED =
best-attempt videos of the same runs (41 clips, 328 frames). Features
are InceptionV3 pool3 (pytorch-fid weights, input resized internally).
Report as frame-wise FID under our fixed protocol; absolute values are
not comparable to numbers published under other protocols. Small-N
caveat applies and is reported alongside the numbers."""
import numpy as np
import torch

from scripts.run_fvd import collect_generated, collect_real, frechet


def clips_to_frames(clips):
    out = []
    for c in clips:
        for i in range(c.shape[0]):
            out.append(c[i])
    return out


def inception_features(frames, model, device, batch=32):
    feats = []
    for i in range(0, len(frames), batch):
        arr = np.stack(frames[i:i + batch]).astype(np.float32) / 255.0
        t = torch.from_numpy(arr).permute(0, 3, 1, 2).contiguous().to(device)
        with torch.no_grad():
            f = model(t)[0]
        feats.append(f.squeeze(-1).squeeze(-1).cpu().numpy())
    return np.concatenate(feats)


def main():
    from pytorch_fid.inception import InceptionV3
    device = "cuda" if torch.cuda.is_available() else "cpu"
    idx = InceptionV3.BLOCK_INDEX_BY_DIM[2048]
    model = InceptionV3([idx]).to(device).eval()

    open_clips, closed_clips = collect_generated()
    real_clips = collect_real()
    print("clips: open=%d closed=%d real=%d"
          % (len(open_clips), len(closed_clips), len(real_clips)))

    f_open = inception_features(clips_to_frames(open_clips), model, device)
    f_closed = inception_features(clips_to_frames(closed_clips), model, device)
    f_real = inception_features(clips_to_frames(real_clips), model, device)
    print("frames: open=%d closed=%d real=%d"
          % (len(f_open), len(f_closed), len(f_real)))

    print("FID_OPEN_VS_REAL %.1f" % frechet(f_open, f_real))
    print("FID_CLOSED_VS_REAL %.1f" % frechet(f_closed, f_real))


if __name__ == "__main__":
    main()
