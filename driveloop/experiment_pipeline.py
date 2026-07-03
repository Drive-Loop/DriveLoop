from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from driveloop.backends import MockGenerationBackend
from driveloop.runner import DriveLoopRunner
from driveloop.schema import DriveLoopConfig, DriveLoopRequest


@dataclass(frozen=True)
class ExperimentCase:
    name: str
    prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    expected_condition: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentCase":
        if not data.get("name"):
            raise ValueError("experiment case requires a name")
        if not data.get("prompt"):
            raise ValueError(f"experiment case {data.get('name')} requires a prompt")
        return cls(
            name=str(data["name"]),
            prompt=str(data["prompt"]),
            metadata=dict(data.get("metadata", {})),
            tags=list(data.get("tags", [])),
            expected_condition=dict(data.get("expected_condition", {})),
        )


@dataclass(frozen=True)
class ExperimentPipelineConfig:
    max_iterations: int = 3
    target_score: float = 0.8
    backend_name: str = "mock"


def load_experiment_cases(path: Path | str) -> list[ExperimentCase]:
    data = json.loads(Path(path).read_text())
    rows = data["cases"] if isinstance(data, dict) and "cases" in data else data
    if not isinstance(rows, list):
        raise ValueError("experiment manifest must be a list or contain a cases list")
    return [ExperimentCase.from_dict(row) for row in rows]


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_json_default) + "\n")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-").lower()
    return slug or "case"


class ExperimentPipeline:
    def __init__(
        self,
        output_dir: Path | str,
        config: ExperimentPipelineConfig | None = None,
        backend_factory: Callable[[Path], Any] | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.config = config or ExperimentPipelineConfig()
        self.backend_factory = backend_factory or (
            lambda artifact_dir: MockGenerationBackend(output_dir=artifact_dir)
        )

    def run_cases(self, cases: Iterable[ExperimentCase]) -> dict[str, Any]:
        case_list = list(cases)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        records = [self._run_case(case) for case in case_list]
        summary = {
            "schema_version": "driveloop_experiment_summary.v0",
            "backend": self.config.backend_name,
            "case_count": len(records),
            "accepted_count": sum(1 for record in records if record["status"] == "accepted"),
            "semantic_success_claim_allowed_count": sum(
                1 for record in records if record["claim_boundary"]["semantic_success_claim_allowed"]
            ),
            "claim_boundary": {
                "experiment_summary_is_not_video_semantic_success": True,
                "mock_backend_is_not_dd2_gpu_evidence": self.config.backend_name == "mock",
                "semantic_success_requires_measured_passed_alignment_eval": True,
            },
            "cases": records,
        }
        _write_json(self.output_dir / "summary.json", summary)
        (self.output_dir / "summary.md").write_text(self._render_markdown(summary))
        return summary

    def _run_case(self, case: ExperimentCase) -> dict[str, Any]:
        case_dir = self.output_dir / _slugify(case.name)
        metadata = dict(case.metadata)
        metadata.setdefault("experiment_case", case.name)
        if case.tags:
            metadata.setdefault("experiment_tags", case.tags)
        if case.expected_condition:
            metadata.setdefault("expected_condition", case.expected_condition)

        runner = DriveLoopRunner(
            backend=self.backend_factory(case_dir / "artifacts"),
            config=DriveLoopConfig(
                max_iterations=self.config.max_iterations,
                target_score=self.config.target_score,
                output_dir=case_dir / "history",
            ),
        )
        result = runner.run(DriveLoopRequest(prompt=case.prompt, metadata=metadata))
        attempt_records = [asdict(attempt) for attempt in result.attempt_history]

        _write_json(case_dir / "result.json", asdict(result))
        with (case_dir / "attempts.jsonl").open("w", encoding="utf-8") as f:
            for attempt in attempt_records:
                f.write(json.dumps(attempt, ensure_ascii=False, default=_json_default) + "\n")

        accepted = any(attempt.get("status") == "accepted" for attempt in attempt_records)
        semantic_claim_allowed = (
            self.config.backend_name != "mock"
            and bool(result.best_evaluation.diagnosis.passed)
        )
        record = {
            "schema_version": "driveloop_experiment_case_result.v0",
            "name": case.name,
            "tags": case.tags,
            "status": "accepted" if accepted else "failed",
            "best_score": result.best_evaluation.score,
            "attempt_count": len(attempt_records),
            "attempt_statuses": [attempt.get("status") for attempt in attempt_records],
            "diagnosis_reasons": list(result.best_evaluation.diagnosis.reasons),
            "suggested_actions": list(result.best_evaluation.diagnosis.suggested_actions),
            "claim_boundary": {
                "experiment_case_record_is_not_video_semantic_success": True,
                "mock_backend_is_not_dd2_gpu_evidence": self.config.backend_name == "mock",
                "semantic_success_requires_measured_passed_alignment_eval": True,
                "semantic_success_claim_allowed": semantic_claim_allowed,
                "source_selection_ready": any(
                    attempt.get("source_selection", {}).get("ready") is True
                    for attempt in attempt_records
                ),
                "perception_evaluation_enabled": bool(
                    case.metadata.get("perception_evaluation", {}).get("enabled")
                    if isinstance(case.metadata.get("perception_evaluation"), dict)
                    else False
                ),
            },
            "outputs": {
                "case_dir": str(case_dir),
                "result_json": str(case_dir / "result.json"),
                "attempts_jsonl": str(case_dir / "attempts.jsonl"),
                "history_jsonl": str(case_dir / "history" / "history.jsonl"),
            },
        }
        _write_json(case_dir / "case_summary.json", record)
        return record

    def _render_markdown(self, summary: dict[str, Any]) -> str:
        lines = [
            "# DriveLoop Experiment Summary",
            "",
            f"- schema_version: `{summary['schema_version']}`",
            f"- backend: `{summary['backend']}`",
            f"- case_count: `{summary['case_count']}`",
            f"- accepted_count: `{summary['accepted_count']}`",
            f"- semantic_success_claim_allowed_count: `{summary['semantic_success_claim_allowed_count']}`",
            "",
            "| case | status | best_score | attempts | semantic_success_claim_allowed |",
            "| --- | --- | ---: | ---: | --- |",
        ]
        for row in summary["cases"]:
            lines.append(
                f"| {row['name']} | {row['status']} | {row['best_score']:.3f} | "
                f"{row['attempt_count']} | {row['claim_boundary']['semantic_success_claim_allowed']} |"
            )
        lines.extend([
            "",
            "Claim boundary: this file summarizes experiment records only; it is not video semantic-success evidence.",
            "",
        ])
        return "\n".join(lines)
