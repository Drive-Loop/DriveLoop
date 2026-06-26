from __future__ import annotations

import os
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
        artifact_dir: str | Path = "outputs/driveloop/drivedreamer2_backend/artifacts",
        python_executable: str = "python",
        timeout_seconds: Optional[int] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.config_name = config_name
        self.baseline_output_dir = Path(baseline_output_dir)
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

        return Generation(
            iteration=iteration,
            prompt=request.prompt,
            artifacts={"video": str(artifact_video)},
            metadata={
                "backend": "drivedreamer2",
                "config_name": self.config_name,
                "baseline_video": str(baseline_video),
                "returncode": completed.returncode,
            },
        )
