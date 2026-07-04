from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.run_closed_loop_experiment_registry import build_registry, discover_registry_cases, render_markdown


def write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def alignment_eval(scenario_id: str, claim: str, score: float, passed: bool, checks: tuple[int, int]) -> dict:
    return {
        "generation": {
            "prompt": "night urban street with a motorcycle making a visible cut-in from the left",
            "metadata": {
                "scenario_id": scenario_id,
                "prompt_video_alignment": {
                    "status": "measured",
                    "source": "manual_review",
                    "reviewer": "tester",
                },
            },
        },
        "evaluation": {
            "score": score,
            "metrics": {
                "alignment_required_check_count": float(checks[1]),
                "alignment_passed_required_check_count": float(checks[0]),
            },
            "diagnosis": {
                "passed": passed,
                "reasons": [] if passed else ["alignment_check_failed:maneuver"],
            },
        },
        "interpretation": {
            "video_semantic_claim": claim,
        },
    }


def test_registry_promotes_measured_failed_to_passed_case_study(tmp_path):
    failed = write_json(
        tmp_path / "failed.json",
        alignment_eval("candidate70_failed", "measured_failed", 0.361111, False, (3, 9)),
    )
    retry = write_json(
        tmp_path / "retry.json",
        alignment_eval("candidate70_retry", "measured_passed", 0.916667, True, (9, 9)),
    )
    summary = write_json(
        tmp_path / "summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "candidate70_failed_to_passed",
            "closed_loop_status": "measured_failed_to_measured_passed",
            "attempts": {
                "pre_refinement": {
                    "video_semantic_claim": "measured_failed",
                    "score": 0.361111,
                    "passed_required_check_count": 3,
                    "required_check_count": 9,
                },
                "post_refinement_retry": {
                    "video_semantic_claim": "measured_passed",
                    "score": 0.916667,
                    "passed_required_check_count": 9,
                    "required_check_count": 9,
                },
            },
            "evidence_chain": [
                "external_alignment_review",
                "failure_taxonomy",
                "refinement_proposal",
                "post_retry_alignment_review",
            ],
            "claim_boundary": {
                "closed_loop_case_is_not_strict_open_loop_baseline_comparison": True,
            },
            "remaining_work": ["repeat_closed_loop_protocol_on_more_long_tail_cases"],
        },
    )

    registry = build_registry(
        {
            "cases": [
                {
                    "case_id": "candidate70",
                    "task_family": "motorcycle_cut_in",
                    "closed_loop_case_summary": str(summary),
                    "failed_alignment_eval": str(failed),
                    "retry_alignment_eval": str(retry),
                }
            ]
        },
        tmp_path,
    )

    row = registry["cases"][0]
    assert registry["schema_version"] == "driveloop_closed_loop_experiment_registry.v0"
    assert registry["case_study_evidence_count"] == 1
    assert registry["case_study_claim_allowed_count"] == 1
    assert registry["paper_claim_allowed_count"] == 0
    assert row["evidence_level"] == "case_study_evidence"
    assert row["case_study_claim_allowed"] is True
    assert row["paper_claim_allowed"] is False
    assert row["strict_baseline_comparison_supported"] is False
    assert row["automatic_multiround_supported"] is False
    assert row["pre_checks"] == "3/9"
    assert row["retry_checks"] == "9/9"
    assert "add_strict_open_loop_dd2_baseline_comparison" in row["remaining_work"]
    assert row["claim_boundary"]["case_study_claim_allowed_means_single_case_evidence_only"] is True
    assert row["claim_boundary"]["paper_claim_allowed_is_deprecated_use_case_study_claim_allowed"] is True


def test_registry_does_not_upgrade_candidate_artifact_to_paper_claim(tmp_path):
    manifest = write_json(
        tmp_path / "artifact_manifest.json",
        {
            "schema_version": "driveloop_candidate_artifact_manifest.v0",
            "scenario_id": "candidate_only",
            "prompt": "motorcycle lane change",
            "candidate_status": "candidate_video_only",
            "video_semantic_claim": "not_measured",
        },
    )

    registry = build_registry(
        {
            "cases": [
                {
                    "case_id": "candidate_only",
                    "task_family": "motorcycle_lane_change",
                    "artifact_manifest": str(manifest),
                }
            ]
        },
        tmp_path,
    )

    row = registry["cases"][0]
    assert row["evidence_level"] == "candidate_artifact_only"
    assert row["case_study_claim_allowed"] is False
    assert row["paper_claim_allowed"] is False
    assert row["pre_claim"] is None
    assert row["retry_claim"] is None
    assert registry["paper_claim_allowed_count"] == 0


def test_markdown_renders_registry_table(tmp_path):
    registry = build_registry(
        {
            "cases": [
                {
                    "case_id": "empty_case",
                    "task_family": "smoke",
                }
            ]
        },
        tmp_path,
    )
    markdown = render_markdown(registry)

    assert "# DriveLoop Closed-loop Experiment Registry" in markdown
    assert "raw_case_count" in markdown
    assert "deduplicated_case_count" in markdown
    assert "| empty_case | smoke |" in markdown
    assert "`registry_is_not_video_semantic_success`: `True`" in markdown


def test_cli_writes_json_and_markdown(tmp_path):
    summary = write_json(
        tmp_path / "summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "candidate70",
            "closed_loop_status": "measured_failed_to_measured_passed",
            "attempts": {
                "pre_refinement": {"video_semantic_claim": "measured_failed", "score": 0.3},
                "post_refinement_retry": {"video_semantic_claim": "measured_passed", "score": 0.9},
            },
            "evidence_chain": ["external_alignment_review", "post_retry_alignment_review"],
        },
    )
    manifest = write_json(
        tmp_path / "registry_manifest.json",
        {
            "cases": [
                {
                    "case_id": "candidate70",
                    "task_family": "motorcycle_cut_in",
                    "closed_loop_case_summary": str(summary),
                }
            ]
        },
    )
    output_json = tmp_path / "out" / "registry.json"
    output_md = tmp_path / "out" / "registry.md"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_closed_loop_experiment_registry.py",
            "--manifest",
            str(manifest),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert data["case_study_claim_allowed_count"] == 1
    assert data["paper_claim_allowed_count"] == 0
    assert output_md.exists()



def test_discover_registry_cases_from_scan_root(tmp_path):
    summary = write_json(
        tmp_path / "outputs" / "closed_loop_case_summary" / "candidate70_summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "candidate70_motorcycle_cut_in",
            "closed_loop_status": "measured_failed_to_measured_passed",
            "attempts": {
                "pre_refinement": {"video_semantic_claim": "measured_failed", "score": 0.3},
                "post_refinement_retry": {"video_semantic_claim": "measured_passed", "score": 0.9},
            },
            "evidence_chain": ["external_alignment_review", "post_retry_alignment_review"],
        },
    )
    write_json(
        tmp_path / "outputs" / "closed_loop_case_summary" / "ignore.json",
        {"schema_version": "not_a_closed_loop_summary"},
    )
    write_json(
        tmp_path / "outputs" / "closed_loop_case_summary" / "list_top_level.json",
        [{"schema_version": "driveloop_closed_loop_case_summary.v0"}],
    )

    rows = discover_registry_cases(tmp_path / "outputs")
    assert len(rows) == 1
    assert rows[0]["case_id"] == "candidate70_motorcycle_cut_in"
    assert rows[0]["task_family"] == "motorcycle_cut_in"
    assert rows[0]["closed_loop_case_summary"] == str(summary)

    registry = build_registry({"cases": rows}, tmp_path)
    assert registry["case_count"] == 1
    assert registry["case_study_claim_allowed_count"] == 1
    assert registry["paper_claim_allowed_count"] == 0


def test_cli_scan_root_writes_registry(tmp_path):
    write_json(
        tmp_path / "outputs" / "audit_only_closed_loop_runner" / "case_a" / "closed_loop_case_summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "case_a_motorcycle_cut_in",
            "closed_loop_status": "measured_failed_to_measured_passed",
            "attempts": {
                "pre_refinement": {"video_semantic_claim": "measured_failed", "score": 0.2},
                "post_refinement_retry": {"video_semantic_claim": "measured_passed", "score": 0.95},
            },
            "evidence_chain": ["external_alignment_review", "post_retry_alignment_review"],
        },
    )
    write_json(
        tmp_path / "outputs" / "audit_only_closed_loop_runner" / "case_a" / "runner_summary.json",
        {
            "schema_version": "driveloop_audit_only_closed_loop_runner.v0",
            "claim_boundary": {"semantic_success_claim_allowed": False},
        },
    )

    output_json = tmp_path / "registry.json"
    output_md = tmp_path / "registry.md"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_closed_loop_experiment_registry.py",
            "--scan-root",
            str(tmp_path / "outputs"),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert data["case_count"] == 1
    assert data["case_study_claim_allowed_count"] == 1
    assert data["paper_claim_allowed_count"] == 0
    assert data["cases"][0]["sources"]["runner_summary"]["exists"] is True
    assert output_md.exists()



def test_registry_deduplicates_candidate70_duplicate_summaries(tmp_path):
    first = write_json(
        tmp_path / "outputs" / "closed_loop_case_summary" / "candidate70_failed_to_passed_summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "candidate70_failed_to_passed",
            "closed_loop_status": "measured_failed_to_measured_passed",
            "attempts": {
                "pre_refinement": {"video_semantic_claim": "measured_failed", "score": 0.361111},
                "post_refinement_retry": {"video_semantic_claim": "measured_passed", "score": 0.916667},
            },
            "evidence_chain": ["external_alignment_review", "post_retry_alignment_review"],
        },
    )
    second_dir = tmp_path / "outputs" / "audit_only_closed_loop_runner" / "candidate70"
    second = write_json(
        second_dir / "closed_loop_case_summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "candidate70_audit_only_failed_to_passed_runner",
            "closed_loop_status": "measured_failed_to_measured_passed",
            "attempts": {
                "pre_refinement": {"video_semantic_claim": "measured_failed", "score": 0.361111},
                "post_refinement_retry": {"video_semantic_claim": "measured_passed", "score": 0.916667},
            },
            "evidence_chain": ["external_alignment_review", "post_retry_alignment_review"],
        },
    )
    write_json(
        second_dir / "runner_summary.json",
        {
            "schema_version": "driveloop_audit_only_closed_loop_runner.v0",
            "claim_boundary": {"semantic_success_claim_allowed": False},
        },
    )

    rows = discover_registry_cases(tmp_path / "outputs")
    assert len(rows) == 2

    registry = build_registry({"cases": rows}, tmp_path)
    assert registry["raw_case_count"] == 2
    assert registry["case_count"] == 1
    assert registry["deduplicated_case_count"] == 1
    row = registry["cases"][0]
    assert row["case_id"] == "candidate70_audit_only_failed_to_passed_runner"
    assert row["sources"]["runner_summary"]["exists"] is True
    assert row["duplicate_sources"][0]["path"] == str(first)
    assert row["claim_boundary"]["duplicate_sources_are_not_counted_as_separate_cases"] is True
    assert registry["claim_boundary"]["duplicate_closed_loop_summaries_are_collapsed"] is True



def test_discovery_auto_links_alignment_evals_by_claim_score_and_checks(tmp_path):
    outputs = tmp_path / "outputs"
    failed_eval = write_json(
        outputs / "prompt_video_alignment_eval" / "failed" / "prompt_video_alignment_evaluation.json",
        alignment_eval("failed_scenario", "measured_failed", 0.361111, False, (3, 9)),
    )
    retry_eval = write_json(
        outputs / "prompt_video_alignment_eval" / "retry" / "prompt_video_alignment_evaluation.json",
        alignment_eval("retry_scenario", "measured_passed", 0.916667, True, (9, 9)),
    )
    write_json(
        outputs / "closed_loop_case_summary" / "candidate70_summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "candidate70_motorcycle_cut_in",
            "closed_loop_status": "measured_failed_to_measured_passed",
            "attempts": {
                "pre_refinement": {
                    "video_semantic_claim": "measured_failed",
                    "score": 0.361111,
                    "passed_required_check_count": 3,
                    "required_check_count": 9,
                },
                "post_refinement_retry": {
                    "video_semantic_claim": "measured_passed",
                    "score": 0.916667,
                    "passed_required_check_count": 9,
                    "required_check_count": 9,
                },
            },
            "evidence_chain": ["external_alignment_review", "post_retry_alignment_review"],
        },
    )

    rows = discover_registry_cases(outputs)
    assert rows[0]["failed_alignment_eval"] == str(failed_eval)
    assert rows[0]["retry_alignment_eval"] == str(retry_eval)

    registry = build_registry({"cases": rows}, tmp_path)
    row = registry["cases"][0]
    assert row["scenario_id"] == "retry_scenario"
    assert row["prompt"] == "night urban street with a motorcycle making a visible cut-in from the left"
    assert row["sources"]["failed_alignment_eval"]["exists"] is True
    assert row["sources"]["retry_alignment_eval"]["exists"] is True
    assert row["claim_boundary"]["auto_matched_alignment_eval_is_metadata_link_not_new_review"] is True


def test_discovery_keeps_ambiguous_alignment_matches_as_candidates(tmp_path):
    outputs = tmp_path / "outputs"
    write_json(
        outputs / "prompt_video_alignment_eval" / "a" / "prompt_video_alignment_evaluation.json",
        alignment_eval("failed_a", "measured_failed", 0.361111, False, (3, 9)),
    )
    write_json(
        outputs / "prompt_video_alignment_eval" / "b" / "prompt_video_alignment_evaluation.json",
        alignment_eval("failed_b", "measured_failed", 0.361111, False, (3, 9)),
    )
    write_json(
        outputs / "closed_loop_case_summary" / "candidate70_summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "candidate70_motorcycle_cut_in",
            "closed_loop_status": "incomplete_or_not_measured",
            "attempts": {
                "pre_refinement": {
                    "video_semantic_claim": "measured_failed",
                    "score": 0.361111,
                    "passed_required_check_count": 3,
                    "required_check_count": 9,
                },
            },
            "evidence_chain": ["external_alignment_review"],
        },
    )

    rows = discover_registry_cases(outputs)
    assert "failed_alignment_eval" not in rows[0]
    assert len(rows[0]["failed_alignment_eval_candidates"]) == 2



def test_registry_records_longtail_control_coverage_artifact(tmp_path):
    summary = write_json(
        tmp_path / "summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "case_with_longtail_coverage",
            "closed_loop_status": "measured_passed",
        },
    )
    coverage = write_json(
        tmp_path / "longtail_control_coverage.json",
        {
            "schema_version": "driveloop_longtail_control_coverage.v0",
            "score": 0.5,
            "tag_count": 1,
            "covered_tag_count": 0,
            "tags": [
                {
                    "tag": "motorcycle_cut_in",
                    "covered": False,
                    "missing_channels": ["evaluation"],
                }
            ],
            "claim_boundary": {
                "longtail_control_coverage_is_not_video_semantic_success": True,
            },
        },
    )

    registry = build_registry(
        {
            "cases": [
                {
                    "case_id": "case_with_longtail_coverage",
                    "closed_loop_case_summary": str(summary),
                    "longtail_control_coverage": str(coverage),
                }
            ]
        }
    )

    row = registry["cases"][0]
    longtail = row["longtail_control_coverage"]
    assert longtail["available"] is True
    assert longtail["source"] == "artifact"
    assert longtail["score"] == 0.5
    assert longtail["missing_channels"] == {"motorcycle_cut_in": ["evaluation"]}
    assert row["sources"]["longtail_control_coverage"]["exists"] is True
    assert registry["longtail_control_coverage_available_count"] == 1
    assert registry["longtail_control_coverage_mean_score"] == 0.5
    assert row["claim_boundary"]["longtail_control_coverage_is_not_video_semantic_success"] is True


def test_registry_computes_longtail_control_coverage_from_manifest_scene_and_plan(tmp_path):
    summary = write_json(
        tmp_path / "summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "computed_longtail_coverage",
            "closed_loop_status": "measured_failed",
        },
    )

    registry = build_registry(
        {
            "cases": [
                {
                    "case_id": "computed_longtail_coverage",
                    "closed_loop_case_summary": str(summary),
                    "scene_specification": {
                        "prompt": "a motorcycle cuts in from the left",
                    },
                    "condition_plan": {
                        "tags": ["motorcycle_cut_in"],
                        "prompt_suffixes": ["motorcycle cut in maneuver"],
                    },
                }
            ]
        }
    )

    row = registry["cases"][0]
    longtail = row["longtail_control_coverage"]
    assert longtail["available"] is True
    assert longtail["source"] == "manifest_computed"
    assert longtail["score"] == 0.0
    assert longtail["missing_channels"] == {
        "motorcycle_cut_in": ["source_or_structural", "evaluation"]
    }



def test_registry_records_perception_metric_manifest_from_eval_report(tmp_path):
    summary = write_json(
        tmp_path / "summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "case_with_perception_eval",
            "closed_loop_status": "measured_passed",
        },
    )
    perception_eval = write_json(
        tmp_path / "perception_video_evaluation.json",
        {
            "schema_version": "driveloop_perception_video_eval.v0",
            "evaluation": {
                "score": 0.91,
                "metrics": {
                    "perception_measured": 1.0,
                    "Q_cov": 1.0,
                    "Q_conf": 0.91,
                    "Q_track": 1.0,
                    "Q_id": 1.0,
                    "Q_box": 0.83,
                },
                "diagnosis": {"passed": True, "reasons": []},
            },
            "interpretation": {
                "perception_claim": "measured_passed",
                "semantic_success_claim": "not_proven_by_perception_metrics_alone",
            },
        },
    )

    registry = build_registry(
        {
            "cases": [
                {
                    "case_id": "case_with_perception_eval",
                    "closed_loop_case_summary": str(summary),
                    "perception_eval": str(perception_eval),
                }
            ]
        }
    )

    row = registry["cases"][0]
    manifest = row["perception_metric_manifest"]
    assert manifest["available"] is True
    assert manifest["source"] == "perception_eval"
    assert manifest["perception_claim"] == "measured_passed"
    assert manifest["metrics"]["Q_cov"] == 1.0
    assert manifest["metrics_complete"] is True
    assert manifest["measured"] is True
    assert manifest["passed"] is True
    assert row["perception_passed"] is True
    assert row["sources"]["perception_metric_manifest"]["exists"] is False
    assert registry["perception_metric_manifest_available_count"] == 1
    assert registry["perception_metric_manifest_measured_count"] == 1
    assert registry["perception_metric_manifest_complete_count"] == 1
    assert registry["perception_metric_manifest_mean_score"] == 0.91
    assert row["claim_boundary"]["perception_metric_manifest_is_not_video_semantic_success"] is True


def test_registry_records_perception_metric_manifest_artifact(tmp_path):
    summary = write_json(
        tmp_path / "summary.json",
        {
            "schema_version": "driveloop_closed_loop_case_summary.v0",
            "case_id": "case_with_perception_manifest",
            "closed_loop_status": "measured_failed",
        },
    )
    perception_manifest = write_json(
        tmp_path / "perception_metric_manifest.json",
        {
            "schema_version": "driveloop_perception_metric_manifest.v0",
            "available": True,
            "source": "artifact",
            "evaluator": "PerceptionVideoEvaluator",
            "perception_claim": "measured_failed",
            "semantic_success_claim": "not_proven_by_perception_metrics_alone",
            "score": 0.42,
            "measured": True,
            "passed": False,
            "metrics_complete": True,
            "metrics": {
                "Q_cov": 0.25,
                "Q_conf": 0.8,
                "Q_track": 0.25,
                "Q_id": 1.0,
                "Q_box": 1.0,
            },
            "missing_metrics": [],
            "metric_source_keys": {},
            "source_metric_prefixes": [],
            "claim_boundary": {
                "perception_metric_manifest_is_not_video_semantic_success": True,
            },
        },
    )

    registry = build_registry(
        {
            "cases": [
                {
                    "case_id": "case_with_perception_manifest",
                    "closed_loop_case_summary": str(summary),
                    "perception_metric_manifest": str(perception_manifest),
                }
            ]
        }
    )

    row = registry["cases"][0]
    manifest = row["perception_metric_manifest"]
    assert manifest["available"] is True
    assert manifest["source"] == "artifact"
    assert manifest["perception_claim"] == "measured_failed"
    assert manifest["score"] == 0.42
    assert manifest["metrics"]["Q_cov"] == 0.25
    assert row["sources"]["perception_metric_manifest"]["exists"] is True



def test_registry_reads_automatic_closed_loop_manifest(tmp_path):
    automatic = write_json(
        tmp_path / "automatic_closed_loop_manifest.json",
        {
            "schema_version": "driveloop_automatic_closed_loop_manifest.v0",
            "source": "DriveLoopRunner+MockGenerationBackend",
            "automatic_loop_supported": True,
            "automatic_multiround_supported": True,
            "attempt_count": 2,
            "complete_transition_count": 1,
            "blockers": [],
            "audit_only_detected": False,
            "manual_review_dependency_detected": False,
            "claim_boundary": {
                "manifest_is_not_video_semantic_success": True,
            },
        },
    )

    registry = build_registry(
        {
            "cases": [
                {
                    "case_id": "mock_automatic_loop",
                    "task_family": "mock_closed_loop",
                    "automatic_closed_loop_manifest": str(automatic),
                }
            ]
        },
        tmp_path,
    )

    row = registry["cases"][0]
    assert row["automatic_multiround_supported"] is True
    assert row["automatic_closed_loop_manifest"]["available"] is True
    assert row["automatic_closed_loop_manifest"]["attempt_count"] == 2
    assert row["automatic_closed_loop_manifest"]["complete_transition_count"] == 1
    assert row["sources"]["automatic_closed_loop_manifest"]["exists"] is True
    assert registry["automatic_multiround_supported_count"] == 1
    assert registry["automatic_closed_loop_manifest_available_count"] == 1
    assert registry["claim_boundary"]["registry_automatic_closed_loop_manifest_is_not_video_semantic_success"] is True
    assert "automate_generate_evaluate_diagnose_refine_regenerate_loop" not in row["remaining_work"]
