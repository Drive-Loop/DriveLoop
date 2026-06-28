from argparse import Namespace
from pathlib import Path

from scripts.run_alignment_feedback_loop_demo import run_demo


def test_alignment_feedback_loop_demo_records_feedback_trace(tmp_path: Path):
    payload = run_demo(
        Namespace(
            prompt="daytime urban road",
            scenario_id="unit_alignment_feedback_loop",
            output_dir=str(tmp_path),
            target_score=0.8,
        )
    )

    assert payload["closed_loop_control_flow"] == "demonstrated_with_mock_backend"
    assert payload["tensor_control_claim"] == "not_evaluated"
    assert payload["video_semantic_claim"] == "not_evaluated"
    assert payload["iterations"] == 2
    assert payload["alignment_feedback_trace_present"] is True

    trace = payload["alignment_feedback_trace"]
    assert trace["status"] == "measured_failed"
    assert trace["control_level"] == "text_feedback_only"
    assert trace["failed_checks"] == [
        "object_presence.motorcycle",
        "spatial_relation.left_lane_change",
    ]

    assert "a motorcycle must be visibly present" in payload["final_prompt"]
    assert "the motorcycle performs a visible lane change from the left" in payload["final_prompt"]
    assert "does not run DD2 diffusion" in payload["claim_boundary"]


def test_alignment_feedback_loop_demo_writes_summary(tmp_path: Path):
    payload = run_demo(
        Namespace(
            prompt="daytime urban road",
            scenario_id="unit_write_summary",
            output_dir=str(tmp_path),
            target_score=0.8,
        )
    )

    summary_path = (
        tmp_path
        / "unit_write_summary"
        / "alignment_feedback_loop_demo_summary.json"
    )

    assert summary_path.exists()
    assert payload["scenario_id"] == "unit_write_summary"
