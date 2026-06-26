from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from driveloop import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.backends import MockGenerationBackend


class DriveLoopRunnerTest(unittest.TestCase):
    def test_refines_until_target_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config = DriveLoopConfig(
                max_iterations=3,
                target_score=0.8,
                output_dir=root / "history",
            )
            backend = MockGenerationBackend(output_dir=root / "artifacts")
            request = DriveLoopRequest(prompt="make a driving video")

            result = DriveLoopRunner(backend=backend, config=config).run(request)

            self.assertEqual(result.best_generation.iteration, 1)
            self.assertGreaterEqual(result.best_evaluation.score, 0.8)
            self.assertEqual(len(result.history), 2)
            self.assertIn("realistic autonomous driving scene", result.best_generation.prompt)
            self.assertTrue((root / "history" / "history.jsonl").exists())
            self.assertTrue((root / "artifacts" / "iteration_01.txt").exists())

    def test_good_prompt_stops_after_one_iteration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DriveLoopConfig(
                max_iterations=3,
                target_score=0.8,
                output_dir=Path(tmpdir) / "history",
            )
            backend = MockGenerationBackend(output_dir=Path(tmpdir) / "artifacts")
            request = DriveLoopRequest(
                prompt=(
                    "rainy realistic autonomous driving scene, panoramic multi-view "
                    "video with a vehicle cut in"
                )
            )

            result = DriveLoopRunner(backend=backend, config=config).run(request)

            self.assertEqual(len(result.history), 1)
            self.assertEqual(result.best_generation.iteration, 0)
            self.assertTrue(result.best_evaluation.diagnosis.passed)


if __name__ == "__main__":
    unittest.main()


def test_runner_passes_dd2_condition_to_backend_request():
    from driveloop.backends.base import GenerationBackend
    from driveloop.schema import Generation

    class CapturingBackend(GenerationBackend):
        def __init__(self):
            self.requests = []

        def generate(self, request, iteration):
            self.requests.append(request)
            return Generation(
                iteration=iteration,
                prompt=request.prompt,
                artifacts={},
                metadata={"backend": "capture"},
            )

    with tempfile.TemporaryDirectory() as tmpdir:
        backend = CapturingBackend()
        config = DriveLoopConfig(
            max_iterations=1,
            target_score=0.5,
            output_dir=Path(tmpdir) / "history",
        )
        request = DriveLoopRequest(
            prompt="rainy night intersection, a pedestrian crosses in front while a car cuts in"
        )

        DriveLoopRunner(backend=backend, config=config).run(request)

    assert backend.requests
    dd2_condition = backend.requests[0].condition["dd2_condition"]
    assert dd2_condition["environment"]["weather"] == "rain"
    assert dd2_condition["environment"]["lighting"] == "night"
    assert "crossing" in dd2_condition["motion_primitives"]
    assert "cut_in" in dd2_condition["motion_primitives"]
    assert "text_prompt" in dd2_condition
