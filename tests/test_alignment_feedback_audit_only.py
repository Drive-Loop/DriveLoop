import json
from pathlib import Path

from scripts.prepare_alignment_feedback_audit_only import load_failed_checks, prepare_summary


def test_load_failed_checks_reads_required_failures(tmp_path: Path):
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "measured",
                "checks": [
                    {"name": "object_presence.motorcycle", "required": True, "passed": True},
                    {"name": "spatial_relation.left_lane_change", "required": True, "passed": False},
                    {"name": "optional.weather", "required": False, "passed": False},
                ],
            }
        ),
        encoding="utf-8",
    )

    assert load_failed_checks(report_path) == ["spatial_relation.left_lane_change"]


def test_prepare_summary_carries_manual_review_feedback_to_dd2_trace(tmp_path: Path):
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "measured",
                "checks": [
                    {"name": "spatial_relation.left_lane_change", "required": True, "passed": False}
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = prepare_summary(
        prompt="daytime urban road with a motorcycle",
        alignment_report=report_path,
        scenario_id="unit_alignment_feedback_audit_only",
    )

    assert payload["failed_checks"] == ["spatial_relation.left_lane_change"]
    assert "visible lane change from the left" in payload["refined_prompt"]
    assert payload["audit_summary"]["alignment_feedback_trace_present"] is True
    assert payload["audit_summary"]["alignment_feedback"]["failed_checks"] == [
        "spatial_relation.left_lane_change"
    ]
    assert "lane_change" in payload["audit_summary"]["motion_controls"]
    assert payload["audit_summary"]["tensor_control_claim"] == "not_evaluated"
    assert payload["audit_summary"]["video_semantic_claim"] == "not_evaluated"
