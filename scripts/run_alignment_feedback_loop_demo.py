from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Dict, List

from driveloop import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.backends.mock import MockGenerationBackend
from driveloop.evaluators import BaseEvaluator
from driveloop.schema import Diagnosis, Evaluation, Generation


class AlignmentFeedbackDemoEvaluator(BaseEvaluator):
    """Deterministic evaluator for demonstrating feedback control flow only."""

    def __init__(self, failed_checks: List[str] | None = None) -> None:
        self.calls = 0
        self.failed_checks = failed_checks or [
            "object_presence.motorcycle",
            "spatial_relation.left_lane_change",
        ]

    def evaluate(self, generation: Generation) -> Evaluation:
        self.calls += 1
        if self.calls == 1:
            return Evaluation(
                score=0.0,
                diagnosis=Diagnosis(
                    passed=False,
                    reasons=[f"alignment_check_failed:{check}" for check in self.failed_checks],
                    suggested_actions=["inspect failed alignment checks before making semantic claims"],
                ),
            )
        return Evaluation(score=1.0, diagnosis=Diagnosis(passed=True))


def failed_checks_from_alignment_report(path: str | None) -> List[str] | None:
    if path is None:
        return None

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("alignment report must be a JSON object")

    report = data
    for key in ("prompt_video_alignment", "video_alignment_report", "perception_alignment"):
        value = data.get(key)
        if isinstance(value, dict):
            report = value
            break

    checks = report.get("checks", [])
    if not isinstance(checks, list):
        raise ValueError("alignment report checks must be a list")

    failed: List[str] = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        required = bool(check.get("required", True))
        passed = bool(check.get("passed", False))
        name = check.get("name")
        if required and not passed and isinstance(name, str):
            failed.append(name)

    return failed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Demonstrate DriveLoop alignment feedback control flow with a mock backend."
    )
    parser.add_argument(
        "--prompt",
        default="daytime urban road",
        help="Initial prompt before alignment feedback refinement.",
    )
    parser.add_argument("--scenario-id", default="alignment_feedback_loop_demo")
    parser.add_argument("--output-dir", default="outputs/driveloop/alignment_feedback_loop_demo")
    parser.add_argument("--target-score", type=float, default=0.8)
    parser.add_argument(
        "--alignment-report",
        default=None,
        help="Optional external alignment report whose failed required checks seed the demo evaluator.",
    )
    return parser.parse_args()


def _alignment_trace_from_generation(generation: Generation) -> Dict[str, Any]:
    dd2_condition = generation.metadata.get("dd2_condition", {})
    if not isinstance(dd2_condition, dict):
        return {}

    executable_condition = dd2_condition.get("executable_condition", {})
    if not isinstance(executable_condition, dict):
        return {}

    trace = executable_condition.get("trace_metadata", {})
    if not isinstance(trace, dict):
        return {}

    alignment_feedback = trace.get("alignment_feedback", {})
    return alignment_feedback if isinstance(alignment_feedback, dict) else {}


def run_demo(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = Path(args.output_dir) / args.scenario_id
    backend = MockGenerationBackend(output_dir=output_dir / "artifacts")
    failed_checks = failed_checks_from_alignment_report(getattr(args, "alignment_report", None))
    runner = DriveLoopRunner(
        backend=backend,
        evaluator=AlignmentFeedbackDemoEvaluator(failed_checks=failed_checks),
        config=DriveLoopConfig(
            max_iterations=2,
            target_score=args.target_score,
            output_dir=output_dir,
        ),
    )
    request = DriveLoopRequest(prompt=args.prompt, scenario_id=args.scenario_id)
    result = runner.run(request)

    history = [
        {
            "generation": asdict(generation),
            "evaluation": asdict(evaluation),
        }
        for generation, evaluation in result.history
    ]

    alignment_trace = {}
    if result.history:
        alignment_trace = _alignment_trace_from_generation(result.history[-1][0])

    payload = {
        "scenario_id": args.scenario_id,
        "closed_loop_control_flow": "demonstrated_with_mock_backend",
        "tensor_control_claim": "not_evaluated",
        "video_semantic_claim": "not_evaluated",
        "claim_boundary": (
            "This demo proves DriveLoop feedback control flow with a mock backend. "
            "It does not run DD2 diffusion, inspect video pixels, or prove prompt-video semantic alignment."
        ),
        "iterations": len(result.history),
        "alignment_feedback_trace_present": bool(alignment_trace),
        "alignment_report_source": getattr(args, "alignment_report", None),
        "alignment_feedback_trace": alignment_trace,
        "initial_prompt": result.request.prompt,
        "final_prompt": result.best_generation.prompt,
        "best_evaluation": asdict(result.best_evaluation),
        "history": history,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "alignment_feedback_loop_demo_summary.json"
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> None:
    payload = run_demo(parse_args())
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
