from driveloop.source_ranking import rank_source_candidates, score_source_candidate


def test_source_candidate_ranking_prefers_object_motion_and_map_match():
    scene_spec = {
        "objects": [{"category": "motorcycle"}],
        "environment": {"lighting": "night"},
    }
    condition_plan = {
        "resolved_tags": ["motorcycle_cut_in", "night"],
        "motion_primitives": ["cut_in"],
    }
    candidates = [
        {
            "candidate_id": "car_day",
            "objects": ["car"],
            "lighting": ["day"],
            "motions": ["straight"],
            "has_hdmap": True,
            "has_actor_identity": True,
        },
        {
            "candidate_id": "motorcycle_night_cut_in",
            "objects": ["motorcycle"],
            "lighting": ["night"],
            "long_tail_tags": ["motorcycle_cut_in"],
            "motions": ["cut_in"],
            "has_hdmap": True,
            "has_actor_identity": True,
        },
    ]

    ranking = rank_source_candidates(candidates, scene_spec, condition_plan)

    assert ranking["schema_version"] == "driveloop_source_candidate_ranking.v0"
    assert ranking["best_candidate_id"] == "motorcycle_night_cut_in"
    assert ranking["ready"] is True
    assert ranking["ranked_candidates"][0]["score"] > ranking["ranked_candidates"][1]["score"]
    assert ranking["claim_boundary"]["source_ranking_is_not_video_semantic_success"] is True


def test_source_candidate_score_records_missing_required_object():
    scene_spec = {"objects": [{"category": "motorcycle"}]}
    condition_plan = {"motion_primitives": ["lane_change"]}
    candidate = {
        "candidate_id": "no_motorcycle",
        "objects": ["car"],
        "motions": ["lane_change"],
        "has_hdmap": True,
        "has_actor_identity": True,
    }

    score = score_source_candidate(candidate, scene_spec, condition_plan)

    assert score.ready is False
    assert "motorcycle" in score.missing["required_objects"]
    assert "candidate_missing_required_objects" in score.diagnostics


def test_source_candidate_ranking_blocks_motion_without_map_or_identity():
    scene_spec = {"objects": [{"category": "motorcycle"}]}
    condition_plan = {"motion_primitives": ["cut_in"]}
    candidate = {
        "candidate_id": "structurally_incomplete",
        "objects": ["motorcycle"],
        "motions": ["cut_in"],
        "has_hdmap": False,
        "has_actor_identity": False,
    }

    ranking = rank_source_candidates([candidate], scene_spec, condition_plan)

    row = ranking["ranked_candidates"][0]
    assert row["ready"] is True
    assert "candidate_missing_map_or_lane_geometry" in row["diagnostics"]
    assert "candidate_missing_actor_identity" in row["diagnostics"]
    assert ranking["claim_boundary"]["source_ranking_scores_metadata_compatibility_only"] is True


def test_source_candidate_ranking_handles_empty_candidates():
    ranking = rank_source_candidates([], {}, {})

    assert ranking["candidate_count"] == 0
    assert ranking["best_candidate_id"] is None
    assert ranking["ready"] is False
