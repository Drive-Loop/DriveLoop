"""FVD of DriveLoop videos against real nuScenes cam_front clips.

Sets: REAL = 128 real 8-frame cam_front windows sampled from the train
enumeration (seed 0); OPEN = attempt-0 videos of the v10f pool and
seven-arm runs; CLOSED = best-attempt videos of the same runs.
Generated frames are the cam_front crop of the composite canvas (the
same generated-row geometry the evaluator scores). All clips are 8
frames duplicated to 16 for the I3D torchscript extractor (stylegan-v
weights); report this as FVD-8(dup16). Small-N caveat applies (N=41
generated per set) and is reported alongside the numbers."""
import glob, json, os

import numpy as np

POOL = [
    "candidate1677_truck_cut_in_v10f", "candidate1313_night_truck_v10f",
    "candidate2751_rain_truck_v10f", "candidate1300_night_cut_in_v10f",
    "candidate28_bus_v10f", "candidate41_bicycle_v10f",
]
ARMS = ["cl_v10f_c162_official", "cl_v10f_c162_ft6322_dims",
        "cl_v10f_c2216_official", "cl_v10f_c2216_ft6322_dims",
        "cl_v10f_c70_official", "cl_v10f_c70_ft6322",
        "cl_v10f_c70_official_dims1p5"]
ENUM = "/mnt/driveloop_full/processed/nuscenes/v1.0-trainval/cam_all_train/v0.0.2"
RAW = "/mnt/driveloop_full/raw/nuscenes"
I3D = "/data/projects/DriveLoop/pretrained_models/i3d_torchscript.pt"
N_REAL = 128
VIEW_W, VIEW_H = 448, 256


def read_video_front(path):
    import imageio.v2 as iio
    frames = iio.mimread(path, memtest=False)
    out = []
    for fr in frames[:8]:
        fr = np.asarray(fr)
        h = fr.shape[0]
        crop = fr[h - VIEW_H:, VIEW_W:2 * VIEW_W, :3]
        out.append(crop)
    return np.stack(out) if len(out) == 8 else None


def resize(img):
    try:
        import cv2
        return cv2.resize(img, (VIEW_W, VIEW_H), interpolation=cv2.INTER_AREA)
    except ImportError:
        from PIL import Image
        return np.asarray(Image.fromarray(img).resize((VIEW_W, VIEW_H)))


def collect_generated():
    open_set, closed_set = [], []
    for run in POOL + ARMS:
        for rj in sorted(glob.glob("outputs/driveloop/%s/*/result.json" % run)):
            case_dir = os.path.dirname(rj)
            a0 = os.path.join(case_dir, "artifacts", "iteration_00.mp4")
            if os.path.exists(a0):
                v = read_video_front(a0)
                if v is not None:
                    open_set.append(v)
            res = json.load(open(rj))
            best = ((res.get("best_generation") or {}).get("artifacts") or {}).get("video")
            if best and os.path.exists(str(best)):
                v = read_video_front(best)
                if v is not None:
                    closed_set.append(v)
    return open_set, closed_set


def collect_real():
    from pathlib import Path
    from nuscenes.nuscenes import NuScenes
    from scripts.run_dd2_batch_sampler_audit import (
        candidate_camera_starts, load_records)
    import imageio.v2 as iio

    records = load_records(Path(ENUM) / "labels" / "data.pkl")
    starts = candidate_camera_starts(
        records, frame_num=8, hz_factor=3, video_split_rate=1, multiview=True)
    rng = np.random.default_rng(0)
    picks = rng.choice(len(starts), size=min(N_REAL, len(starts)), replace=False)
    nusc = NuScenes(version="v1.0-trainval", dataroot=RAW, verbose=False)
    clips = []
    for pi in picks:
        group = starts[int(pi)]
        front = group[1] if len(group) > 1 else group[0]
        frames = []
        for i in range(8):
            rec = records[front + i * 3]
            path = nusc.get_sample_data_path(rec["cam_token"])
            img = np.asarray(iio.imread(path))[:, :, :3]
            frames.append(resize(img))
        clips.append(np.stack(frames))
    return clips


def i3d_features(clips, i3d, device):
    import torch
    feats = []
    for i in range(0, len(clips), 8):
        batch = np.stack(clips[i:i + 8]).astype(np.float32)
        batch = np.repeat(batch, 2, axis=1)  # 8 -> 16 frames
        t = torch.from_numpy(batch).permute(0, 4, 1, 2, 3).contiguous().to(device)
        with torch.no_grad():
            f = i3d(t, rescale=True, resize=True, return_features=True)
        feats.append(f.cpu().numpy())
    return np.concatenate(feats)


def frechet(a, b):
    from scipy import linalg
    mu1, mu2 = a.mean(0), b.mean(0)
    s1 = np.cov(a, rowvar=False)
    s2 = np.cov(b, rowvar=False)
    diff = mu1 - mu2
    covmean, _ = linalg.sqrtm(s1.dot(s2), disp=False)
    if np.iscomplexobj(covmean):
        covmean = covmean.real
    return float(diff.dot(diff) + np.trace(s1) + np.trace(s2)
                 - 2 * np.trace(covmean))


def main():
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    i3d = torch.jit.load(I3D).eval().to(device)
    open_set, closed_set = collect_generated()
    print("OPEN_N", len(open_set), "CLOSED_N", len(closed_set))
    real = collect_real()
    print("REAL_N", len(real))
    f_real = i3d_features(real, i3d, device)
    f_open = i3d_features(open_set, i3d, device)
    f_closed = i3d_features(closed_set, i3d, device)
    report = {
        "protocol": "FVD-8(dup16), cam_front crops, i3d_torchscript"
                    " (stylegan-v), seed-0 real sample",
        "n_real": len(real), "n_open": len(open_set),
        "n_closed": len(closed_set),
        "fvd_real_vs_open": frechet(f_real, f_open),
        "fvd_real_vs_closed": frechet(f_real, f_closed),
        "fvd_open_vs_closed": frechet(f_open, f_closed),
        "caveat": "small generated N; detector-level realism proxy only",
    }
    print("FVD_SUMMARY")
    for k, v in report.items():
        print(" ", k, "=", v)
    with open("outputs/driveloop/fvd_report.json", "w") as fh:
        json.dump(report, fh, indent=2)
    print("REPORT outputs/driveloop/fvd_report.json")


if __name__ == "__main__":
    main()
