from __future__ import annotations

import argparse
import json
from pathlib import Path

from driveloop.experiment_pipeline import (
    ExperimentPipeline,
    ExperimentPipelineConfig,
    load_experiment_cases,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a no-GPU DriveLoop experiment manifest.")
    parser.add_argument("--cases", required=True, help="JSON manifest with a cases list")
    parser.add_argument("--output-dir", required=True, help="Directory for experiment records")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--target-score", type=float, default=0.8)
    parser.add_argument("--backend", choices=["mock"], default="mock")
    args = parser.parse_args(argv)

    summary = ExperimentPipeline(
        output_dir=Path(args.output_dir),
        config=ExperimentPipelineConfig(
            max_iterations=args.max_iterations,
            target_score=args.target_score,
            backend_name=args.backend,
        ),
    ).run_cases(load_experiment_cases(args.cases))
    print(json.dumps({
        "summary_json": str(Path(args.output_dir) / "summary.json"),
        "summary_md": str(Path(args.output_dir) / "summary.md"),
        "case_count": summary["case_count"],
        "accepted_count": summary["accepted_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
