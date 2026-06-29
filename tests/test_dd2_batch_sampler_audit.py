import pickle

import numpy as np

from scripts.run_dd2_batch_sampler_audit import build_report


CAMERA_NAMES = ["CAM_FRONT_LEFT", "CAM_FRONT", "CAM_FRONT_RIGHT", "CAM_BACK_RIGHT", "CAM_BACK", "CAM_BACK_LEFT"]


def make_records(candidate_count=2):
    records = []
    span = 40
    for candidate in range(candidate_count):
        base = candidate * span
        mv = {
            "CAM_FRONT_LEFT": base + 0,
            "CAM_FRONT_RIGHT": base + 2,
            "CAM_BACK_RIGHT": base + 3,
            "CAM_BACK": base + 4,
            "CAM_BACK_LEFT": base + 5,
        }
        for offset in range(span):
            cam_name = CAMERA_NAMES[offset % len(CAMERA_NAMES)]
            idx = base + offset
            records.append(
                {
                    "frame_idx": 0 if offset < 6 else offset,
                    "video_length": 80,
                    "cam_type": cam_name.lower(),
                    "multiview_start_idx": mv,
                    "scene_description": f"candidate {candidate} multi lane road",
                    "labels3d": [["vehicle", "car"]] if candidate == 0 else [["vehicle", "motorcycle"]],
                    "boxes3d": np.ones((1, 9), dtype=np.float32) * candidate,
                    "sample_token": f"sample-{candidate}-{offset}",
                    "scene_token": f"scene-{candidate}",
                }
            )
    return records


def test_batch_sampler_audit_reports_distinct_candidates(tmp_path):
    labels = tmp_path / "data.pkl"
    with labels.open("wb") as f:
        pickle.dump(make_records(candidate_count=2), f)

    report = build_report(
        labels,
        max_skip=1,
        frame_num=8,
        cam_num=6,
        hz_factor=3,
        video_split_rate=1,
        multiview=True,
    )

    assert report["candidate_start_count"] == 2
    assert len(report["candidates"]) == 2
    assert report["candidates"][0]["front_record"]["scene_description"] == "candidate 0 multi lane road"
    assert report["candidates"][1]["front_record"]["scene_description"] == "candidate 1 multi lane road"
    assert (
        report["candidates"][0]["signatures"]["boxes3d"]
        != report["candidates"][1]["signatures"]["boxes3d"]
    )
