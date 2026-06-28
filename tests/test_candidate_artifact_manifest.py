from pathlib import Path

from scripts.run_candidate_artifact_manifest import build_manifest


def test_manifest_records_missing_candidate_as_not_measured(tmp_path):
    video = tmp_path / "missing.mp4"

    manifest = build_manifest(
        prompt="prompt",
        scenario_id="case",
        video_path=video,
        readiness_gate=tmp_path / "gate.json",
        command_plan=tmp_path / "plan.json",
        runbook=tmp_path / "runbook.md",
        post_gpu_gate=tmp_path / "post.json",
        manual_report=tmp_path / "manual.json",
        alignment_eval=tmp_path / "eval.json",
    )

    assert manifest["candidate_status"] == "candidate_not_generated"
    assert manifest["video_semantic_claim"] == "not_measured"
    assert manifest["semantic_claim_ready"] is False
    assert manifest["claim_boundary"]["video_exists_is_not_semantic_success"] is True
    assert "video" in manifest["missing_required_claim_artifacts"]


def test_manifest_records_candidate_video_without_semantic_claim(tmp_path):
    video = tmp_path / "iteration_00.mp4"
    video.write_bytes(b"candidate")

    manifest = build_manifest(
        prompt="prompt",
        scenario_id="case",
        video_path=video,
        readiness_gate=tmp_path / "gate.json",
        command_plan=tmp_path / "plan.json",
        runbook=tmp_path / "runbook.md",
        post_gpu_gate=tmp_path / "post.json",
        manual_report=tmp_path / "manual.json",
        alignment_eval=tmp_path / "eval.json",
    )

    assert manifest["candidate_status"] == "candidate_video_only"
    assert manifest["video_semantic_claim"] == "not_measured"
    assert manifest["claim_boundary"]["allowed_without_review"] == "candidate_video_generated_only"
    assert manifest["semantic_claim_ready"] is False
    assert "video" not in manifest["missing_required_claim_artifacts"]


def test_manifest_becomes_claim_ready_only_when_required_artifacts_exist(tmp_path):
    paths = {
        name: tmp_path / f"{name}.json"
        for name in ["post", "manual", "eval", "runtime"]
    }
    video = tmp_path / "iteration_00.mp4"
    video.write_bytes(b"candidate")
    for path in paths.values():
        path.write_text("{}", encoding="utf-8")

    manifest = build_manifest(
        prompt="prompt",
        scenario_id="case",
        video_path=video,
        readiness_gate=tmp_path / "gate.json",
        command_plan=tmp_path / "plan.json",
        runbook=tmp_path / "runbook.md",
        post_gpu_gate=paths["post"],
        manual_report=paths["manual"],
        alignment_eval=paths["eval"],
        runtime_audit=paths["runtime"],
    )

    assert manifest["semantic_claim_ready"] is True
    assert manifest["missing_required_claim_artifacts"] == []
    assert manifest["artifacts"]["runtime_audit"]["required_for_semantic_claim"] is True
