from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from driveloop import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.backends import DriveDreamer2Backend


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DriveLoop with DriveDreamer-2 backend.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--scenario-id", default="drivedreamer2_backend_demo")
    parser.add_argument("--max-iterations", type=int, default=1)
    parser.add_argument("--target-score", type=float, default=0.90)
    parser.add_argument("--output-dir", default="outputs/driveloop/drivedreamer2_backend_demo")
    parser.add_argument("--config-name", default="drivedreamer2_img_cond_mini_local")
    parser.add_argument("--dd2-batch-skip", type=int, default=0)
    parser.add_argument("--audit-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    request = DriveLoopRequest(
        prompt=args.prompt,
        scenario_id=args.scenario_id,
    )
    config = DriveLoopConfig(
        max_iterations=args.max_iterations,
        target_score=args.target_score,
        output_dir=args.output_dir,
    )
    backend = DriveDreamer2Backend(
        project_root=".",
        config_name=args.config_name,
        artifact_dir=f"{args.output_dir}/artifacts",
    )

    result = DriveLoopRunner(backend=backend, config=config).run(request)
    print(
        json.dumps(
            {
                "request": asdict(result.request),
                "best_generation": asdict(result.best_generation),
                "best_evaluation": asdict(result.best_evaluation),
                "iterations": len(result.history),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
