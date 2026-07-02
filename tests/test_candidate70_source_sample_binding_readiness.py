import json
from pathlib import Path

from scripts.run_candidate70_source_sample_binding_readiness import build_gate


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_candidate70_source_sample_binding_blocks_without_runtime_selector(tmp_path):
    identity_summary = tmp_path / "summary.json"
    failed_alignment = tmp_path / "alignment.json"
    runner = tmp_path / "run_driveloop_drivedreamer2.py"
    backend = tmp_path / "drivedreamer2.py"

    write_json(
        identity_summary,
        {
            "candidate": "candidate70",
            "source": "current_converter_get_cam_label",
            "raw_root": "/data/projects/DriveLoop/data/raw/nuscenes",
            "output_label_path": "outputs/driveloop/candidate70_converter_identity_probe/cam_front_8/v0.0.1/labels/data.pkl",
            "target_raw_instance_token": "21cdc9f24c614a6197fd044379697197",
            "frame_count": 2,
            "all_frames_have_target": True,
            "all_frames_have_instance_tokens": True,
            "all_frames_have_sample_annotation_tokens": True,
            "claim": {
                "candidate70_converter_derived_identity_subset_created": True,
            },
            "frame_summaries": [
                {
                    "sample_token": "sample_a",
                    "cam_token": "cam_a",
                    "target_present": True,
                },
                {
                    "sample_token": "sample_b",
                    "cam_token": "cam_b",
                    "target_present": True,
                },
            ],
        },
    )
    write_json(
        failed_alignment,
        {
            "interpretation": {
                "video_semantic_claim": "measured_failed",
            },
        },
    )
    runner.write_text("parser.add_argument('--prompt')\n", encoding="utf-8")
    backend.write_text("baseline_video = self.baseline_output_dir / '000000.mp4'\n", encoding="utf-8")

    gate = build_gate(
        identity_summary_path=identity_summary,
        failed_alignment_path=failed_alignment,
        runner_path=runner,
        backend_path=backend,
    )

    assert gate["readiness_status"] == "blocked_no_verified_runtime_sample_selector"
    assert gate["gpu_smoke_allowed"] is False
    assert gate["does_not_run_gpu"] is True
    assert gate["does_not_generate_video"] is True
    assert gate["checks"]["sample_tokens_available"] is True
    assert gate["checks"]["runner_has_runtime_sample_selector"] is False
    assert gate["checks"]["backend_has_runtime_sample_selector"] is False
    assert gate["checks"]["failed_alignment_is_measured_failed"] is True
    assert "blocked_no_verified_runtime_sample_selector" in gate["blockers"]
    assert gate["candidate70_source_evidence"]["first_sample_token"] == "sample_a"
    assert gate["candidate70_source_evidence"]["last_sample_token"] == "sample_b"
    assert gate["claim_boundary"]["semantic_success_claim_allowed"] is False


def test_candidate70_source_sample_binding_ready_only_when_runtime_selector_exists(tmp_path):
    identity_summary = tmp_path / "summary.json"
    failed_alignment = tmp_path / "alignment.json"
    runner = tmp_path / "run_driveloop_drivedreamer2.py"
    backend = tmp_path / "drivedreamer2.py"

    write_json(
        identity_summary,
        {
            "candidate": "candidate70",
            "target_raw_instance_token": "target",
            "frame_count": 1,
            "all_frames_have_target": True,
            "all_frames_have_instance_tokens": True,
            "all_frames_have_sample_annotation_tokens": True,
            "claim": {
                "candidate70_converter_derived_identity_subset_created": True,
            },
            "frame_summaries": [
                {
                    "sample_token": "sample_a",
                    "cam_token": "cam_a",
                },
            ],
        },
    )
    write_json(
        failed_alignment,
        {
            "interpretation": {
                "video_semantic_claim": "measured_failed",
            },
        },
    )
    runner.write_text("parser.add_argument('--sample-token')\n", encoding="utf-8")
    backend.write_text("sample_token_selector = request.metadata.get('sample_token')\n", encoding="utf-8")

    gate = build_gate(
        identity_summary_path=identity_summary,
        failed_alignment_path=failed_alignment,
        runner_path=runner,
        backend_path=backend,
    )

    assert gate["readiness_status"] == "ready"
    assert gate["runtime_binding_assessment"]["runtime_sample_selector_verified"] is True
    assert gate["gpu_smoke_allowed"] is False
