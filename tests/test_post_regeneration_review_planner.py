from pathlib import Path

from scripts.run_post_regeneration_review_planner import build_post_regeneration_review_plan, render_markdown


def regeneration_plan(tmp_path: Path, prompt: str = "night urban road", scenario_id: str = "case_retry"):
    return {
        "command_status": "draft_ready_for_explicit_approval",
        "resolved_inputs": {
            "prompt": prompt,
            "scenario_id": scenario_id,
            "output_dir": str(tmp_path / "generation"),
        },
        "generated_command": {
            "requires_explicit_user_approval": True,
        },
    }


def test_plan_builds_post_review_commands_from_regeneration_plan(tmp_path: Path):
    plan = build_post_regeneration_review_plan(
        regeneration_plan(tmp_path),
        failed_alignment_eval="failed_eval.json",
        failure_taxonomy="taxonomy.json",
        failed_perception_eval="perception.json",
        refinement_proposal="proposal.json",
    )

    assert plan["plan_status"] == "draft_ready_for_post_regeneration_review"
    assert plan["planner_execution"]["does_not_run_gpu"] is True
    assert plan["claim_boundary"]["review_plan_is_not_video_semantic_success"] is True
    assert "scripts/run_post_gpu_review_gate.py" in plan["commands"]["post_gpu_review_gate"]["argv"]
    assert "scripts/run_prompt_video_alignment_eval.py" in plan["commands"]["prompt_video_alignment_eval_after_completed_review"]["argv"]
    assert "scripts/run_closed_loop_case_summary.py" in plan["commands"]["closed_loop_summary_refresh_after_alignment_eval"]["argv"]
    assert plan["commands"]["post_gpu_review_gate"]["can_run_now"] is False


def test_plan_marks_post_gate_runnable_when_video_exists(tmp_path: Path):
    base = tmp_path / "generation"
    video = base / "artifacts" / "case_retry" / "iteration_00.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"fake video")

    plan = build_post_regeneration_review_plan(regeneration_plan(tmp_path))

    assert plan["artifact_status"]["video_exists"] is True
    assert plan["commands"]["post_gpu_review_gate"]["can_run_now"] is True
    assert plan["commands"]["prompt_video_alignment_eval_after_completed_review"]["can_run_now"] is False
    assert plan["commands"]["prompt_video_alignment_eval_after_completed_review"]["blocked_until"] == "generated_video_and_completed_manual_report_exist"


def test_plan_marks_alignment_eval_runnable_after_completed_manual_report(tmp_path: Path):
    base = tmp_path / "generation"
    video = base / "artifacts" / "case_retry" / "iteration_00.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"fake video")

    manual = Path("outputs/driveloop/post_gpu_review_gate/case_retry/manual_review_pack/manual_alignment_report.json")
    old = manual.read_text(encoding="utf-8") if manual.exists() else None
    manual.parent.mkdir(parents=True, exist_ok=True)
    manual.write_text("{}", encoding="utf-8")
    try:
        plan = build_post_regeneration_review_plan(regeneration_plan(tmp_path))
        assert plan["artifact_status"]["manual_report_exists"] is True
        assert plan["commands"]["prompt_video_alignment_eval_after_completed_review"]["can_run_now"] is True
    finally:
        if old is None:
            manual.unlink(missing_ok=True)
        else:
            manual.write_text(old, encoding="utf-8")


def test_plan_reports_missing_required_fields(tmp_path: Path):
    bad_plan = regeneration_plan(tmp_path, prompt="", scenario_id="")
    bad_plan["resolved_inputs"]["output_dir"] = ""

    plan = build_post_regeneration_review_plan(bad_plan)

    assert plan["plan_status"] == "draft_incomplete_missing_required_fields"
    assert "prompt" in plan["missing_required_fields"]
    assert "scenario_id" in plan["missing_required_fields"]
    assert "generation_output_dir_or_video_path" in plan["missing_required_fields"]
    assert plan["commands"]["post_gpu_review_gate"] is None


def test_markdown_renders_commands_and_boundaries(tmp_path: Path):
    plan = build_post_regeneration_review_plan(
        regeneration_plan(tmp_path),
        failed_alignment_eval="failed_eval.json",
    )
    markdown = render_markdown(plan)

    assert "# Post-regeneration Review Plan: case_retry" in markdown
    assert "scripts/run_post_gpu_review_gate.py" in markdown
    assert "scripts/run_prompt_video_alignment_eval.py" in markdown
    assert "`review_plan_is_not_gpu_approval`: `True`" in markdown
