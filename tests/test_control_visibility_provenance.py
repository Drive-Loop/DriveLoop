"""Provenance of S_ctrl's channel composition.

control_visibility_score returns channels, unmeasured, source and a claim
boundary alongside the score. The runner kept only the score and the source, so
no artifact recorded which channels produced an S_ctrl: a reported 0.5 could not
be read back as a two-channel mean without reconstructing it offline. The utility
weights were unarchived for the same reason, so J could only be checked by
guessing them.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from driveloop.runner import DriveLoopRunner
from driveloop.schema import DriveLoopConfig, DriveLoopRequest, Evaluation, Generation

PROMPT = "a motorcycle cuts in front of the ego vehicle at night"


class _StubBackend:
    def generate(self, request, iteration):
        return Generation(iteration=iteration, prompt=request.prompt)


class _MetricsEvaluator:
    def __init__(self, metrics):
        self._metrics = metrics

    def evaluate(self, generation):
        return Evaluation(0.4, dict(self._metrics))


def _run(metrics, tmp_path, use_task_utility=True):
    runner = DriveLoopRunner(
        backend=_StubBackend(),
        evaluator=_MetricsEvaluator(metrics),
        config=DriveLoopConfig(
            max_iterations=1,
            output_dir=tmp_path / "history",
            use_task_utility=use_task_utility,
        ),
    )
    result = runner.run(DriveLoopRequest(prompt=PROMPT))
    return result.attempt_history[-1].generation.metadata


def test_channel_breakdown_reaches_the_archive(tmp_path):
    metadata = _run({"perception_measured": 1.0, "perception_detection_count": 3.0}, tmp_path)
    cv = metadata["control_visibility"]
    assert cv["source"] == "auto_control_visibility"
    assert isinstance(cv["channels"], dict) and cv["channels"]
    assert isinstance(cv["unmeasured"], list)
    assert "claim_boundary" in cv


def test_an_unmeasured_channel_is_archived_as_unmeasured(tmp_path):
    metadata = _run({"perception_measured": 1.0, "perception_detection_count": 3.0}, tmp_path)
    cv = metadata["control_visibility"]
    assert "lighting.night" in cv["unmeasured"]
    assert "lighting_night" not in cv["channels"]


def test_a_measured_brightness_does_not_score_lighting(tmp_path):
    # The lighting channel was removed (2026-07-18 records): illumination
    # is locked to the source scene under source-bound generation, so a
    # brightness threshold measures the source's light, not the arm's.
    # A present brightness metric no longer moves lighting out of
    # unmeasured; it stays unmeasured, like weather.
    metadata = _run(
        {
            "perception_measured": 1.0,
            "perception_detection_count": 3.0,
            "perception_best_view_brightness": 40.0,
        },
        tmp_path,
    )
    cv = metadata["control_visibility"]
    assert "lighting_night" not in cv["channels"]
    assert "lighting.night" in cv["unmeasured"]


def test_utility_weights_and_s_ctrl_source_reach_the_archive(tmp_path):
    metadata = _run({"perception_measured": 1.0, "perception_detection_count": 3.0}, tmp_path)
    utility = metadata["task_utility"]
    assert utility["S_ctrl_source"] == "auto_control_visibility"
    assert utility["weights"] == {"perception": 0.5, "control": 0.3, "intent": 0.2}
    assert "claim_boundary" in utility


def test_a_measured_alignment_archives_no_channel_breakdown(tmp_path):
    metadata = _run(
        {"perception_measured": 1.0, "perception_detection_count": 3.0, "alignment_score": 0.9},
        tmp_path,
    )
    assert metadata["control_visibility"] is None
    assert metadata["task_utility"]["S_ctrl_source"] == "measured_alignment"
    assert metadata["task_utility"]["S_ctrl"] == 0.9


def test_no_utility_no_provenance_keys(tmp_path):
    metadata = _run(
        {"perception_measured": 1.0, "perception_detection_count": 3.0},
        tmp_path,
        use_task_utility=False,
    )
    assert "control_visibility" not in metadata
    assert "task_utility" not in metadata
