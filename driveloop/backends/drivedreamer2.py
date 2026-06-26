from __future__ import annotations

import json
import math
import os
import pickle
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from driveloop.backends.base import GenerationBackend
from driveloop.schema import DriveLoopRequest, Generation


class DriveDreamer2Backend(GenerationBackend):
    """Command-line wrapper for the DriveDreamer-2 mini baseline."""

    def __init__(
        self,
        project_root: str | Path = ".",
        config_name: str = "drivedreamer2_img_cond_mini_local",
        baseline_output_dir: str | Path = "/data/projects/DriveLoop/outputs/drivedreamer2_img_cond_mini",
        baseline_dataset_dir: str | Path = "/data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_val/v0.0.2",
        artifact_dir: str | Path = "outputs/driveloop/drivedreamer2_backend/artifacts",
        python_executable: str = "python",
        timeout_seconds: Optional[int] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.config_name = config_name
        self.baseline_output_dir = Path(baseline_output_dir)
        self.baseline_dataset_dir = Path(baseline_dataset_dir)
        self.artifact_dir = Path(artifact_dir)
        self.python_executable = python_executable
        self.timeout_seconds = timeout_seconds

    def generate(self, request: DriveLoopRequest, iteration: int) -> Generation:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

        baseline_video = self.baseline_output_dir / "000000.mp4"
        if baseline_video.exists():
            baseline_video.unlink()

        env = os.environ.copy()
        env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

        dd2_condition = request.condition.get("dd2_condition", {})
        dd2_prompt = dd2_condition.get("text_prompt") if isinstance(dd2_condition, dict) else None
        executable_condition = (
            dd2_condition.get("executable_condition", {})
            if isinstance(dd2_condition, dict)
            else {}
        )
        trace_metadata = (
            executable_condition.get("trace_metadata", {})
            if isinstance(executable_condition, dict)
            else {}
        )
        structural_input_plan = (
            executable_condition.get("structural_input_plan", {})
            if isinstance(executable_condition, dict)
            else {}
        )
        if dd2_prompt:
            env["DRIVELOOP_DD2_PROMPT"] = str(dd2_prompt)

        cmd = [
            self.python_executable,
            "./dreamer-train/projects/launch.py",
            "--project_name",
            "DriveDreamer2",
            "--config_name",
            self.config_name,
            "--runners",
            "drivedreamer2.DriveDreamer2_Tester",
        ]

        completed = subprocess.run(
            cmd,
            cwd=self.project_root,
            env=env,
            check=True,
            text=True,
            timeout=self.timeout_seconds,
        )

        if not baseline_video.exists():
            raise FileNotFoundError(f"DriveDreamer-2 did not create {baseline_video}")

        artifact_video = self.artifact_dir / f"iteration_{iteration:02d}.mp4"
        shutil.copy2(baseline_video, artifact_video)

        baseline_structural_snapshot = self._build_baseline_structural_snapshot()
        structural_request_diff = self._build_structural_request_diff(
            structural_input_plan=structural_input_plan,
            baseline_structural_snapshot=baseline_structural_snapshot,
            trace_metadata=trace_metadata,
        )
        override_candidate_plan = self._build_override_candidate_plan(
            structural_input_plan=structural_input_plan,
            structural_request_diff=structural_request_diff,
            baseline_structural_snapshot=baseline_structural_snapshot,
        )

        return Generation(
            iteration=iteration,
            prompt=request.prompt,
            artifacts={"video": str(artifact_video)},
            metadata={
                "backend": "drivedreamer2",
                "config_name": self.config_name,
                "baseline_video": str(baseline_video),
                "returncode": completed.returncode,
                "dd2_prompt": str(dd2_prompt) if dd2_prompt else None,
                "dd2_executable_condition": executable_condition,
                "dd2_condition_schema_version": executable_condition.get("schema_version")
                if isinstance(executable_condition, dict)
                else None,
                "dd2_tensor_control_ready": trace_metadata.get("tensor_control_ready")
                if isinstance(trace_metadata, dict)
                else None,
                "dd2_structural_input_plan": structural_input_plan,
                "dd2_structural_control_level": structural_input_plan.get("control_level")
                if isinstance(structural_input_plan, dict)
                else None,
                "dd2_baseline_structural_snapshot": baseline_structural_snapshot,
                "dd2_structural_request_diff": structural_request_diff,
                "dd2_override_candidate_plan": override_candidate_plan,
            },
        )

    def _build_override_candidate_plan(
        self,
        structural_input_plan: dict,
        structural_request_diff: dict,
        baseline_structural_snapshot: dict | None = None,
    ) -> dict:
        if not structural_request_diff.get("available", False):
            return {
                "available": False,
                "reason": structural_request_diff.get("reason", "missing_structural_request_diff"),
            }

        actor_label_actions = [
            {"type": "add_actor_label", "label": label}
            for label in structural_request_diff.get("missing_requested_labels", [])
        ]
        actor_label_actions.extend(
            {
                "type": "mark_extra_baseline_label",
                "label": label,
            }
            for label in structural_request_diff.get("extra_baseline_labels", [])
        )

        scene_description_action = {
            "type": "keep_baseline_text",
            "target_value": structural_request_diff.get("baseline_scene_description"),
        }
        if structural_request_diff.get("scene_description_changed"):
            scene_description_action = {
                "type": "replace_text_prompt",
                "target_value": structural_request_diff.get("requested_scene_description"),
            }

        requires_box_synthesis = bool(
            structural_request_diff.get("missing_requested_labels")
        )

        return {
            "available": True,
            "control_level": "candidate_plan_only",
            "scene_description_action": scene_description_action,
            "actor_label_actions": actor_label_actions,
            "requires_box_synthesis": requires_box_synthesis,
            "box_synthesis_plan": self._build_box_synthesis_plan(
                structural_request_diff=structural_request_diff,
                requires_box_synthesis=requires_box_synthesis,
                baseline_structural_snapshot=baseline_structural_snapshot,
            ),
            "requires_hdmap_override": structural_input_plan.get("image_hdmap", {}).get("source")
            != "mini_dataset_baseline",
            "baseline_sources": {
                "image_hdmap": structural_input_plan.get("image_hdmap", {}).get("source"),
                "image_box": structural_input_plan.get("image_box", {}).get("source"),
                "boxes3d": structural_input_plan.get("boxes3d", {}).get("source"),
            },
            "limitations": [
                "tensor_override_not_implemented",
                "box_synthesis_not_implemented",
                "hdmap_override_not_implemented",
            ],
        }

    def _build_box_synthesis_plan(
        self,
        structural_request_diff: dict,
        requires_box_synthesis: bool,
        baseline_structural_snapshot: dict | None = None,
    ) -> dict:
        if not requires_box_synthesis:
            return {
                "available": False,
                "reason": "box_synthesis_not_required",
            }

        actors_to_synthesize = [
            {
                "category": label,
                "source_action": "add_actor_label",
                "confidence": "low",
                "reason": "missing_requested_label",
            }
            for label in structural_request_diff.get("missing_requested_labels", [])
        ]
        placement_policy = "front_adjacent_lane_cut_in"
        box_template_source = "class_default_dimensions"

        return {
            "available": True,
            "control_level": "plan_only",
            "target_tensor": "boxes3d",
            "derived_tensor": "image_box",
            "placement_policy": placement_policy,
            "box_template_source": box_template_source,
            "requires_manual_review": True,
            "actors_to_synthesize": actors_to_synthesize,
            "box_synthesis_draft": self._build_box_synthesis_draft(
                actors_to_synthesize=actors_to_synthesize,
                placement_policy=placement_policy,
                box_template_source=box_template_source,
                baseline_structural_snapshot=baseline_structural_snapshot,
            ),
            "limitations": [
                "3d_position_not_estimated",
                "camera_projection_not_computed",
                "image_box_canvas_not_rendered",
            ],
        }

    def _build_box_synthesis_draft(
        self,
        actors_to_synthesize: list,
        placement_policy: str,
        box_template_source: str,
        baseline_structural_snapshot: dict | None = None,
    ) -> dict:
        default_dimensions = {
            "bicycle": {"width": 0.6, "height": 1.6, "depth": 1.8},
            "pedestrian": {"width": 0.6, "height": 1.7, "depth": 0.6},
            "car": {"width": 1.8, "height": 1.6, "depth": 4.5},
            "truck": {"width": 2.5, "height": 3.0, "depth": 7.0},
            "bus": {"width": 2.6, "height": 3.2, "depth": 10.0},
        }

        draft_boxes3d = []
        for actor in actors_to_synthesize:
            category = actor["category"]
            dims = default_dimensions.get(category)
            if not dims:
                continue
            draft_boxes3d.append(
                {
                    "category": category,
                    "box3d": [
                        8.0,
                        1.8,
                        18.0,
                        dims["width"],
                        dims["height"],
                        dims["depth"],
                        0.0,
                        0.0,
                        -0.25,
                    ],
                    "placement_policy": placement_policy,
                    "source": box_template_source,
                    "requires_projection": True,
                }
            )

        sample = baseline_structural_snapshot.get("sample", {}) if isinstance(baseline_structural_snapshot, dict) else {}
        cam_intrinsic = sample.get("cam_intrinsic") if isinstance(sample, dict) else None
        validation = self._validate_box_synthesis_draft(
            draft_boxes3d,
            cam_intrinsic=cam_intrinsic,
        )

        return {
            "available": bool(draft_boxes3d),
            "control_level": "draft_only",
            "coordinate_frame": "dd2_dataset_frame_unverified",
            "coordinate_frame_verified": False,
            "units": "meters",
            "boxes3d_format": "x_y_z_width_height_depth_rotX_rotY_rotZ",
            "default_dimensions": default_dimensions,
            "draft_boxes3d": draft_boxes3d,
            "validation": validation,
            "limitations": [
                "not_written_to_dataset",
                "3d_position_not_estimated",
                "camera_projection_not_computed",
            ],
        }

    def _validate_box_synthesis_draft(
        self,
        draft_boxes3d: list,
        cam_intrinsic: list | None = None,
    ) -> dict:
        entries = []
        projection_available = self._projection_matrix_available(cam_intrinsic)

        for entry in draft_boxes3d:
            raw_box = entry.get("box3d", []) if isinstance(entry, dict) else []
            numeric_box = []
            numeric = True
            for value in raw_box:
                try:
                    numeric_box.append(float(value))
                except (TypeError, ValueError):
                    numeric = False

            shape_ok = len(raw_box) == 9
            dims_positive = (
                len(numeric_box) == 9
                and numeric_box[3] > 0
                and numeric_box[4] > 0
                and numeric_box[5] > 0
            )
            z_positive = len(numeric_box) == 9 and numeric_box[2] > 0
            projection = None
            if shape_ok and numeric and dims_positive and z_positive and projection_available:
                projection = self._project_box3d_axis_aligned(numeric_box, cam_intrinsic)

            category = entry.get("category") if isinstance(entry, dict) else None
            entries.append(
                {
                    "category": category,
                    "shape_ok": shape_ok,
                    "float32_convertible": numeric and shape_ok,
                    "dimensions_positive": dims_positive,
                    "mean_z_positive": z_positive,
                    "projection_finite": projection.get("finite") if projection else None,
                    "projected_2d_range": projection.get("range") if projection else None,
                    "requires_projection_validation": not projection_available,
                    "image_box_canvas_dry_run": self._build_image_box_canvas_dry_run(
                        category=category,
                        projection=projection,
                    ),
                }
            )

        limitations = [
            "image_box_canvas_not_rendered",
            "dataset_not_written",
        ]
        if projection_available:
            limitations.append("projection_validator_uses_axis_aligned_corners")
        else:
            limitations.append("projection_not_run")

        return {
            "available": bool(entries),
            "control_level": "validator_only",
            "projection_control_level": "validator_only" if projection_available else "not_run",
            "all_entries_valid": bool(entries)
            and all(
                item["shape_ok"]
                and item["float32_convertible"]
                and item["dimensions_positive"]
                and item["mean_z_positive"]
                and (item["projection_finite"] is not False)
                for item in entries
            ),
            "entries": entries,
            "limitations": limitations,
        }

    def _projection_matrix_available(self, cam_intrinsic: list | None) -> bool:
        return (
            isinstance(cam_intrinsic, list)
            and len(cam_intrinsic) >= 3
            and all(isinstance(row, list) and len(row) >= 3 for row in cam_intrinsic[:3])
        )

    def _build_image_box_canvas_dry_run(
        self,
        category: str | None,
        projection: dict | None,
    ) -> dict:
        class_channels = {
            "animal": 0,
            "pedestrian": 1,
            "bicycle": 5,
            "motorcycle": 6,
            "car": 8,
            "truck": 9,
            "bus": 11,
            "barrier": 17,
            "traffic_cone": 18,
        }
        class_channel = class_channels.get(category)
        projected_range = projection.get("range") if projection else None
        projected_box_drawable = (
            bool(projection.get("finite"))
            and projected_range is not None
            and class_channel is not None
        ) if projection else None

        return {
            "control_level": "validator_only",
            "target_shape": [19, 900, 1600],
            "class_channel": class_channel,
            "projected_box_drawable": projected_box_drawable,
            "projected_2d_range": projected_range,
            "canvas_rendered": False,
            "dataset_written": False,
        }

    def _project_box3d_axis_aligned(self, box3d: list, cam_intrinsic: list) -> dict:
        x, y, z, width, height, depth = box3d[:6]
        half_w, half_h, half_d = width / 2.0, height / 2.0, depth / 2.0
        corners = [
            (x + sx * half_w, y + sy * half_h, z + sz * half_d)
            for sx in (-1.0, 1.0)
            for sy in (-1.0, 1.0)
            for sz in (-1.0, 1.0)
        ]

        projected = []
        finite = True
        for cx, cy, cz in corners:
            px = cam_intrinsic[0][0] * cx + cam_intrinsic[0][1] * cy + cam_intrinsic[0][2] * cz
            py = cam_intrinsic[1][0] * cx + cam_intrinsic[1][1] * cy + cam_intrinsic[1][2] * cz
            pz = cam_intrinsic[2][0] * cx + cam_intrinsic[2][1] * cy + cam_intrinsic[2][2] * cz
            if pz == 0:
                finite = False
                continue
            u = px / pz
            v = py / pz
            finite = finite and math.isfinite(u) and math.isfinite(v)
            projected.append((u, v))

        if not projected:
            return {"finite": False, "range": None}

        xs = [point[0] for point in projected]
        ys = [point[1] for point in projected]
        return {
            "finite": finite,
            "range": {
                "min": [round(min(xs), 2), round(min(ys), 2)],
                "max": [round(max(xs), 2), round(max(ys), 2)],
            },
        }


    def _build_structural_request_diff(
        self,
        structural_input_plan: dict,
        baseline_structural_snapshot: dict,
        trace_metadata: dict,
    ) -> dict:
        if not isinstance(structural_input_plan, dict) or not structural_input_plan:
            return {
                "available": False,
                "reason": "missing_structural_input_plan",
            }

        sample = baseline_structural_snapshot.get("sample", {})
        if not sample.get("available", False):
            return {
                "available": False,
                "reason": "missing_baseline_sample",
            }

        requested_labels = list(
            structural_input_plan.get("labels", {}).get("values", [])
        )
        baseline_labels = self._canonicalize_baseline_labels(
            sample.get("labels3d_preview", [])
        )

        requested_scene_description = structural_input_plan.get(
            "scene_description", {}
        ).get("value")
        baseline_scene_description = sample.get("scene_description")

        requested_set = set(requested_labels)
        baseline_set = set(baseline_labels)

        return {
            "available": True,
            "requested_labels": requested_labels,
            "baseline_labels": baseline_labels,
            "missing_requested_labels": sorted(requested_set - baseline_set),
            "extra_baseline_labels": sorted(baseline_set - requested_set),
            "requested_scene_description": requested_scene_description,
            "baseline_scene_description": baseline_scene_description,
            "scene_description_changed": requested_scene_description != baseline_scene_description,
            "tensor_override_ready": trace_metadata.get("tensor_control_ready")
            if isinstance(trace_metadata, dict)
            else None,
        }

    def _canonicalize_baseline_labels(self, labels3d_preview: list) -> list:
        labels = []
        aliases = {
            "vehicle": None,
            "human": None,
            "adult": "pedestrian",
            "child": "pedestrian",
            "bicycle": "bicycle",
            "car": "car",
            "truck": "truck",
            "bus": "bus",
            "motorcycle": "motorcycle",
            "pedestrian": "pedestrian",
        }

        for label in labels3d_preview:
            if isinstance(label, str):
                raw_parts = label.split(".")
            elif isinstance(label, (list, tuple)):
                raw_parts = [str(part) for part in label]
            else:
                continue

            for part in raw_parts:
                canonical = aliases.get(part)
                if canonical:
                    labels.append(canonical)
                    break

        return list(dict.fromkeys(labels))

    def _build_baseline_structural_snapshot(self) -> dict:
        dataset_dir = self.baseline_dataset_dir
        snapshot = {
            "dataset_dir": str(dataset_dir),
            "available": dataset_dir.exists(),
        }
        if not dataset_dir.exists():
            return snapshot

        dataset_config = self._read_json(dataset_dir / "config.json")
        labels_config = self._read_json(dataset_dir / "labels" / "config.json")
        images_config = self._read_json(dataset_dir / "images" / "config.json")
        hdmaps_config = self._read_json(dataset_dir / "hdmaps" / "config.json")

        snapshot.update(
            {
                "dataset_config": self._summarize_config(dataset_config),
                "labels_config": self._summarize_config(labels_config),
                "images_config": self._summarize_config(images_config),
                "hdmaps_config": self._summarize_config(hdmaps_config),
                "sample": self._summarize_first_label_sample(dataset_dir / "labels" / "data.pkl"),
            }
        )
        return snapshot

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {"available": False, "path": str(path)}
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data["available"] = True
        data["path"] = str(path)
        return data

    def _summarize_config(self, config: dict) -> dict:
        return {
            "available": config.get("available", False),
            "path": config.get("path"),
            "class_name": config.get("_class_name"),
            "key_names": list(config.get("_key_names", [])),
            "data_size": config.get("data_size"),
            "data_type": config.get("data_type"),
            "data_name": config.get("data_name"),
            "config_paths": list(config.get("config_paths", [])),
        }

    def _summarize_first_label_sample(self, path: Path) -> dict:
        if not path.exists():
            return {"available": False, "path": str(path)}

        with path.open("rb") as f:
            data = pickle.load(f)

        if not data:
            return {"available": False, "path": str(path), "reason": "empty_data"}

        sample = data[0]
        boxes3d = sample.get("boxes3d")
        ori_labels3d = list(sample.get("ori_labels3d", []))
        labels3d = list(sample.get("labels3d", []))
        calib = sample.get("calib", {})
        cam_intrinsic = (
            calib.get("cam_intrinsic")
            if isinstance(calib, dict)
            else None
        )

        return {
            "available": True,
            "path": str(path),
            "scene_description": sample.get("scene_description"),
            "boxes3d_shape": list(boxes3d.shape) if hasattr(boxes3d, "shape") else None,
            "boxes3d_dtype": str(boxes3d.dtype) if hasattr(boxes3d, "dtype") else None,
            "ori_labels3d_count": len(ori_labels3d),
            "ori_labels3d_preview": ori_labels3d[:8],
            "labels3d_count": len(labels3d),
            "labels3d_preview": labels3d[:8],
            "cam_intrinsic_shape": list(cam_intrinsic.shape)
            if hasattr(cam_intrinsic, "shape")
            else None,
            "cam_intrinsic": cam_intrinsic.tolist()
            if hasattr(cam_intrinsic, "tolist")
            else None,
        }
