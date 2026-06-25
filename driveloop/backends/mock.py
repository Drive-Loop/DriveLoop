from __future__ import annotations

from pathlib import Path

from driveloop.backends.base import GenerationBackend
from driveloop.schema import DriveLoopRequest, Generation


class MockGenerationBackend(GenerationBackend):
    """Deterministic backend for testing DriveLoop without GPU or nuScenes data."""

    def __init__(self, output_dir: str | Path = "outputs/driveloop/mock") -> None:
        self.output_dir = Path(output_dir)

    def generate(self, request: DriveLoopRequest, iteration: int) -> Generation:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = self.output_dir / f"iteration_{iteration:02d}.txt"
        artifact_path.write_text(
            f"prompt={request.prompt}\ncondition={request.condition}\n",
            encoding="utf-8",
        )
        return Generation(
            iteration=iteration,
            prompt=request.prompt,
            artifacts={"mock_video": str(artifact_path)},
            metadata={"backend": "mock"},
        )
