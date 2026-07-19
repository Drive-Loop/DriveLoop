#!/usr/bin/env python
"""Find the actor instance token(s) of a category present across the front frames
of a scanned candidate window -- the identity to bind when building a new source
window. Reuses the enumeration primitives from run_dd2_batch_sampler_audit so the
candidate index means the same thing it does in the scan and in binding.

Read-only: loads the enumeration labels/data.pkl and reports; renders nothing.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from scripts.run_dd2_batch_sampler_audit import candidate_camera_starts, load_records


def _category(labels: List[Any], box_index: int) -> str:
    if box_index >= len(labels):
        return ""
    label = labels[box_index]
    if isinstance(label, (list, tuple)):
        return ".".join(str(part) for part in label)
    return str(label)


def instances_across_frames(front_records: List[Dict[str, Any]], category_prefix: str) -> Tuple[Dict[str, set], Dict[str, str]]:
    """Map instance_token -> set of front-frame indices it appears in (restricted
    to boxes whose category starts with category_prefix), plus its category."""
    prefix = category_prefix.lower()
    presence: Dict[str, set] = defaultdict(set)
    category_of: Dict[str, str] = {}
    for frame_index, record in enumerate(front_records):
        instances = record.get("instance_tokens") or []
        labels = record.get("labels3d") or record.get("ori_labels3d") or []
        for box_index, instance in enumerate(instances):
            category = _category(labels, box_index)
            if instance and category.lower().startswith(prefix):
                presence[str(instance)].add(frame_index)
                category_of[str(instance)] = category
    return presence, category_of


def find_actor(labels_path: Any, candidate_index: int, category_prefix: str = "pedestrian",
               frame_num: int = 8, hz_factor: int = 3, video_split_rate: int = 1,
               multiview: bool = True) -> Dict[str, Any]:
    records = load_records(Path(labels_path))
    starts = candidate_camera_starts(
        records, frame_num=frame_num, hz_factor=hz_factor,
        video_split_rate=video_split_rate, multiview=multiview,
    )
    if not 0 <= candidate_index < len(starts):
        raise SystemExit("candidate_index %d out of range (%d candidate starts)" % (candidate_index, len(starts)))
    camera_starts = starts[candidate_index]
    front_start = camera_starts[1] if multiview and len(camera_starts) > 1 else camera_starts[0]
    front_indices = [front_start + i * hz_factor for i in range(frame_num)]
    front_records = [records[j] for j in front_indices if 0 <= j < len(records)]

    presence, category_of = instances_across_frames(front_records, category_prefix)
    all_frames = sorted(
        ((instance, sorted(frames)) for instance, frames in presence.items() if len(frames) == frame_num),
        key=lambda item: item[0],
    )
    ranked = sorted(((len(frames), instance) for instance, frames in presence.items()), reverse=True)

    front0 = front_records[0] if front_records else {}
    return {
        "candidate_index": candidate_index,
        "category_prefix": category_prefix,
        "f0_sample_token": front0.get("sample_token"),
        "scene_token": front0.get("scene_token"),
        "scene_description": front0.get("scene_description"),
        "front_record_indices": front_indices,
        "instances_present_all_frames": [
            {"instance_token": inst, "category": category_of[inst], "frames": frames}
            for inst, frames in all_frames
        ],
        "top_by_frame_coverage": [
            {"instance_token": inst, "category": category_of[inst], "frame_count": count}
            for count, inst in ranked[:10]
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Find an actor instance token present across a candidate's front frames (for source-window binding)."
    )
    parser.add_argument("--labels", required=True, help="enumeration labels/data.pkl")
    parser.add_argument("--candidate-index", type=int, required=True)
    parser.add_argument("--category-prefix", default="pedestrian")
    parser.add_argument("--frame-num", type=int, default=8)
    parser.add_argument("--hz-factor", type=int, default=3)
    parser.add_argument("--video-split-rate", type=int, default=1)
    args = parser.parse_args(argv)
    print(json.dumps(
        find_actor(args.labels, args.candidate_index, args.category_prefix,
                   args.frame_num, args.hz_factor, args.video_split_rate),
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
