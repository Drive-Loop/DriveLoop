from scripts.run_audit_only_closed_loop_orchestrator import (
    build_orchestrator_trace,
    derive_refinement_prompt,
    render_markdown,
)


def alignment_payload(claim: str, score: float, passed: bool, passed_checks: int, required_checks: int):
    return {
        "generation": {"prompt": "night urban street with a vulnerable road user cut-in"},
        "evaluation": {
            "score": score,
            "metrics": {
                "alignment_required_check_count": float(required_checks),
                "alignment_passed_required_check_count": float(passed_checks),
                "video_artifact_available": 1.0,
                "alignment_measured": 1.0,
            },
            "diagnosis": {
                "passed": passed,
                "reasons": [] if passed else ["alignment_check_failed:object_presence"],
            },
        },
        "interpretation": {"video_semantic_claim": claim},
    }


def test_orchestrator_stops_when_initial_attempt_is_accepted():
    trace = build_orchestrator_trace(
        initial_alignment_eval=alignment_payload("measured_passed", 0.95, True, 9, 9),
        case_id="accepted_case",
    )

    assert trace["closed_loop_status"] == "accepted_without_refinement"
    assert len(trace["attempts"]) == 1
    assert trace["attempts"][0]["accepted"] is True
    assert trace["refinement_proposal"] == {}
    assert trace["claim_boundary"]["orchestrator_does_not_run_gpu"] is True


def test_orchestrator_diagnoses_and_waits_for_generation_without_retry_eval():
    trace = build_orchestrator_trace(
        initial_alignment_eval=alignment_payload("measured_failed", 0.2, False, 2, 9),
        failure_taxonomy={
            "taxonomy_labels": ["object_identity_failed", "tracking_identity_failed"],
            "failed_required_checks": [],
        },
        case_id="waiting_case",
    )

    assert trace["closed_loop_status"] == "diagnosed_and_refinement_proposed_waiting_for_generation"
    assert trace["attempts"][0]["accepted"] is False
    assert trace["refinement_proposal"]["does_not_run_gpu"] is True
    assert trace["refinement_proposal"]["retry_policy"]["explicit_gpu_retry_approval_required"] is True
    assert any(step["step"] == "regenerate" and step["status"] == "blocked_requires_explicit_generation_step" for step in trace["algorithm_trace"])


def test_orchestrator_records_failed_to_passed_when_retry_eval_is_available():
    trace = build_orchestrator_trace(
        initial_alignment_eval=alignment_payload("measured_failed", 0.361111, False, 3, 9),
        retry_alignment_eval=alignment_payload("measured_passed", 0.916667, True, 9, 9),
        failure_taxonomy={"taxonomy_labels": ["cut_in_motion_failed"], "failed_required_checks": []},
        refinement_proposal={
            "source_prompt": "initial",
            "refined_prompt": "refined",
            "does_not_run_gpu": True,
            "semantic_success_claim_allowed": False,
            "retry_policy": {
                "explicit_gpu_retry_approval_required": True,
                "post_gpu_review_required_after_any_retry": True,
                "proposal_is_not_gpu_approval": True,
            },
        },
        case_id="candidate70",
    )

    assert trace["closed_loop_status"] == "measured_failed_to_measured_passed"
    assert len(trace["attempts"]) == 2
    assert trace["attempts"][1]["accepted"] is True
    assert trace["refinement_proposal"]["source"] == "provided_refinement_proposal"
    assert trace["claim_boundary"]["orchestrator_does_not_call_dd2"] is True


def test_derived_prompt_uses_failure_labels():
    prompt = derive_refinement_prompt(
        "night urban scene",
        {
            "taxonomy_labels": [
                "object_identity_failed",
                "tracking_identity_failed",
                "lateral_motion_failed",
                "hdmap_alignment_failed",
            ]
        },
    )

    assert prompt is not None
    assert "large, visible" in prompt
    assert "trackable" in prompt
    assert "measurable lateral motion" in prompt
    assert "lane geometry" in prompt


def test_markdown_renders_algorithm_trace_and_boundaries():
    trace = build_orchestrator_trace(
        initial_alignment_eval=alignment_payload("measured_failed", 0.361111, False, 3, 9),
        retry_alignment_eval=alignment_payload("measured_passed", 0.916667, True, 9, 9),
        failure_taxonomy={"taxonomy_labels": ["cut_in_motion_failed"], "failed_required_checks": []},
        case_id="candidate70",
    )

    markdown = render_markdown(trace)

    assert "# Audit-only Closed-loop Trace: candidate70" in markdown
    assert "| 0 | pre_refinement | `measured_failed` | 0.361111 | 3/9 | False |" in markdown
    assert "| 1 | post_refinement_retry | `measured_passed` | 0.916667 | 9/9 | True |" in markdown
    assert "`regenerate`: `blocked_requires_explicit_generation_step`" in markdown
    assert "`orchestrator_does_not_run_gpu`: `True`" in markdown
