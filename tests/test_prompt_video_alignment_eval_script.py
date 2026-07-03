from __future__ import annotations

from argparse import Namespace
import json
from pathlib import Path

import pytest

from scripts.run_prompt_video_alignment_eval import build_generation, evaluate_generation, load_alignment_report


def test_script_evaluation_reports_not_measured_without_external_report(tmp_path: Path):
    video_path = tmp_path / "iteration_00.mp4"
    video_path.write_bytes(b"fake video bytes")

    generation = build_generation(
        Namespace(
            prompt="daytime urban road with a motorcycle changing lane from the left",
            scenario_id="unit_no_report",
            video_path=str(video_path),
            alignment_report=None,
        )
    )

    payload = evaluate_generation(generation, pass_threshold=0.8)

    assert payload["evaluation"]["score"] == 0.0
    assert payload["evaluation"]["diagnosis"]["passed"] is False
    assert "video_alignment_not_measured" in payload["evaluation"]["diagnosis"]["reasons"]
    assert payload["interpretation"]["video_semantic_claim"] == "not_measured"


def test_script_evaluation_scores_external_alignment_report(tmp_path: Path):
    video_path = tmp_path / "iteration_00.mp4"
    video_path.write_bytes(b"fake video bytes")
    report_path = tmp_path / "alignment_report.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "measured",
                "source": "manual_review_v0",
                "checks": [
                    {"name": "object_presence.motorcycle", "required": True, "passed": True, "score": 0.9},
                    {"name": "spatial_relation.left_lane_change", "required": True, "passed": True, "score": 0.8},
                ],
            }
        ),
        encoding="utf-8",
    )

    generation = build_generation(
        Namespace(
            prompt="daytime urban road with a motorcycle changing lane from the left",
            scenario_id="unit_measured",
            video_path=str(video_path),
            alignment_report=str(report_path),
        )
    )

    payload = evaluate_generation(generation, pass_threshold=0.8)

    assert payload["evaluation"]["score"] == 0.85
    assert payload["evaluation"]["diagnosis"]["passed"] is True
    assert payload["interpretation"]["video_semantic_claim"] == "measured_passed"


def test_script_accepts_wrapped_alignment_report(tmp_path: Path):
    report_path = tmp_path / "wrapped_report.json"
    report_path.write_text(
        json.dumps(
            {
                "prompt_video_alignment": {
                    "status": "measured",
                    "checks": [
                        {"name": "object_presence.car", "required": True, "passed": True, "score": 0.8}
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    report = load_alignment_report(str(report_path))

    assert report["status"] == "measured"
    assert report["checks"][0]["name"] == "object_presence.car"


def test_script_rejects_missing_video_artifact(tmp_path: Path):
    missing_video = tmp_path / "missing.mp4"

    with pytest.raises(FileNotFoundError):
        build_generation(
            Namespace(
                prompt="daytime urban road",
                scenario_id="unit_missing_video",
                video_path=str(missing_video),
                alignment_report=None,
            )
        )

def test_script_evaluation_marks_failed_external_alignment_report(tmp_path: Path):
    video_path = tmp_path / "iteration_00.mp4"
    video_path.write_bytes(b"fake video bytes")
    report_path = tmp_path / "alignment_report_failed.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "measured",
                "source": "manual_review_v0",
                "checks": [
                    {"name": "object_presence.motorcycle", "required": True, "passed": False, "score": 0.0},
                    {"name": "lighting.daytime", "required": True, "passed": True, "score": 0.9},
                ],
            }
        ),
        encoding="utf-8",
    )

    generation = build_generation(
        Namespace(
            prompt="daytime urban road with a motorcycle changing lane from the left",
            scenario_id="unit_measured_failed",
            video_path=str(video_path),
            alignment_report=str(report_path),
        )
    )

    payload = evaluate_generation(generation, pass_threshold=0.8)

    assert payload["evaluation"]["diagnosis"]["passed"] is False
    assert payload["interpretation"]["video_semantic_claim"] == "measured_failed"


def test_script_evaluation_rejects_not_measured_report_template(tmp_path: Path):
    video_path = tmp_path / "iteration_00.mp4"
    video_path.write_bytes(b"fake video bytes")
    report_path = tmp_path / "alignment_report_template.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "not_measured",
                "source": "manual_review_frame_pack_v0",
                "checks": [
                    {
                        "name": "object_presence.motorcycle",
                        "required": True,
                        "passed": False,
                        "score": 0.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    generation = build_generation(
        Namespace(
            prompt="daytime urban road with a motorcycle changing lane from the left",
            scenario_id="unit_not_measured_template",
            video_path=str(video_path),
            alignment_report=str(report_path),
        )
    )

    payload = evaluate_generation(generation, pass_threshold=0.8)

    assert payload["evaluation"]["diagnosis"]["passed"] is False
    assert payload["interpretation"]["video_semantic_claim"] == "not_measured"
