"""Provenance of the perception support video and of the DD2 staging output.

Two archive defects made finished runs unauditable. The resolved
--perception-baseline-video decided the support term but reached no artifact, so
which video was subtracted could only be recovered by fingerprinting counters.
And metadata['baseline_video'] named the DD2 tester's own staging output, which
an auditor could mistake for the no-injection baseline: subtracting an arm
against itself yields IoU 1.0 everywhere and fabricates a confirmation.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from driveloop.composite_perception import CompositePerceptionVideoEvaluator
from driveloop.runner import DriveLoopRunner
from driveloop.schema import DriveLoopConfig, DriveLoopRequest, Evaluation, Generation


class _StubBackend:
    def generate(self, request, iteration):
        return Generation(iteration=iteration, prompt=request.prompt)


class _ResolvingEvaluator:
    def __init__(self, resolved):
        self._resolved = resolved

    def resolve_baseline_video(self, generation):
        return self._resolved

    def evaluate(self, generation):
        return Evaluation(1.0, {"perception_measured": 1.0})


class _PlainEvaluator:
    def evaluate(self, generation):
        return Evaluation(1.0, {"perception_measured": 1.0})


def _run(evaluator, tmp_path):
    runner = DriveLoopRunner(
        backend=_StubBackend(),
        evaluator=evaluator,
        config=DriveLoopConfig(max_iterations=1, output_dir=tmp_path / "history"),
    )
    result = runner.run(DriveLoopRequest(prompt="a motorcycle cuts in at night"))
    return result.attempt_history[-1].generation.metadata


def test_resolve_prefers_request_metadata_over_constructor_default():
    evaluator = CompositePerceptionVideoEvaluator(baseline_video="/tmp/ctor.mp4")
    assert evaluator.resolve_baseline_video(Generation(iteration=0, prompt="p")) == "/tmp/ctor.mp4"
    override = Generation(
        iteration=0, prompt="p", metadata={"perception_baseline_video": "/tmp/meta.mp4"}
    )
    assert evaluator.resolve_baseline_video(override) == "/tmp/meta.mp4"


def test_resolve_returns_none_when_no_support_is_configured():
    evaluator = CompositePerceptionVideoEvaluator()
    assert evaluator.resolve_baseline_video(Generation(iteration=0, prompt="p")) is None


def test_runner_archives_the_resolved_support_video(tmp_path):
    support = tmp_path / "support.mp4"
    support.write_bytes(b"support")
    metadata = _run(_ResolvingEvaluator(str(support)), tmp_path)
    assert metadata["perception_baseline_video_resolved"] == str(support)
    assert metadata["perception_baseline_video_exists"] is True


def test_runner_archives_a_missing_support_video_as_missing(tmp_path):
    metadata = _run(_ResolvingEvaluator(str(tmp_path / "absent.mp4")), tmp_path)
    assert metadata["perception_baseline_video_resolved"] == str(tmp_path / "absent.mp4")
    assert metadata["perception_baseline_video_exists"] is False


def test_runner_records_an_unsupported_run_as_null_rather_than_silence(tmp_path):
    metadata = _run(_ResolvingEvaluator(None), tmp_path)
    assert metadata["perception_baseline_video_resolved"] is None
    assert metadata["perception_baseline_video_exists"] is False


def test_runner_stays_silent_for_evaluators_without_support_resolution(tmp_path):
    metadata = _run(_PlainEvaluator(), tmp_path)
    assert "perception_baseline_video_resolved" not in metadata
    assert "perception_baseline_video_exists" not in metadata


def test_dd2_staging_output_key_no_longer_shadows_the_support_baseline():
    src = (REPO_ROOT / "driveloop" / "backends" / "drivedreamer2.py").read_text(encoding="utf-8")
    assert '"dd2_raw_output_video": str(baseline_video),' in src
    assert '"baseline_video": str(baseline_video),' not in src
