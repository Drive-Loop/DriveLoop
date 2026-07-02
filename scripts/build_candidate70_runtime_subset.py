#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import pickle
import shutil
from pathlib import Path
from typing import Any

from dd_scripts.converters.nuscenes_converter import NuScenesConverter
from dreamer_datasets.datasets.dataset import Dataset, load_dataset
from dreamer_datasets.datasets.lmdb_dataset import LmdbWriter
from dreamer_datasets.datasets.pkl_dataset import PklWriter

from scripts.run_dd2_batch_sampler_audit import (
    CAM_NAMES,
    candidate_camera_starts,
    selected_frame_indices,
)
from driveloop.source_sample_binding import build_source_sample_binding


CAM_START_ORDER = ["CAM_FRONT_LEFT", "CAM_FRONT", "CAM_FRONT_RIGHT", "CAM_BACK_RIGHT", "CAM_BACK", "CAM_BACK_LEFT"]


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, list):
        raise TypeError(f"expected list payload in {path}")
    return [item for item in payload if isinstance(item, dict)]


def write_root_dataset_config(output_dir: Path) -> None:
    datasets = [
        load_dataset(str(output_dir / "labels")),
        load_dataset(str(output_dir / "images")),
        load_dataset(str(output_dir / "hdmaps")),
    ]
    Dataset(datasets).save(str(output_dir))


def build_subset(
    *,
    source_dataset_dir: Path,
    raw_nuscenes_root: Path,
    output_dir: Path,
    identity_summary: Path,
    source_candidate_id: str,
    instance_token: str,
    frame_num: int,
    hz_factor: int,
    video_split_rate: int,
    multiview: bool,
    overwrite: bool,
) -> dict[str, Any]:
    if output_dir.exists():
        if not overwrite:
            raise FileExistsError(f"{output_dir} already exists; pass --overwrite to replace it")
        shutil.rmtree(output_dir)

    binding = build_source_sample_binding(
        source_dataset_dir,
        source_candidate_id=source_candidate_id,
        instance_token=instance_token,
        identity_summary_path=identity_summary,
        frame_num=frame_num,
        hz_factor=hz_factor,
        video_split_rate=video_split_rate,
        multiview=multiview,
    )
    if binding.get("ready") is not True:
        raise RuntimeError(f"source binding is not ready: {binding}")

    labels_path = source_dataset_dir / "labels" / "data.pkl"
    records = load_records(labels_path)
    starts = candidate_camera_starts(
        records,
        frame_num=frame_num,
        hz_factor=hz_factor,
        video_split_rate=video_split_rate,
        multiview=multiview,
    )
    candidate_index = int(binding["dd2_batch_skip"])
    camera_starts = starts[candidate_index]

    video_frame_len = frame_num * hz_factor
    window_indices = []
    for start_index in camera_starts:
        window_indices.extend(start_index + offset for offset in range(video_frame_len))

    old_to_new = {old_index: new_index for new_index, old_index in enumerate(window_indices)}
    start_old_to_new = {
        old_start: old_to_new[old_start]
        for old_start in camera_starts
    }

    labels_dir = output_dir / "labels"
    images_dir = output_dir / "images"
    hdmaps_dir = output_dir / "hdmaps"

    output_dir.mkdir(parents=True, exist_ok=True)

    label_writer = PklWriter(str(labels_dir))
    image_writer = LmdbWriter(str(images_dir))
    hdmap_writer = LmdbWriter(str(hdmaps_dir))

    labels_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    hdmaps_dir.mkdir(parents=True, exist_ok=True)

    converter = NuScenesConverter(
        data_dir=str(raw_nuscenes_root),
        version="v1.0-trainval",
        save_path=str(output_dir.parent),
        save_version=output_dir.name,
    )

    new_records = []
    for new_index, old_index in enumerate(window_indices):
        record = copy.deepcopy(records[old_index])
        record["data_index"] = new_index

        mv = record.get("multiview_start_idx")
        if isinstance(mv, dict):
            remapped = {}
            for cam_name in CAM_NAMES:
                old_start = mv.get(cam_name)
                if old_start in start_old_to_new:
                    remapped[cam_name] = start_old_to_new[old_start]
            record["multiview_start_idx"] = remapped

        label_writer.write_dict(record)
        new_records.append(record)

        image_path = Path(converter.nusc.get_sample_data_path(record["cam_token"]))
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        image_writer.write_image(new_index, str(image_path))

        image_hdmap = converter._get_hdmap(record["cam_token"], record["scene_token"])
        hdmap_writer.write_image(new_index, image_hdmap)

    label_writer.write_config()
    label_writer.close()
    image_writer.write_config()
    image_writer.close()
    hdmap_writer.write_config(data_name="image_hdmap")
    hdmap_writer.close()
    write_root_dataset_config(output_dir)

    subset_binding = build_source_sample_binding(
        output_dir,
        source_candidate_id=source_candidate_id,
        instance_token=instance_token,
        identity_summary_path=identity_summary,
        frame_num=frame_num,
        hz_factor=hz_factor,
        video_split_rate=video_split_rate,
        multiview=multiview,
    )
    selected_indices = selected_frame_indices(
        [start_old_to_new[start] for start in camera_starts],
        frame_num=frame_num,
        hz_factor=hz_factor,
    )

    report = {
        "schema_version": "driveloop_candidate70_runtime_subset.v0",
        "source_dataset_dir": str(source_dataset_dir),
        "raw_nuscenes_root": str(raw_nuscenes_root),
        "output_dir": str(output_dir),
        "source_binding": binding,
        "subset_binding": subset_binding,
        "source_candidate_index": candidate_index,
        "source_camera_starts": camera_starts,
        "subset_record_count": len(new_records),
        "subset_selected_frame_indices": selected_indices,
        "claim_boundary": {
            "runtime_subset_is_derived_from_full_trainval": True,
            "runtime_subset_is_not_video_semantic_success": True,
            "runtime_subset_is_not_gpu_approval": True,
        },
    }
    report_path = output_dir / "subset_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build candidate70 full-trainval source-bound DD2 runtime subset.")
    parser.add_argument("--source-dataset-dir", type=Path, required=True)
    parser.add_argument("--raw-nuscenes-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--identity-summary", type=Path, required=True)
    parser.add_argument("--source-candidate-id", default="candidate70")
    parser.add_argument("--instance-token", required=True)
    parser.add_argument("--frame-num", type=int, default=8)
    parser.add_argument("--hz-factor", type=int, default=3)
    parser.add_argument("--video-split-rate", type=int, default=1)
    parser.add_argument("--single-view", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    report = build_subset(
        source_dataset_dir=args.source_dataset_dir,
        raw_nuscenes_root=args.raw_nuscenes_root,
        output_dir=args.output_dir,
        identity_summary=args.identity_summary,
        source_candidate_id=args.source_candidate_id,
        instance_token=args.instance_token,
        frame_num=args.frame_num,
        hz_factor=args.hz_factor,
        video_split_rate=args.video_split_rate,
        multiview=not args.single_view,
        overwrite=args.overwrite,
    )
    print(json.dumps({
        "output_dir": report["output_dir"],
        "source_dd2_batch_skip": report["source_binding"].get("dd2_batch_skip"),
        "subset_ready": report["subset_binding"].get("ready"),
        "subset_dd2_batch_skip": report["subset_binding"].get("dd2_batch_skip"),
        "subset_record_count": report["subset_record_count"],
        "subset_report": str(Path(report["output_dir"]) / "subset_report.json"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
