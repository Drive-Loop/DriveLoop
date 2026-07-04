from scripts.run_alignment_failure_taxonomy import build_taxonomy


def alignment_payload():
    return {
        "generation": {
            "metadata": {
                "prompt_video_alignment": {
                    "checks": [
                        {
                            "name": "object_presence.motorcycle",
                            "required": True,
                            "passed": False,
                            "score": 0.3,
                            "evidence": "A bicycle/cyclist-like object is visible, but reviewer is not confident it is a motorcycle.",
                        },
                        {
                            "name": "spatial_relation.left_lane_change",
                            "required": True,
                            "passed": False,
                            "score": 0.0,
                            "evidence": "No visible lane change from the left was observed. The road center marking appears to be double solid lines.",
                        },
                        {
                            "name": "lighting.daytime",
                            "required": True,
                            "passed": True,
                            "score": 1.0,
                            "evidence": "The scene is daytime.",
                        },
                    ]
                }
            }
        },
        "evaluation": {"diagnosis": {"passed": False}},
        "interpretation": {"video_semantic_claim": "measured_failed"},
    }


def test_taxonomy_labels_motorcycle_and_lane_change_failures():
    taxonomy = build_taxonomy(
        alignment_payload(),
        {"allowed": True, "status": "allowed"},
    )

    assert taxonomy["video_semantic_claim"] == "measured_failed"
    assert taxonomy["alignment_passed"] is False
    assert taxonomy["candidate_support_allowed"] is True
    assert "object_identity_failed" in taxonomy["taxonomy_labels"]
    assert "motorcycle_identity_failed" in taxonomy["taxonomy_labels"]
    assert "lane_change_motion_failed" in taxonomy["taxonomy_labels"]
    assert "road_marking_conflict" in taxonomy["taxonomy_labels"]


def test_taxonomy_hints_do_not_claim_success():
    taxonomy = build_taxonomy(
        alignment_payload(),
        {"allowed": True, "status": "allowed"},
    )

    assert taxonomy["claim_boundary"]["taxonomy_is_diagnostic_not_success_claim"] is True
    assert taxonomy["claim_boundary"]["semantic_success_requires_measured_passed_review"] is True
    assert "candidate_support_is_not_the_primary_blocker" in taxonomy["intervention_hints"]
    assert "run audit-only/runtime tensor checks before any new GPU candidate" in taxonomy["intervention_hints"]


def test_taxonomy_handles_blocked_candidate_support():
    taxonomy = build_taxonomy(
        alignment_payload(),
        {"allowed": False, "status": "blocked"},
    )

    assert taxonomy["candidate_support_allowed"] is False
    assert "fix_or_replace_prompt_conditioned_source_candidate_before_gpu" in taxonomy["intervention_hints"]


def candidate70_alignment_payload():
    return {
        "generation": {
            "metadata": {
                "prompt_video_alignment": {
                    "checks": [
                        {
                            "name": "object_presence.motorcycle_or_scooter_visible",
                            "required": True,
                            "passed": False,
                            "score": 0.0,
                            "evidence": "No clearly visible motorcycle or scooter target can be identified in the sampled frames.",
                        },
                        {
                            "name": "object_consistency.target_actor_trackable_across_frames",
                            "required": True,
                            "passed": False,
                            "score": 0.0,
                            "evidence": "Because the target two-wheeler is not clearly visible, the same target actor cannot be tracked across frames.",
                        },
                        {
                            "name": "maneuver.cut_in_from_left_toward_ego_visible",
                            "required": True,
                            "passed": False,
                            "score": 0.0,
                            "evidence": "The contact sheet does not show a visible motorcycle cut-in from the left toward the ego vehicle/path.",
                        },
                        {
                            "name": "temporal_motion.lateral_displacement_visible",
                            "required": True,
                            "passed": False,
                            "score": 0.0,
                            "evidence": "No target actor lateral displacement is visually measurable across frames.",
                        },
                        {
                            "name": "hdmap_alignment.lane_geometry_visually_consistent_with_scene",
                            "required": True,
                            "passed": False,
                            "score": 0.4,
                            "evidence": "The requested maneuver cannot be visually verified against the scene.",
                        },
                    ]
                }
            }
        },
        "evaluation": {"diagnosis": {"passed": False}},
        "interpretation": {"video_semantic_claim": "measured_failed"},
    }


def test_taxonomy_labels_candidate70_cut_in_visibility_failures():
    taxonomy = build_taxonomy(
        candidate70_alignment_payload(),
        {"allowed": True, "status": "allowed"},
    )

    labels = taxonomy["taxonomy_labels"]
    assert "object_identity_failed" in labels
    assert "motorcycle_identity_failed" in labels
    assert "tracking_identity_failed" in labels
    assert "cut_in_motion_failed" in labels
    assert "lane_change_motion_failed" in labels
    assert "lateral_motion_failed" in labels
    assert "hdmap_alignment_failed" in labels
    assert "make the target two-wheeler larger, visible, and laterally displaced toward the ego path" in taxonomy["intervention_hints"]
    assert taxonomy["claim_boundary"]["semantic_success_requires_measured_passed_review"] is True
