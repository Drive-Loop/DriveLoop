from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from pyquaternion import Quaternion

from dd_scripts.converters.nuscenes_converter import (
    NuScenesConverter,
    get_map_geom,
    line_geoms_to_vectors,
    poly_geoms_to_vectors,
    quaternion_yaw,
    view_points_depth,
)
from scripts.run_candidate70_hdmap_geometry_introspection_audit import (
    DEFAULT_PROBE,
    array_signature,
    geometry_counts,
    load_json,
    rasterize_vectors,
    vector_stats,
)


DEFAULT_OUTPUT = Path(
    "outputs/driveloop/candidate70_hdmap_lane_geometry_replacement_candidate/"
    "candidate70_lane_geometry_replacement_candidate_summary.json"
)
DEFAULT_IMAGES_DIR = Path("outputs/driveloop/candidate70_hdmap_lane_geometry_replacement_candidate/images")


def diff_image(a: Image.Image, b: Image.Image) -> Image.Image:
    arr_a = np.asarray(a.convert("RGB"), dtype=np.int16)
    arr_b = np.asarray(b.convert("RGB"), dtype=np.int16)
    return Image.fromarray(np.abs(arr_a - arr_b).astype(np.uint8))


def build_raw_local_map_vectors(
    converter: NuScenesConverter,
    cam_token: str,
    scene_token: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], np.ndarray]:
    cam_record = converter.nusc.get("sample_data", cam_token)
    pose_record = converter.nusc.get("ego_pose", cam_record["ego_pose_token"])
    cs_record = converter.nusc.get("calibrated_sensor", cam_record["calibrated_sensor_token"])
    cam_intrinsic = np.array(cs_record["camera_intrinsic"])
    ego2global_translation = np.array(pose_record["translation"])
    rotation = Quaternion(pose_record["rotation"])
    map_pose = ego2global_translation[:2]
    patch_box = (map_pose[0], map_pose[1], 102.4, 102.4)
    patch_angle = quaternion_yaw(rotation) / np.pi * 180
    location = converter.nusc.get("log", converter.nusc.get("scene", scene_token)["log_token"])["location"]
    nusc_map = converter.nusc_maps[location]
    map_explorer = converter.map_explorer[location]

    line_geom = get_map_geom(patch_box, patch_angle, ["road_divider", "lane_divider"], nusc_map, map_explorer)
    line_vector_dict = line_geoms_to_vectors(line_geom)
    ped_geom = get_map_geom(patch_box, patch_angle, ["ped_crossing"], nusc_map, map_explorer)
    ped_vector_list = line_geoms_to_vectors(ped_geom)["ped_crossing"]
    polygon_geom = get_map_geom(patch_box, patch_angle, ["road_segment", "lane"], nusc_map, map_explorer)
    poly_bound_list = poly_geoms_to_vectors(polygon_geom)

    vectors: list[dict[str, Any]] = []
    for line_type, vects in line_vector_dict.items():
        for line, length in vects:
            label = converter.class2label.get(line_type, -1)
            if label != -1:
                pts = np.asarray(line, dtype=np.float64)
                vectors.append({
                    "pts": np.concatenate((pts, np.zeros((pts.shape[0], 1))), axis=1),
                    "pts_num": int(length),
                    "type": int(label),
                    "type_name": line_type,
                })

    for ped_line, length in ped_vector_list:
        label = converter.class2label.get("ped_crossing", -1)
        if label != -1:
            pts = np.asarray(ped_line, dtype=np.float64)
            vectors.append({
                "pts": np.concatenate((pts, np.zeros((pts.shape[0], 1))), axis=1),
                "pts_num": int(length),
                "type": int(label),
                "type_name": "ped_crossing",
            })

    for contour, length in poly_bound_list:
        label = converter.class2label.get("contours", -1)
        if label != -1:
            pts = np.asarray(contour, dtype=np.float64)
            vectors.append({
                "pts": np.concatenate((pts, np.zeros((pts.shape[0], 1))), axis=1),
                "pts_num": int(length),
                "type": int(label),
                "type_name": "contours",
            })

    metadata = {
        "location": location,
        "patch_box": list(patch_box),
        "patch_angle": float(patch_angle),
        "coordinate_frame": "ego_aligned_local_map_patch",
        "imsize": [cam_record["width"], cam_record["height"]],
        "raw_geometry_counts": geometry_counts(line_vector_dict, ped_vector_list, poly_bound_list),
    }
    return vectors, metadata, cs_record, cam_intrinsic


def project_vectors(
    raw_vectors: list[dict[str, Any]],
    cs_record: dict[str, Any],
    cam_intrinsic: np.ndarray,
    *,
    local_x_offset_m: float = 0.0,
    local_y_offset_m: float = 0.0,
    target_type_name: str = "lane_divider",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    projected_vectors: list[dict[str, Any]] = []
    modified_count = 0
    modified_visible_count = 0
    modified_total_pts_num = 0
    sensor_translation = np.array(cs_record["translation"]).reshape((-1, 1))
    sensor_rotation = Quaternion(cs_record["rotation"]).rotation_matrix.T
    local_offset = np.array([local_x_offset_m, local_y_offset_m, 0.0], dtype=np.float64)

    for raw_vector in raw_vectors:
        pts = np.asarray(raw_vector["pts"], dtype=np.float64).copy()
        offset_applied = raw_vector.get("type_name") == target_type_name and (
            local_x_offset_m != 0.0 or local_y_offset_m != 0.0
        )
        if offset_applied:
            pts = pts + local_offset
            modified_count += 1

        pts3d = pts.T
        pts3d = pts3d - sensor_translation
        pts3d = np.dot(sensor_rotation, pts3d)
        projected, depth = view_points_depth(pts3d, cam_intrinsic, normalize=True)
        visible = depth > 1e-3
        visible_pts_num = int(int(raw_vector.get("pts_num", 0) or 0) - int((depth <= 1e-3).sum()))

        projected_vector = {
            "pts": projected[:2, visible].T,
            "pts_num": visible_pts_num,
            "source_pts_num": int(raw_vector.get("pts_num", 0) or 0),
            "visible_depth_positive": int(visible.sum()),
            "type": int(raw_vector["type"]),
            "type_name": raw_vector["type_name"],
        }
        if offset_applied:
            projected_vector["candidate_geometry_operation"] = {
                "operation": "offset_lane_divider_local_map_vector_before_camera_projection",
                "coordinate_frame": "ego_aligned_local_map_patch",
                "local_x_offset_m": local_x_offset_m,
                "local_y_offset_m": local_y_offset_m,
            }
            modified_total_pts_num += visible_pts_num
            if visible_pts_num >= 2:
                modified_visible_count += 1

        projected_vectors.append(projected_vector)

    operation = {
        "operation": "offset_lane_divider_local_map_vector_before_camera_projection",
        "target_type_name": target_type_name,
        "coordinate_frame": "ego_aligned_local_map_patch",
        "local_x_offset_m": local_x_offset_m,
        "local_y_offset_m": local_y_offset_m,
        "modified_count": modified_count,
        "modified_visible_count": modified_visible_count,
        "modified_total_pts_num": modified_total_pts_num,
        "projection_stage": "before_camera_extrinsic_and_intrinsic_projection",
    }
    return projected_vectors, operation


def build_frame_record(
    converter: NuScenesConverter,
    probe_record: dict[str, Any],
    images_dir: Path,
    local_x_offset_m: float,
    local_y_offset_m: float,
) -> dict[str, Any]:
    cam_token = str(probe_record["cam_token"])
    scene_token = str(probe_record["scene_token"])
    raw_vectors, metadata, cs_record, cam_intrinsic = build_raw_local_map_vectors(converter, cam_token, scene_token)

    baseline_vectors, _ = project_vectors(raw_vectors, cs_record, cam_intrinsic)
    candidate_vectors, operation = project_vectors(
        raw_vectors,
        cs_record,
        cam_intrinsic,
        local_x_offset_m=local_x_offset_m,
        local_y_offset_m=local_y_offset_m,
    )

    baseline = rasterize_vectors(baseline_vectors, metadata["imsize"])
    candidate = rasterize_vectors(candidate_vectors, metadata["imsize"])
    diff = diff_image(baseline, candidate)

    frame_index = int(probe_record.get("i", 0))
    data_index = probe_record.get("data_index")
    frame_prefix = f"candidate70_frame_{frame_index:02d}_idx_{data_index}"
    images_dir.mkdir(parents=True, exist_ok=True)

    candidate_path = images_dir / f"{frame_prefix}_lane_geometry_replacement_candidate.png"
    diff_path = images_dir / f"{frame_prefix}_lane_geometry_replacement_candidate_diff.png"
    candidate.save(candidate_path)
    diff.save(diff_path)

    baseline_signature = array_signature(baseline)
    candidate_signature = array_signature(candidate)
    diff_signature = array_signature(diff)
    converter_signature = probe_record.get("converter_signature", {})
    baseline_matches_converter = baseline_signature.get("sha256") == converter_signature.get("sha256")
    candidate_differs_from_baseline = candidate_signature.get("sha256") != baseline_signature.get("sha256")

    return {
        "i": frame_index,
        "data_index": data_index,
        "frame_idx": probe_record.get("frame_idx"),
        "cam_token": cam_token,
        "scene_token": scene_token,
        "geometry_metadata": metadata,
        "baseline_vector_stats": vector_stats(baseline_vectors),
        "candidate_vector_stats": vector_stats(candidate_vectors),
        "operation": operation,
        "baseline_signature": baseline_signature,
        "converter_signature": converter_signature,
        "baseline_matches_converter_signature": baseline_matches_converter,
        "candidate_raster_path": str(candidate_path),
        "candidate_signature": candidate_signature,
        "diff_path": str(diff_path),
        "diff_signature": diff_signature,
        "candidate_differs_from_baseline": candidate_differs_from_baseline,
        "diff_nonzero": int(diff_signature.get("nonzero", 0) or 0),
        "claim_boundary": {
            "candidate_is_local_map_vector_geometry_operation": True,
            "candidate_is_not_direct_nuscenes_database_edit": True,
            "candidate_raster_is_not_video_semantic_success": True,
            "does_not_run_gpu": True,
        },
    }


def build_summary(
    records: list[dict[str, Any]],
    probe_path: Path,
    raw_root: str,
    local_x_offset_m: float,
    local_y_offset_m: float,
) -> dict[str, Any]:
    baseline_match_true = sum(1 for record in records if record.get("baseline_matches_converter_signature") is True)
    baseline_match_false = sum(1 for record in records if record.get("baseline_matches_converter_signature") is False)
    candidate_changed_true = sum(1 for record in records if record.get("candidate_differs_from_baseline") is True)
    candidate_changed_false = sum(1 for record in records if record.get("candidate_differs_from_baseline") is False)
    total_diff_nonzero = sum(int(record.get("diff_nonzero", 0) or 0) for record in records)
    total_modified_visible_lane_dividers = sum(
        int((record.get("operation") or {}).get("modified_visible_count", 0) or 0)
        for record in records
    )
    replacement_candidate_available = (
        bool(records)
        and baseline_match_false == 0
        and candidate_changed_false == 0
        and total_diff_nonzero > 0
        and total_modified_visible_lane_dividers > 0
    )

    return {
        "schema_version": "candidate70_hdmap_lane_geometry_replacement_candidate_builder.v1",
        "audit_only": True,
        "does_not_run_gpu": True,
        "does_not_generate_video": True,
        "does_not_modify_model_inputs": True,
        "probe_path": str(probe_path),
        "raw_root": raw_root,
        "operation": {
            "operation": "offset_lane_divider_local_map_vector_before_camera_projection",
            "target_type_name": "lane_divider",
            "coordinate_frame": "ego_aligned_local_map_patch",
            "local_x_offset_m": local_x_offset_m,
            "local_y_offset_m": local_y_offset_m,
            "geometry_grounded_candidate": True,
        },
        "frame_count": len(records),
        "baseline_match_true": baseline_match_true,
        "baseline_match_false": baseline_match_false,
        "candidate_changed_true": candidate_changed_true,
        "candidate_changed_false": candidate_changed_false,
        "total_diff_nonzero": total_diff_nonzero,
        "total_modified_visible_lane_dividers": total_modified_visible_lane_dividers,
        "records": records,
        "claim": {
            "candidate70_lane_geometry_replacement_candidate_built": bool(records),
            "candidate70_geometry_grounded_replacement_candidate_available": replacement_candidate_available,
            "candidate70_true_lane_geometry_replacement_available": False,
            "hdmap_lane_geometry_override_verified": False,
            "lane_change_control_verified": False,
            "runtime_motion_control_connected": False,
            "semantic_success_claim_allowed": False,
        },
        "claim_boundary": {
            "local_map_vector_offset_is_geometry_grounded_candidate_not_direct_database_edit": True,
            "candidate_raster_requires_runtime_surface_audit_before_gate_use": True,
            "hdmap_raster_diff_is_not_lane_change_control": True,
            "runtime_or_raster_audit_is_not_video_semantic_success": True,
            "gpu_requires_separate_readiness_gate": True,
        },
        "next_required_steps": [
            "Audit whether the local-map-vector geometry candidate reaches DD2 grounding_downsampler_input.",
            "Do not claim video semantic success without measured evaluation.",
            "Do not run GPU without explicit user approval.",
        ],
    }


def run_builder(
    probe_path: Path,
    output_path: Path,
    images_dir: Path,
    local_x_offset_m: float,
    local_y_offset_m: float,
    max_frames: int | None,
) -> dict[str, Any]:
    probe = load_json(probe_path)
    raw_root = str(probe.get("raw_root", "/data/projects/DriveLoop/data/raw/nuscenes"))
    records = probe.get("records", [])
    if not isinstance(records, list) or not records:
        raise SystemExit(f"No records found in probe: {probe_path}")

    version = "v1.0-mini"
    dataroot = Path(raw_root)
    if dataroot.name == version:
        dataroot = dataroot.parent
    converter = NuScenesConverter(
        data_dir=str(dataroot),
        version=version,
        save_path="/tmp/driveloop_candidate70_hdmap_lane_geometry_replacement_candidate_unused",
        save_version="v0.0.1",
    )

    selected_records = records[:max_frames] if max_frames is not None else records
    frame_records = [
        build_frame_record(
            converter=converter,
            probe_record=record,
            images_dir=images_dir,
            local_x_offset_m=local_x_offset_m,
            local_y_offset_m=local_y_offset_m,
        )
        for record in selected_records
        if isinstance(record, dict)
    ]
    summary = build_summary(
        records=frame_records,
        probe_path=probe_path,
        raw_root=raw_root,
        local_x_offset_m=local_x_offset_m,
        local_y_offset_m=local_y_offset_m,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a non-GPU local-map-vector candidate70 HDMap lane-geometry replacement raster.")
    parser.add_argument("--probe-path", type=Path, default=DEFAULT_PROBE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--images-dir", type=Path, default=DEFAULT_IMAGES_DIR)
    parser.add_argument("--local-x-offset-m", type=float, default=0.0)
    parser.add_argument("--local-y-offset-m", type=float, default=-1.5)
    parser.add_argument("--max-frames", type=int, default=None)
    args = parser.parse_args()

    summary = run_builder(
        probe_path=args.probe_path,
        output_path=args.output,
        images_dir=args.images_dir,
        local_x_offset_m=args.local_x_offset_m,
        local_y_offset_m=args.local_y_offset_m,
        max_frames=args.max_frames,
    )
    print(args.output)
    print(json.dumps({
        "schema_version": summary["schema_version"],
        "frame_count": summary["frame_count"],
        "baseline_match_true": summary["baseline_match_true"],
        "baseline_match_false": summary["baseline_match_false"],
        "candidate_changed_true": summary["candidate_changed_true"],
        "candidate_changed_false": summary["candidate_changed_false"],
        "total_diff_nonzero": summary["total_diff_nonzero"],
        "total_modified_visible_lane_dividers": summary["total_modified_visible_lane_dividers"],
        "claim": summary["claim"],
        "claim_boundary": summary["claim_boundary"],
    }, indent=2))


if __name__ == "__main__":
    main()
