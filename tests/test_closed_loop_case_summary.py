from scripts.run_closed_loop_case_summary import build_case_summary, render_markdown


def alignment_payload(claim: str, score: float, passed: bool, passed_checks: int, required_checks: int):
    return {
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


def test_summary_records_measured_failed_to_passed_case():
    summary = build_case_summary(
        failed_alignment_eval=alignment_payload("measured_failed", 0.361111, False, 3, 9),
        retry_alignment_eval=alignment_payload("measured_passed", 0.916667, True, 9, 9),
        failure_taxonomy={
            "video_semantic_claim": "measured_failed",
            "alignment_passed": False,
            "taxonomy_labels": ["object_identity_failed", "cut_in_motion_failed"],
            "intervention_hints": ["make the target visible"],
        },
        failed_perception_eval={
            "evaluation": {
                "metrics": {
                    "perception_measured": 1.0,
                    "Q_cov": 0.0,
                    "Q_conf": 0.0,
                    "Q_track": 0.0,
                    "Q_id": 0.0,
                    "Q_box": 0.0,
                    "perception_detection_count": 0.0,
                    "perception_track_count": 0.0,
                }
            }
        },
        refinement_proposal={
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

    assert summary["closed_loop_status"] == "measured_failed_to_measured_passed"
    assert summary["attempts"]["pre_refinement"]["score"] == 0.361111
    assert summary["attempts"]["post_refinement_retry"]["passed_required_check_count"] == 9.0
    assert "object_identity_failed" in summary["failure_diagnosis"]["taxonomy_labels"]
    assert summary["failed_attempt_perception"]["metrics"]["Q_cov"] == 0.0
    assert summary["refinement_proposal"]["explicit_gpu_retry_approval_required"] is True
    assert summary["claim_boundary"]["summary_does_not_run_gpu"] is True
    assert summary["claim_boundary"]["closed_loop_case_is_not_strict_open_loop_baseline_comparison"] is True


def test_summary_does_not_upgrade_incomplete_retry_to_success():
    summary = build_case_summary(
        failed_alignment_eval=alignment_payload("measured_failed", 0.2, False, 1, 9),
        retry_alignment_eval=alignment_payload("measured_failed", 0.5, False, 5, 9),
    )

    assert summary["closed_loop_status"] == "incomplete_or_not_measured"
    assert summary["claim_boundary"]["video_or_tensor_existence_is_not_semantic_success"] is True


def test_markdown_renders_core_table_and_boundaries():
    summary = build_case_summary(
        failed_alignment_eval=alignment_payload("measured_failed", 0.361111, False, 3, 9),
        retry_alignment_eval=alignment_payload("measured_passed", 0.916667, True, 9, 9),
        failure_taxonomy={"taxonomy_labels": ["tracking_identity_failed"]},
        case_id="candidate70",
    )

    markdown = render_markdown(summary)

    assert "# Closed-loop Case Summary: candidate70" in markdown
    assert "| Pre-refinement | `measured_failed` | 0.361111 | 3/9 | False |" in markdown
    assert "| Post-refinement retry | `measured_passed` | 0.916667 | 9/9 | True |" in markdown
    assert "`tracking_identity_failed`" in markdown
    assert "`summary_does_not_generate_video`: `True`" in markdown
