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
    parser = argparse.ArgumentParser(description="Run a DriveLoop experiment manifest.")
    parser.add_argument("--cases", required=True, help="JSON manifest with a cases list")
    parser.add_argument("--output-dir", required=True, help="Directory for experiment records")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--target-score", type=float, default=0.8)
    parser.add_argument("--backend", choices=["mock", "drivedreamer2"], default="mock")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--config-name", default="drivedreamer2_img_cond_mini_local")
    parser.add_argument("--dd2-batch-skip", type=int, default=0)
    parser.add_argument("--source-candidate-id", default=None)
    parser.add_argument("--sample-token", default=None)
    parser.add_argument("--scene-token", default=None)
    parser.add_argument("--instance-token", default=None)
    parser.add_argument("--source-identity-summary", default=None)
    parser.add_argument("--baseline-dataset-dir", default="/data/projects/DriveLoop/data/processed/nuscenes/v1.0-mini/cam_all_val/v0.0.2")
    parser.add_argument("--baseline-output-dir", default="/data/projects/DriveLoop/outputs/drivedreamer2_img_cond_mini")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=None)
    args = parser.parse_args(argv)

    summary = ExperimentPipeline(
        output_dir=Path(args.output_dir),
        config=ExperimentPipelineConfig(
            max_iterations=args.max_iterations,
            target_score=args.target_score,
            backend_name=args.backend,
            dd2_project_root=args.project_root,
            dd2_config_name=args.config_name,
            dd2_baseline_output_dir=args.baseline_output_dir,
            dd2_baseline_dataset_dir=args.baseline_dataset_dir,
            dd2_audit_only=args.audit_only,
            dd2_batch_skip=args.dd2_batch_skip,
            dd2_source_candidate_id=args.source_candidate_id,
            dd2_sample_token=args.sample_token,
            dd2_scene_token=args.scene_token,
            dd2_instance_token=args.instance_token,
            dd2_source_identity_summary=args.source_identity_summary,
            dd2_timeout_seconds=args.timeout_seconds,
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
