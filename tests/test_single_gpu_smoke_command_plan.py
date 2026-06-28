from pathlib import Path

from scripts.run_single_gpu_smoke_command_plan import build_command_plan, expected_video_path


def test_expected_video_path_matches_single_runner_artifact_layout():
    assert expected_video_path(Path("outputs/demo"), "scenario_a") == Path(
        "outputs/demo/artifacts/scenario_a/iteration_00.mp4"
    )


def test_command_plan_is_non_gpu_generator_with_claim_boundaries():
    plan = build_command_plan(
        prompt="daytime urban road with a motorcycle changing lane from the left",
        scenario_id="motorcycle_case",
        output_dir=Path("outputs/case"),
        readiness_output=Path("outputs/gate.json"),
        post_gate_dir=Path("outputs/post_gate"),
    )

    assert plan["does_not_run_gpu"] is True
    assert plan["claim_boundary"]["semantic_claim_allowed_after_gpu"] is False
    assert plan["claim_boundary"]["lane_change_control_claim_allowed"] is False
    assert plan["expected_video_path"] == "outputs/case/artifacts/motorcycle_case/iteration_00.mp4"


def test_command_plan_contains_full_execution_chain():
    plan = build_command_plan(scenario_id="motorcycle_case")

    commands = plan["commands"]
    assert "scripts/run_gpu_smoke_readiness_gate.py" in commands["readiness_gate"]
    assert "scripts/run_driveloop_drivedreamer2.py" in commands["gpu_smoke_candidate_generation"]
    assert "--max-iterations 1" in commands["gpu_smoke_candidate_generation"]
    assert "scripts/run_post_gpu_review_gate.py" in commands["post_gpu_review_gate"]
    assert "scripts/run_prompt_video_alignment_eval.py" in commands["alignment_eval_after_completed_review"]
    assert plan["execution_order"] == [
        "readiness_gate",
        "gpu_smoke_candidate_generation",
        "post_gpu_review_gate",
        "alignment_eval_after_completed_review",
    ]
