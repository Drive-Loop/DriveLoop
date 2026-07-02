from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from scripts.run_dd2_batch_sampler_audit import (
    candidate_camera_starts,
    load_records,
    selected_frame_indices,
)


def _as_set(values: Iterable[Any]) -> set[str]:
    return {str(value) for value in values if value not in (None, "")}


def _identity_sample_tokens(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    frames = data.get("frame_summaries", [])
    if not isinstance(frames, list):
        return set()
    return _as_set(frame.get("sample_token") for frame in frames if isinstance(frame, dict))


def build_source_sample_binding(
    dataset_dir: str | Path,
    *,
    source_candidate_id: str | None = None,
    sample_token: str | None = None,
    scene_token: str | None = None,
    instance_token: str | None = None,
    identity_summary_path: str | Path | None = None,
    frame_num: int = 8,
    hz_factor: int = 3,
    video_split_rate: int = 1,
    multiview: bool = True,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    labels_path = dataset_dir / "labels" / "data.pkl"
    identity_path = Path(identity_summary_path) if identity_summary_path else None

    selector = {
        "source_candidate_id": source_candidate_id,
        "sample_token": sample_token,
        "scene_token": scene_token,
        "instance_token": instance_token,
        "identity_summary_path": str(identity_path) if identity_path else None,
    }
    target_sample_tokens = _as_set([sample_token]) | _identity_sample_tokens(identity_path)
    target_scene_tokens = _as_set([scene_token])

    requested = bool(source_candidate_id or target_sample_tokens or target_scene_tokens or instance_token)
    if not requested:
        return {
            "schema_version": "driveloop_source_sample_binding.v0",
            "requested": False,
            "ready": False,
            "selector": selector,
            "reason": "no_source_sample_selector_requested",
        }

    if not labels_path.exists():
        return {
            "schema_version": "driveloop_source_sample_binding.v0",
            "requested": True,
            "ready": False,
            "selector": selector,
            "labels_path": str(labels_path),
            "reason": "dd2_labels_data_missing",
        }

    records = load_records(labels_path)
    starts = candidate_camera_starts(
        records,
        frame_num=frame_num,
        hz_factor=hz_factor,
        video_split_rate=video_split_rate,
        multiview=multiview,
    )

    for candidate_index, camera_starts in enumerate(starts):
        selected_indices = selected_frame_indices(
            camera_starts,
            frame_num=frame_num,
            hz_factor=hz_factor,
        )
        selected_records = [records[index] for index in selected_indices if 0 <= index < len(records)]
        selected_sample_tokens = _as_set(record.get("sample_token") for record in selected_records)
        selected_scene_tokens = _as_set(record.get("scene_token") for record in selected_records)

        matched_sample_tokens = sorted(target_sample_tokens & selected_sample_tokens)
        matched_scene_tokens = sorted(target_scene_tokens & selected_scene_tokens)
        sample_tokens_match = bool(target_sample_tokens) and target_sample_tokens.issubset(selected_sample_tokens)
        scene_tokens_match = bool(target_scene_tokens) and target_scene_tokens.issubset(selected_scene_tokens)
        token_groups_requested = bool(target_sample_tokens or target_scene_tokens)
        token_groups_match = (
            token_groups_requested
            and (not target_sample_tokens or sample_tokens_match)
            and (not target_scene_tokens or scene_tokens_match)
        )
        if token_groups_match:
            front_record_index = camera_starts[1] if multiview and len(camera_starts) > 1 else camera_starts[0]
            front_record = records[front_record_index]
            return {
                "schema_version": "driveloop_source_sample_binding.v0",
                "requested": True,
                "ready": True,
                "selector": selector,
                "dataset_dir": str(dataset_dir),
                "labels_path": str(labels_path),
                "record_count": len(records),
                "candidate_start_count": len(starts),
                "dd2_batch_skip": candidate_index,
                "front_record_index": front_record_index,
                "front_record": {
                    "sample_token": front_record.get("sample_token"),
                    "scene_token": front_record.get("scene_token"),
                    "cam_type": front_record.get("cam_type"),
                    "frame_idx": front_record.get("frame_idx"),
                    "scene_description": front_record.get("scene_description"),
                },
                "selected_frame_indices_preview": selected_indices[:24],
                "matched_sample_tokens": matched_sample_tokens,
                "matched_scene_tokens": matched_scene_tokens,
                "unique_selected_sample_token_count": len(selected_sample_tokens),
                "unique_selected_scene_token_count": len(selected_scene_tokens),
                "claim_boundary": {
                    "runtime_sample_selector_verified": True,
                    "source_sample_binding_is_not_gpu_approval": True,
                    "source_sample_binding_is_not_video_semantic_success": True,
                },
            }

    return {
        "schema_version": "driveloop_source_sample_binding.v0",
        "requested": True,
        "ready": False,
        "selector": selector,
        "dataset_dir": str(dataset_dir),
        "labels_path": str(labels_path),
        "record_count": len(records),
        "candidate_start_count": len(starts),
        "target_sample_token_count": len(target_sample_tokens),
        "target_scene_token_count": len(target_scene_tokens),
        "reason": "no_dd2_candidate_contains_requested_source_tokens",
        "claim_boundary": {
            "runtime_sample_selector_verified": False,
            "source_sample_binding_is_not_gpu_approval": True,
            "source_sample_binding_is_not_video_semantic_success": True,
        },
    }
