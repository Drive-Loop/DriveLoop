from scripts.run_prompt_conditional_candidate_audit import audit_candidate


def test_allows_candidate_that_supports_accepted_prompt():
    candidate = {
        "candidate_id": "moto_001",
        "object_tags": ["motorcycle"],
        "motion_tags": ["lane_change"],
        "environment_tags": ["daytime", "urban"],
        "selection_reason_tags": ["motorcycle", "lane_change"],
    }

    result = audit_candidate(
        "daytime urban road with a motorcycle changing lane",
        candidate,
    )

    assert result["status"] == "allowed"
    assert result["allowed"] is True
    assert "lane_change" in result["requested_rules"]
    assert "lane_change" in result["candidate_supported_rules"]
    assert result["missing_requested_support"] == []
    assert result["unrequested_selection_bias"] == []


def test_blocks_candidate_missing_requested_object_support():
    candidate = {
        "candidate_id": "car_001",
        "object_tags": ["car"],
        "motion_tags": ["lane_change"],
        "selection_reason_tags": ["car", "lane_change"],
    }

    result = audit_candidate(
        "daytime urban road with a motorcycle changing lane",
        candidate,
    )

    assert result["status"] == "blocked"
    assert "motorcycle" in result["missing_requested_support"]
    assert result["claim_boundary"]["allowed_candidate_is_not_video_semantic_success"] is True


def test_blocks_unrequested_selection_bias():
    candidate = {
        "candidate_id": "moto_default",
        "object_tags": ["motorcycle"],
        "environment_tags": ["daytime"],
        "selection_reason_tags": ["motorcycle"],
    }

    result = audit_candidate(
        "daytime urban road with regular traffic",
        candidate,
    )

    assert result["status"] == "blocked"
    assert "motorcycle" in result["unrequested_selection_bias"]
    assert "accepted_prompt_must_drive_candidate_selection" in result["claim_boundary"]


def test_does_not_treat_candidate_support_as_semantic_success():
    candidate = {
        "candidate_id": "moto_002",
        "object_tags": ["motorcycle"],
        "motion_tags": ["lane_change"],
        "selection_reason_tags": ["motorcycle", "lane_change"],
    }

    result = audit_candidate(
        "motorcycle lane change",
        candidate,
    )

    assert result["allowed"] is True
    assert result["claim_boundary"]["source_candidate_support_is_not_generation_success"] is True
    assert result["claim_boundary"]["allowed_candidate_is_not_video_semantic_success"] is True


def test_phrase_matching_detects_lane_change_without_matching_train_as_rain():
    candidate = {
        "candidate_id": "train_split_case",
        "split": "train",
        "object_tags": ["motorcycle"],
        "motion_tags": ["lane_related"],
        "environment_tags": ["daytime", "urban"],
        "selection_reason_tags": ["motorcycle", "lane_related"],
    }

    result = audit_candidate(
        "daytime urban road with a motorcycle lane change",
        candidate,
    )

    assert result["allowed"] is True
    assert "lane_change" in result["requested_rules"]
    assert "lane_change" in result["candidate_supported_rules"]
    assert "rainy" not in result["candidate_supported_rules"]
