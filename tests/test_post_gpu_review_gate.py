from pathlib import Path

from scripts.run_post_gpu_review_gate import build_not_measured_payload


def test_post_gpu_review_gate_marks_candidate_video_not_measured(tmp_path: Path):
    video_path = tmp_path / "iteration_00.mp4"
    video_path.write_bytes(b"fake video bytes")

    payload = build_not_measured_payload(
        prompt="daytime urban road with a motorcycle",
        scenario_id="unit_post_gpu_gate",
        video_path=video_path,
        review_pack_manifest={
            "contact_sheet": "contact_sheet.jpg",
            "report_template": "manual_alignment_report_template.json",
        },
    )

    assert payload["schema_version"] == "driveloop_post_gpu_review_gate.v0"
    assert payload["candidate_video_available"] is True
    assert payload["video_semantic_claim"] == "not_measured"
    assert payload["review_status"] == "requires_manual_or_perception_review"
    assert payload["alignment_evaluation"]["interpretation"]["video_semantic_claim"] == "not_measured"
    assert "run scripts/run_prompt_video_alignment_eval.py" in payload["next_required_steps"][2]
    assert "does not permit prompt-video semantic success claims" in payload["claim_boundary"]
