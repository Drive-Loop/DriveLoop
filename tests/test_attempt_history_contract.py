from __future__ import annotations

import json
import tempfile
from pathlib import Path

from driveloop import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.backends import MockGenerationBackend


REQUIRED_ATTEMPT_FIELDS = {
    "iteration",
    "request",
    "scene_specification",
    "long_tail_condition_plan",
    "dd2_condition",
    "condition_package",
    "source_binding",
    "generation",
    "source_selection",
    "evaluation",
    "refinement",
    "status",
    "claim_boundary",
}

REQUIRED_CLAIM_BOUNDARY_FIELDS = {
    "attempt_record_is_not_video_semantic_success",
    "generation_artifact_is_not_semantic_success",
    "runtime_trace_is_not_semantic_success",
    "semantic_success_requires_measured_passed_alignment_eval",
    "source_binding_is_not_gpu_approval",
    "evaluation_passed",
}


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_history_jsonl_records_required_paper_attempt_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = DriveLoopRunner(
            backend=MockGenerationBackend(output_dir=root / "artifacts"),
            config=DriveLoopConfig(
                max_iterations=3,
                target_score=0.8,
                output_dir=root / "history",
            ),
        ).run(DriveLoopRequest(prompt="make a driving video"))

        records = _read_jsonl(root / "history" / "history.jsonl")

    assert len(records) == len(result.attempt_history)
    assert [record["attempt"]["status"] for record in records] == [
        attempt.status for attempt in result.attempt_history
    ]

    for iteration, record in enumerate(records):
        assert {"generation", "evaluation", "attempt"}.issubset(record)

        attempt = record["attempt"]
        assert REQUIRED_ATTEMPT_FIELDS.issubset(attempt)
        assert attempt["iteration"] == iteration
        assert attempt["generation"] == record["generation"]
        assert attempt["evaluation"] == record["evaluation"]

        assert attempt["request"]["prompt"]
        assert attempt["scene_specification"]["prompt"]
        assert isinstance(attempt["long_tail_condition_plan"]["prompt_suffixes"], list)

        assert (
            attempt["dd2_condition"]["executable_condition"]["schema_version"]
            == "dd2_executable_condition.v0"
        )
        assert (
            attempt["condition_package"]["schema_version"]
            == "driveloop_attempt_condition_package.v0"
        )
        assert "unsupported_controls" in attempt["condition_package"]
        assert isinstance(attempt["source_binding"], dict)

        assert attempt["status"] in {
            "accepted",
            "needs_refinement",
            "source_binding_unavailable",
            "source_selection_unavailable",
        }

        claim_boundary = attempt["claim_boundary"]
        assert REQUIRED_CLAIM_BOUNDARY_FIELDS.issubset(claim_boundary)
        assert claim_boundary["attempt_record_is_not_video_semantic_success"] is True
        assert claim_boundary["generation_artifact_is_not_semantic_success"] is True
        assert claim_boundary["runtime_trace_is_not_semantic_success"] is True
