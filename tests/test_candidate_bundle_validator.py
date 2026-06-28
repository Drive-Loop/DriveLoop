from scripts.run_candidate_bundle_validator import validate_bundle


def artifact(exists):
    return {"exists": exists}


def manifest_with(**artifacts):
    return {
        "scenario_id": "case",
        "candidate_status": "candidate_video_only",
        "video_semantic_claim": "not_measured",
        "artifacts": {name: artifact(exists) for name, exists in artifacts.items()},
    }


def test_validator_blocks_when_video_missing():
    result = validate_bundle(
        manifest_with(
            video=False,
            post_gpu_gate=False,
            manual_review_report=False,
            alignment_eval=False,
        )
    )

    assert result["bundle_status"] == "blocked"
    assert result["status_reason"] == "candidate video is missing"
    assert result["semantic_success_claim_allowed"] is False
    assert "video" in result["missing_for_review_ready"]


def test_validator_marks_review_ready_before_alignment_eval():
    result = validate_bundle(
        manifest_with(
            video=True,
            post_gpu_gate=True,
            manual_review_report=True,
            alignment_eval=False,
            runtime_audit=True,
        )
    )

    assert result["bundle_status"] == "review_ready"
    assert result["checks"]["alignment_eval_exists"] is False
    assert "alignment_eval" in result["missing_for_measured_ready"]
    assert result["semantic_success_claim_allowed"] is False


def test_validator_marks_measured_ready_without_claiming_success():
    result = validate_bundle(
        manifest_with(
            video=True,
            runtime_audit=True,
            post_gpu_gate=True,
            manual_review_report=True,
            alignment_eval=True,
        )
    )

    assert result["bundle_status"] == "measured_ready"
    assert result["missing_for_measured_ready"] == []
    assert result["semantic_success_claim_allowed"] is False
    assert result["claim_boundary"]["semantic_success_requires_measured_passed_result"] is True
