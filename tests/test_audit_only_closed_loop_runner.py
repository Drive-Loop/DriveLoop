from __future__ import annotations

from pathlib import Path

from scripts import run_audit_only_closed_loop_runner as runner


def parse_minimal(tmp_path: Path):
    failed = tmp_path / "failed.json"
    failed.write_text("{}", encoding="utf-8")
    return runner.parse_args(
        [
            "--case-id",
            "case_a",
            "--initial-alignment-eval",
            str(failed),
            "--output-root",
            str(tmp_path / "out"),
        ]
    )


def test_build_commands_uses_checked_cli_flags(tmp_path: Path) -> None:
    args = parse_minimal(tmp_path)
    paths = runner.artifact_paths(args.output_root)

    commands = runner.build_commands(args, paths)
    joined = "\n".join(" ".join(command["argv"]) for command in commands)

    assert "--initial-alignment-eval" in joined
    assert "--orchestrator-trace" in joined
    assert "--regeneration-command-plan" in joined
    assert "--summary-output-json" in joined
    assert "scripts/run_audit_only_closed_loop_orchestrator.py" in joined
    assert "scripts/run_audit_only_regeneration_command_planner.py" in joined
    assert "scripts/run_post_regeneration_review_planner.py" in joined


def test_retry_alignment_eval_adds_case_summary_step(tmp_path: Path) -> None:
    failed = tmp_path / "failed.json"
    retry = tmp_path / "retry.json"
    failed.write_text("{}", encoding="utf-8")
    retry.write_text("{}", encoding="utf-8")

    args = runner.parse_args(
        [
            "--case-id",
            "case_b",
            "--initial-alignment-eval",
            str(failed),
            "--retry-alignment-eval",
            str(retry),
            "--output-root",
            str(tmp_path / "out"),
        ]
    )

    commands = runner.build_commands(args, runner.artifact_paths(args.output_root))
    assert commands[-1]["step"] == "closed_loop_case_summary"
    assert "scripts/run_closed_loop_case_summary.py" in commands[-1]["argv"]


def test_without_retry_does_not_add_case_summary_step(tmp_path: Path) -> None:
    args = parse_minimal(tmp_path)
    commands = runner.build_commands(args, runner.artifact_paths(args.output_root))
    assert [command["step"] for command in commands] == [
        "closed_loop_orchestrator",
        "regeneration_command_planner",
        "post_regeneration_review_planner",
    ]


def test_summary_preserves_claim_boundary(tmp_path: Path) -> None:
    args = parse_minimal(tmp_path)
    paths = runner.artifact_paths(args.output_root)
    commands = runner.build_commands(args, paths)
    results = [{"step": command["step"], "returncode": 0, "writes": command["writes"]} for command in commands]

    summary = runner.build_summary(args, paths, commands, results)

    assert summary["runner_execution"]["ran_gpu"] is False
    assert summary["runner_execution"]["called_dd2_runtime"] is False
    assert summary["runner_execution"]["generated_video"] is False
    assert summary["claim_boundary"]["semantic_success_claim_allowed"] is False
    assert summary["runner_status"] == "audit_only_completed_pending_regeneration"


def test_summary_status_with_retry_evidence(tmp_path: Path) -> None:
    failed = tmp_path / "failed.json"
    retry = tmp_path / "retry.json"
    failed.write_text("{}", encoding="utf-8")
    retry.write_text("{}", encoding="utf-8")

    args = runner.parse_args(
        [
            "--case-id",
            "case_c",
            "--initial-alignment-eval",
            str(failed),
            "--retry-alignment-eval",
            str(retry),
            "--output-root",
            str(tmp_path / "out"),
        ]
    )
    paths = runner.artifact_paths(args.output_root)
    commands = runner.build_commands(args, paths)
    results = [{"step": command["step"], "returncode": 0, "writes": command["writes"]} for command in commands]

    summary = runner.build_summary(args, paths, commands, results)

    assert summary["runner_status"] == "audit_only_completed_with_retry_evidence"


def test_write_outputs(tmp_path: Path) -> None:
    args = parse_minimal(tmp_path)
    paths = runner.artifact_paths(args.output_root)
    commands = runner.build_commands(args, paths)
    results = [{"step": command["step"], "returncode": 0, "writes": command["writes"]} for command in commands]
    summary = runner.build_summary(args, paths, commands, results)

    runner.write_json(paths["runner_summary_json"], summary)
    runner.write_markdown(paths["runner_summary_md"], summary)

    assert paths["runner_summary_json"].exists()
    assert paths["runner_summary_md"].exists()
    assert "audit_only_closed_loop_runner" in paths["runner_summary_json"].read_text(encoding="utf-8")


def test_optional_source_binding_and_identity_are_forwarded(tmp_path: Path) -> None:
    args = parse_minimal(tmp_path)
    args.source_binding_readiness = tmp_path / "binding.json"
    args.source_identity_summary = tmp_path / "identity.json"
    args.baseline_dataset_dir = tmp_path / "dataset"
    args.baseline_output_dir = tmp_path / "baseline"
    args.source_candidate_id = "candidate70"
    args.instance_token = "instance-token"

    commands = runner.build_commands(args, runner.artifact_paths(args.output_root))
    regen = next(command for command in commands if command["step"] == "regeneration_command_planner")
    joined = " ".join(regen["argv"])

    assert "--source-binding-readiness" in joined
    assert "--source-identity-summary" in joined
    assert "--baseline-dataset-dir" in joined
    assert "--baseline-output-dir" in joined
    assert "--source-candidate-id candidate70" in joined
    assert "--instance-token instance-token" in joined
