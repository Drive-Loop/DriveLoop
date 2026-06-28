from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Dict

from driveloop import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.backends.mock import MockGenerationBackend
from driveloop.evaluators import BaseEvaluator
from driveloop.schema import Diagnosis, Evaluation, Generation


class AlignmentFeedbackDemoEvaluator(BaseEvaluator):
    """Deterministic evaluator for demonstrating feedback control flow only."""

    def __init__(self) -> None:
        self.calls = 0

    def evaluate(self, generation: Generation) -> Evaluation:
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
    runner = DriveLoopRunner(
        backend=backend,
        evaluator=AlignmentFeedbackDemoEvaluator(),
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
