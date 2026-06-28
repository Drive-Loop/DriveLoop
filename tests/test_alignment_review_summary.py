import json
from pathlib import Path

from scripts.run_alignment_review_summary import build_summary, summarize_file


def test_summarize_manual_alignment_report_marks_failed_required_checks(tmp_path: Path):
    report = tmp_path / "manual_alignment_report_review_v0.json"
    report.write_text(
        json.dumps(
            {
                "status": "measured",
                "source": "manual_review_v0",
                "review_scope": {
                    "prompt": "daytime urban road with a motorcycle changing lane from the left",
                    "video": "iteration_00.mp4",
                    "contact_sheet": "contact_sheet.jpg",
                },
                "checks": [
                    {"name": "object_presence.motorcycle", "required": True, "passed": True, "score": 0.6},
                    {"name": "spatial_relation.left_lane_change", "required": True, "passed": False, "score": 0.0},
                ],
            }
        ),
        encoding="utf-8",
    )

    row = summarize_file(report)

    assert row["kind"] == "manual_alignment_report"
    assert row["video_semantic_claim"] == "measured_failed"
    assert row["required_check_count"] == 2
    assert row["passed_required_check_count"] == 1
    assert row["failed_required_checks"] == ["spatial_relation.left_lane_change"]


def test_summary_preserves_evaluator_semantic_claim(tmp_path: Path):
    evaluation = tmp_path / "prompt_video_alignment_evaluation.json"
    evaluation.write_text(
        json.dumps(
            {
                "generation": {
                    "prompt": "daytime urban road",
                    "artifacts": {"video": "iteration_00.mp4"},
                    "metadata": {
                        "scenario_id": "unit_eval",
                        "prompt_video_alignment": {
                            "status": "measured",
                            "source": "manual_review_v0",
                            "checks": [
                                {"name": "lighting.daytime", "required": True, "passed": True, "score": 1.0}
                            ],
                        },
                    },
                },
                "evaluation": {"score": 1.0},
                "interpretation": {"video_semantic_claim": "measured_passed"},
            }
        ),
        encoding="utf-8",
    )

    summary = build_summary([tmp_path])

    assert summary["row_count"] == 1
    assert summary["claim_counts"] == {"measured_passed": 1}
    assert summary["rows"][0]["scenario_id"] == "unit_eval"
    assert summary["rows"][0]["video_semantic_claim"] == "measured_passed"


def test_summary_ignores_non_review_alignment_metadata(tmp_path: Path):
    unrelated = tmp_path / "motorcycle_fix_gpu_smoke_summary.json"
    unrelated.write_text(
        json.dumps(
            {
                "status": "completed",
                "metadata": {
                    "dd2_paper_alignment_report": {
                        "stage_3_scene_consistent_generation": {"tensor_control_ready": True}
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    summary = build_summary([tmp_path])

    assert summary["row_count"] == 0
    assert summary["claim_counts"] == {}


def test_summary_normalizes_legacy_measured_by_external_report_claim(tmp_path: Path):
    evaluation = tmp_path / "prompt_video_alignment_evaluation.json"
    evaluation.write_text(
        json.dumps(
            {
                "generation": {
                    "prompt": "daytime urban road",
                    "artifacts": {"video": "iteration_00.mp4"},
                    "metadata": {
                        "scenario_id": "legacy_eval",
                        "prompt_video_alignment": {
                            "status": "measured",
                            "source": "manual_review_draft_v0",
                            "checks": [
                                {"name": "object_presence.motorcycle", "required": True, "passed": False, "score": 0.0}
                            ],
                        },
                    },
                },
                "evaluation": {"score": 0.0},
                "interpretation": {"video_semantic_claim": "measured_by_external_report"},
            }
        ),
        encoding="utf-8",
    )

    summary = build_summary([tmp_path])

    assert summary["row_count"] == 1
    assert summary["claim_counts"] == {"measured_failed": 1}
    assert summary["rows"][0]["video_semantic_claim"] == "measured_failed"
