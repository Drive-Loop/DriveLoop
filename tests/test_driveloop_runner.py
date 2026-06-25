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
