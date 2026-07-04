from scripts.run_audit_only_regeneration_command_planner import (
    build_regeneration_command_plan,
    render_markdown,
    source_binding_summary,
)


def trace_payload():
    return {
        "case_id": "candidate70_audit_only_closed_loop",
        "closed_loop_status": "diagnosed_and_refinement_proposed_waiting_for_generation",
        "refinement_proposal": {
            "refined_prompt": "night urban road with visible target actor.",
            "source_prompt": "night urban road.",
            "does_not_run_gpu": True,
            "semantic_success_claim_allowed": False,
            "retry_policy": {
                "explicit_gpu_retry_approval_required": True,
                "post_gpu_review_required_after_any_retry": True,
                "proposal_is_not_gpu_approval": True,
            },
        },
        "algorithm_trace": [
            {"step": "evaluate_attempt_0", "status": "completed"},
            {"step": "diagnose_failure", "status": "completed"},
            {"step": "refine_prompt_or_condition", "status": "completed"},
            {"step": "regenerate", "status": "blocked_requires_explicit_generation_step"},
        ],
    }


def binding_payload():
    return {
        "runtime_binding_assessment": {
            "source_sample_binding": {
                "ready": True,
                "dataset_dir": "/mnt/driveloop_full/candidate70",
                "selector": {
                    "source_candidate_id": "candidate70",
                    "instance_token": "abc123",
                    "identity_summary_path": "outputs/identity/summary.json",
                },
            }
        }
    }


def test_source_binding_summary_extracts_runtime_binding_fields():
    binding = source_binding_summary(binding_payload())

    assert binding["ready"] is True
    assert binding["dataset_dir"] == "/mnt/driveloop_full/candidate70"
    assert binding["source_candidate_id"] == "candidate70"
    assert binding["instance_token"] == "abc123"
    assert binding["identity_summary_path"] == "outputs/identity/summary.json"


def test_planner_builds_do_not_execute_command_draft():
    plan = build_regeneration_command_plan(
        trace_payload(),
        binding_payload(),
        scenario_id="candidate70_retry_draft",
        output_dir="outputs/driveloop/candidate70_retry_draft",
    )

    assert plan["command_status"] == "draft_ready_for_explicit_approval"
    assert plan["missing_required_fields"] == []
    assert plan["generated_command"]["requires_explicit_user_approval"] is True
    assert plan["generated_command"]["do_not_execute_automatically"] is True
    assert plan["generated_command"]["would_run_dd2_if_executed"] is True
    assert plan["planner_execution"]["does_not_run_gpu"] is True
    assert plan["resolved_inputs"]["source_candidate_id"] == "candidate70"
    assert plan["resolved_inputs"]["baseline_dataset_dir"] == "/mnt/driveloop_full/candidate70"
    assert "--prompt" in plan["generated_command"]["argv"]
    assert "night urban road with visible target actor." in plan["generated_command"]["argv"]


def test_planner_reports_missing_required_prompt():
    trace = trace_payload()
    trace["refinement_proposal"] = {}
    plan = build_regeneration_command_plan(trace, binding_payload())

    assert plan["command_status"] == "draft_incomplete_missing_required_fields"
    assert "refined_prompt" in plan["missing_required_fields"]
    assert plan["generated_command"]["shell"] is None
    assert plan["claim_boundary"]["command_plan_is_not_gpu_approval"] is True


def test_planner_requires_blocked_regeneration_step():
    trace = trace_payload()
    trace["algorithm_trace"] = [{"step": "evaluate_attempt_0", "status": "completed"}]
    plan = build_regeneration_command_plan(trace, binding_payload())

    assert plan["command_status"] == "draft_incomplete_missing_required_fields"
    assert "blocked_regeneration_step" in plan["missing_required_fields"]


def test_markdown_includes_command_and_claim_boundary():
    plan = build_regeneration_command_plan(
        trace_payload(),
        binding_payload(),
        scenario_id="candidate70_retry_draft",
    )
    markdown = render_markdown(plan)

    assert "# Regeneration Command Plan: candidate70_audit_only_closed_loop" in markdown
    assert "python" in markdown
    assert "scripts/run_driveloop_drivedreamer2.py" in markdown
    assert "`command_plan_is_not_gpu_approval`: `True`" in markdown
