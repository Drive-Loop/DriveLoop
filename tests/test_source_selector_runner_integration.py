from __future__ import annotations

import json
import pickle
import tempfile
from pathlib import Path

from driveloop import DD2SourceSelector, DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.backends.base import GenerationBackend
from driveloop.schema import Generation


class SourceSelectionEchoBackend(GenerationBackend):
    def __init__(self) -> None:
        self.requests = []

    def generate(self, request, iteration):
        self.requests.append(request)
        selection = request.metadata.get("source_selection", {})
        return Generation(
            iteration=iteration,
            prompt=request.prompt,
            artifacts={},
            metadata={
                "backend": "source_selection_echo",
                "dd2_source_sample_binding": selection.get("binding", {}),
            },
        )


def write_dataset(root: Path) -> Path:
    labels = root / "labels"
    labels.mkdir(parents=True)
    records = [
        {"cam_type": "CAM_FRONT", "frame_idx": 0, "video_length": 2, "sample_token": "sample_a", "scene_token": "scene_0"},
        {"cam_type": "CAM_FRONT", "frame_idx": 1, "video_length": 2, "sample_token": "sample_b", "scene_token": "scene_0"},
    ]
    with (labels / "data.pkl").open("wb") as handle:
        pickle.dump(records, handle)
    return root


def write_identity(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"frame_summaries": [{"sample_token": "sample_a"}, {"sample_token": "sample_b"}]}),
        encoding="utf-8",
    )
    return path


def test_runner_records_source_selection_in_attempt_and_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        dataset = write_dataset(root / "dataset")
        identity = write_identity(root / "identity.json")
        backend = SourceSelectionEchoBackend()

        result = DriveLoopRunner(
            backend=backend,
            source_selector=DD2SourceSelector(
                dataset,
                source_candidate_id="candidate70",
                identity_summary_path=identity,
                frame_num=2,
                hz_factor=1,
                video_split_rate=1,
                multiview=False,
            ),
            config=DriveLoopConfig(
                max_iterations=1,
                target_score=0.8,
                output_dir=root / "history",
            ),
        ).run(
            DriveLoopRequest(
                prompt="rainy realistic autonomous driving scene with a motorcycle cut in",
            )
        )

        records = [
            json.loads(line)
            for line in (root / "history" / "history.jsonl").read_text().splitlines()
        ]

    assert backend.requests[0].metadata["source_candidate_id"] == "candidate70"
    assert backend.requests[0].metadata["source_selection"]["ready"] is True

    attempt = result.attempt_history[0]
    assert attempt.status == "accepted"
    assert attempt.source_selection["ready"] is True
    assert attempt.source_selection["binding"]["dd2_batch_skip"] == 0
    assert attempt.source_binding["ready"] is True
    assert records[0]["attempt"]["source_selection"]["ready"] is True


def test_runner_marks_source_selection_unavailable_before_acceptance():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        dataset = write_dataset(root / "dataset")

        result = DriveLoopRunner(
            backend=SourceSelectionEchoBackend(),
            source_selector=DD2SourceSelector(
                dataset,
                sample_token="missing_sample",
                frame_num=2,
                hz_factor=1,
                video_split_rate=1,
                multiview=False,
            ),
            config=DriveLoopConfig(
                max_iterations=1,
                target_score=0.8,
                output_dir=root / "history",
            ),
        ).run(
            DriveLoopRequest(
                prompt="rainy realistic autonomous driving scene with a motorcycle cut in",
            )
        )

    attempt = result.attempt_history[0]
    assert attempt.status == "source_selection_unavailable"
    assert attempt.source_selection["ready"] is False
    assert attempt.source_selection["diagnosis"]["status"] == "failed"
    assert attempt.source_binding["ready"] is False
    assert "source_selection_unavailable" in attempt.evaluation.diagnosis.reasons
    assert "no_dd2_candidate_contains_requested_source_tokens" in attempt.evaluation.diagnosis.reasons
    assert attempt.refinement is not None
    assert attempt.refinement.condition["source_selection_feedback"]["status"] == "source_unavailable"
