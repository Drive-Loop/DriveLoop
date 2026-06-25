from __future__ import annotations

import argparse
import json

from driveloop import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.backends import MockGenerationBackend


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a DriveLoop mock closed-loop demo.")
    parser.add_argument("--prompt", required=True, help="Initial driving scenario prompt.")
    parser.add_argument("--scenario-id", default=None, help="Optional scenario identifier.")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--target-score", type=float, default=0.8)
    parser.add_argument("--output-dir", default="outputs/driveloop/mock_demo")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = DriveLoopConfig(
        max_iterations=args.max_iterations,
        target_score=args.target_score,
        output_dir=args.output_dir,
    )
    request = DriveLoopRequest(
        prompt=args.prompt,
        scenario_id=args.scenario_id,
    )
    backend = MockGenerationBackend(output_dir=f"{args.output_dir}/artifacts")
    result = DriveLoopRunner(backend=backend, config=config).run(request)

    payload = {
        "request": {
            "prompt": result.request.prompt,
            "scenario_id": result.request.scenario_id,
        },
        "best_generation": {
            "iteration": result.best_generation.iteration,
            "prompt": result.best_generation.prompt,
            "artifacts": result.best_generation.artifacts,
        },
        "best_evaluation": {
            "score": result.best_evaluation.score,
            "metrics": result.best_evaluation.metrics,
            "diagnosis": {
                "passed": result.best_evaluation.diagnosis.passed,
                "reasons": result.best_evaluation.diagnosis.reasons,
                "suggested_actions": result.best_evaluation.diagnosis.suggested_actions,
            },
        },
        "iterations": len(result.history),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
