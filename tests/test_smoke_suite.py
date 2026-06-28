from argparse import Namespace

from scripts.run_driveloop_smoke_suite import SMOKE_SCENARIOS, run_scenario


def test_smoke_suite_summary_exposes_condition_trace(tmp_path):
    args = Namespace(
        backend="mock",
        output_dir=str(tmp_path),
        max_iterations=1,
        target_score=0.5,
        config_name="drivedreamer2_img_cond_mini_local",
        scenario_id="smoke_foggy_cyclist",
    )

    scenario = next(item for item in SMOKE_SCENARIOS if item["scenario_id"] == "smoke_foggy_cyclist")
    summary = run_scenario(args, scenario, tmp_path)

    assert "condition_trace" in summary
    assert "dd2_condition" in summary["condition_trace"]
    assert "executable_condition" in summary
    assert summary["executable_condition"]["schema_version"] == "dd2_executable_condition.v0"
    assert summary["executable_condition"]["target_backend"] == "drivedreamer2_mini"
    assert summary["executable_condition"]["trace_metadata"]["tensor_control_ready"] is True
    assert (
        summary["executable_condition"]["trace_metadata"]["structural_control_level"]
        == "tensor_override_contract"
    )
