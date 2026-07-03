from __future__ import annotations

import json
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
            self.assertEqual(len(result.attempt_history), 2)
            self.assertEqual(result.attempt_history[0].status, "needs_refinement")
            self.assertEqual(result.attempt_history[1].status, "accepted")
            self.assertIn("realistic autonomous driving scene", result.best_generation.prompt)
            history_path = root / "history" / "history.jsonl"
            self.assertTrue(history_path.exists())
            records = [json.loads(line) for line in history_path.read_text().splitlines()]
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["attempt"]["status"], "needs_refinement")
            self.assertEqual(records[1]["attempt"]["status"], "accepted")
            self.assertEqual(
                records[0]["attempt"]["condition_package"]["schema_version"],
                "driveloop_attempt_condition_package.v0",
            )
            self.assertTrue(records[0]["attempt"]["claim_boundary"]["attempt_record_is_not_video_semantic_success"])
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

def test_runner_refines_prompt_from_alignment_diagnostics():
    from driveloop.evaluators import BaseEvaluator
    from driveloop.schema import Diagnosis, Evaluation

    class AlignmentThenPassEvaluator(BaseEvaluator):
        def __init__(self):
            self.calls = 0

        def evaluate(self, generation):
            self.calls += 1
            if self.calls == 1:
                return Evaluation(
                    score=0.0,
                    diagnosis=Diagnosis(
                        passed=False,
                        reasons=[
                            "alignment_check_failed:object_presence.motorcycle",
                            "alignment_check_failed:spatial_relation.left_lane_change",
                        ],
                        suggested_actions=["inspect failed alignment checks before making semantic claims"],
                    ),
                )
            return Evaluation(score=1.0, diagnosis=Diagnosis(passed=True))

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        evaluator = AlignmentThenPassEvaluator()
        backend = MockGenerationBackend(output_dir=root / "artifacts")
        config = DriveLoopConfig(
            max_iterations=2,
            target_score=0.8,
            output_dir=root / "history",
        )
        request = DriveLoopRequest(prompt="daytime urban road")

        result = DriveLoopRunner(
            backend=backend,
            evaluator=evaluator,
            config=config,
        ).run(request)

    assert len(result.history) == 2
    assert result.best_evaluation.score == 1.0
    assert "a motorcycle must be visibly present" in result.best_generation.prompt
    assert "the motorcycle performs a visible lane change from the left" in result.best_generation.prompt

def test_runner_carries_alignment_feedback_to_next_backend_request():
    from driveloop.backends.base import GenerationBackend
    from driveloop.evaluators import BaseEvaluator
    from driveloop.schema import Diagnosis, Evaluation, Generation

    class CapturingBackend(GenerationBackend):
        def __init__(self):
            self.requests = []

        def generate(self, request, iteration):
            self.requests.append(request)
            return Generation(iteration=iteration, prompt=request.prompt, artifacts={}, metadata={})

    class AlignmentThenPassEvaluator(BaseEvaluator):
        def __init__(self):
            self.calls = 0

        def evaluate(self, generation):
            self.calls += 1
            if self.calls == 1:
                return Evaluation(
                    score=0.0,
                    diagnosis=Diagnosis(
                        passed=False,
                        reasons=["alignment_check_failed:object_presence.motorcycle"],
                        suggested_actions=["inspect failed alignment checks before making semantic claims"],
                    ),
                )
            return Evaluation(score=1.0, diagnosis=Diagnosis(passed=True))

    with tempfile.TemporaryDirectory() as tmpdir:
        backend = CapturingBackend()
        config = DriveLoopConfig(
            max_iterations=2,
            target_score=0.8,
            output_dir=Path(tmpdir) / "history",
        )
        DriveLoopRunner(
            backend=backend,
            evaluator=AlignmentThenPassEvaluator(),
            config=config,
        ).run(DriveLoopRequest(prompt="daytime urban road"))

    assert len(backend.requests) == 2
    feedback = backend.requests[1].condition["alignment_feedback"]
    assert feedback["schema_version"] == "driveloop_alignment_feedback.v0"
    assert feedback["status"] == "measured_failed"
    assert feedback["control_level"] == "text_feedback_only"
    assert feedback["failed_checks"] == ["object_presence.motorcycle"]
    assert "dd2_condition" in backend.requests[1].condition

    trace = backend.requests[1].condition["dd2_condition"]["executable_condition"]["trace_metadata"]
    assert trace["alignment_feedback"]["status"] == "measured_failed"
    assert trace["alignment_feedback"]["control_level"] == "text_feedback_only"
    assert trace["tensor_control_ready"] is False

def test_runner_records_paper_attempt_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        backend = MockGenerationBackend(output_dir=root / "artifacts")
        config = DriveLoopConfig(
            max_iterations=1,
            target_score=0.5,
            output_dir=root / "history",
        )
        request = DriveLoopRequest(
            prompt="night realistic autonomous driving scene with a motorcycle cut in"
        )

        result = DriveLoopRunner(backend=backend, config=config).run(request)

    assert len(result.attempt_history) == 1
    attempt = result.attempt_history[0]
    generation, evaluation = result.history[0]

    assert attempt.iteration == 0
    assert attempt.request == request
    assert attempt.scene_specification.prompt == request.prompt
    assert "motorcycle" in [actor.category for actor in attempt.scene_specification.objects]
    assert "cut_in" in attempt.scene_specification.motion_primitives
    assert attempt.dd2_condition["text_prompt"].startswith("night realistic autonomous driving scene")
    assert attempt.dd2_condition["executable_condition"]["schema_version"] == "dd2_executable_condition.v0"
    assert attempt.condition_package["schema_version"] == "driveloop_attempt_condition_package.v0"
    assert "trajectory_control" in attempt.condition_package["unsupported_controls"]
    assert attempt.generation == generation
    assert attempt.evaluation == evaluation
    assert attempt.claim_boundary["attempt_record_is_not_video_semantic_success"] is True


def test_runner_attempt_state_records_source_binding_failure():
    from driveloop.backends.base import GenerationBackend
    from driveloop.schema import Generation

    class SourceBindingBackend(GenerationBackend):
        def generate(self, request, iteration):
            return Generation(
                iteration=iteration,
                prompt=request.prompt,
                artifacts={},
                metadata={
                    "backend": "source_binding_test",
                    "dd2_source_sample_binding": {
                        "requested": True,
                        "ready": False,
                        "reason": "no_dd2_candidate_contains_requested_source_tokens",
                        "claim_boundary": {
                            "source_sample_binding_is_not_gpu_approval": True,
                        },
                    },
                },
            )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = DriveLoopConfig(
            max_iterations=1,
            target_score=0.5,
            output_dir=Path(tmpdir) / "history",
        )
        result = DriveLoopRunner(
            backend=SourceBindingBackend(),
            config=config,
        ).run(DriveLoopRequest(prompt="rainy realistic autonomous driving scene with a vehicle cut in"))

    attempt = result.attempt_history[0]
    assert attempt.status == "source_binding_unavailable"
    assert attempt.source_binding["ready"] is False
    assert attempt.claim_boundary["source_binding_is_not_gpu_approval"] is True
