from __future__ import annotations

import json
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
            },
        )

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
        }
