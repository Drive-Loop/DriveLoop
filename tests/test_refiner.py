from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import Diagnosis, DriveLoopRequest, Evaluation


def test_refiner_keeps_prompt_when_alignment_not_measured_only():
    request = DriveLoopRequest(prompt="daytime urban road with a motorcycle")
    evaluation = Evaluation(
        score=0.0,
        diagnosis=Diagnosis(
            passed=False,
            reasons=["video_alignment_not_measured"],
            suggested_actions=[
                "run a perception, VLM, or human-review alignment pass and attach an auditable report"
            ],
        ),
    )

    refinement = RuleBasedRefiner().refine(request, evaluation)

    assert refinement.prompt == request.prompt
    assert "run prompt-video alignment review before claiming semantic success" in refinement.notes
    assert refinement.condition["alignment_feedback"]["status"] == "not_measured"
    assert refinement.condition["alignment_feedback"]["control_level"] == "text_feedback_only"


def test_refiner_adds_text_constraints_for_failed_alignment_checks():
    request = DriveLoopRequest(prompt="daytime urban road with a motorcycle")
    evaluation = Evaluation(
        score=0.0,
        diagnosis=Diagnosis(
            passed=False,
            reasons=[
                "alignment_check_failed:object_presence.motorcycle",
                "alignment_check_failed:spatial_relation.left_lane_change",
            ],
            suggested_actions=["inspect failed alignment checks before making semantic claims"],
        ),
    )

    refinement = RuleBasedRefiner().refine(request, evaluation)

    assert "a motorcycle must be visibly present" in refinement.prompt
    assert "the motorcycle performs a visible lane change from the left" in refinement.prompt
    assert "panoramic multi-view video" in refinement.prompt
    feedback = refinement.condition["alignment_feedback"]
    assert feedback["status"] == "measured_failed"
    assert feedback["control_level"] == "text_feedback_only"
    assert feedback["failed_checks"] == [
        "object_presence.motorcycle",
        "spatial_relation.left_lane_change",
    ]
    assert "a motorcycle must be visibly present" in feedback["requested_visual_constraints"]


def test_refiner_preserves_existing_prompt_quality_refinement():
    request = DriveLoopRequest(prompt="make a driving video")
    evaluation = Evaluation(
        score=0.45,
        diagnosis=Diagnosis(
            passed=False,
            reasons=[
                "prompt_missing_realism",
                "weather_or_lighting_unspecified",
                "traffic_actor_unspecified",
            ],
            suggested_actions=[
                "add realistic autonomous driving scene wording",
                "specify weather or lighting",
                "add explicit traffic actor or maneuver",
            ],
        ),
    )

    refinement = RuleBasedRefiner().refine(request, evaluation)

    assert "realistic autonomous driving scene" in refinement.prompt
    assert "daytime clear weather" in refinement.prompt
    assert "surrounded by vehicles with a safe lane-change interaction" in refinement.prompt
    assert "panoramic multi-view video" in refinement.prompt


def test_refiner_builds_perception_feedback_for_detector_failures():
    request = DriveLoopRequest(prompt="night road with a motorcycle cut in")
    evaluation = Evaluation(
        score=0.2,
        diagnosis=Diagnosis(
            passed=False,
            reasons=[
                "low_detection_coverage",
                "unstable_track_coverage",
                "identity_inconsistent",
            ],
            suggested_actions=[
                "make the target actor visible across more frames",
                "reduce occlusion and keep motion temporally coherent",
            ],
        ),
    )

    refinement = RuleBasedRefiner().refine(request, evaluation)

    assert "target actor remains large, visible, and unoccluded" in refinement.prompt
    assert "continuous motion without occlusion" in refinement.prompt
    assert "same target actor identity" in refinement.prompt

    feedback = refinement.condition["perception_feedback"]
    assert feedback["schema_version"] == "driveloop_perception_feedback.v0"
    assert feedback["status"] == "measured_failed"
    assert feedback["control_level"] == "text_and_condition_feedback"
    assert feedback["failed_checks"] == [
        "low_detection_coverage",
        "unstable_track_coverage",
        "identity_inconsistent",
    ]


def test_refiner_builds_source_selection_feedback_for_source_mismatch():
    request = DriveLoopRequest(prompt="night road with a motorcycle cut in")
    evaluation = Evaluation(
        score=0.0,
        diagnosis=Diagnosis(
            passed=False,
            reasons=[
                "source_selection_unavailable",
                "no_dd2_candidate_contains_requested_source_tokens",
            ],
            suggested_actions=[
                "select another source candidate or rebuild the runtime dataset for the requested source tokens",
            ],
        ),
    )

    refinement = RuleBasedRefiner().refine(request, evaluation)

    feedback = refinement.condition["source_selection_feedback"]
    assert feedback["schema_version"] == "driveloop_source_selection_feedback.v0"
    assert feedback["status"] == "source_unavailable"
    assert feedback["policy"] == "select_alternate_source_or_rebuild_runtime_dataset_before_generation_retry"
    assert "select or rebuild a source candidate before retrying generation" in refinement.notes


def test_refiner_builds_runtime_control_feedback_for_unsupported_runtime_controls():
    request = DriveLoopRequest(prompt="night road with a motorcycle lane change")
    evaluation = Evaluation(
        score=0.0,
        diagnosis=Diagnosis(
            passed=False,
            reasons=[
                "dd2_tensor_control_not_ready",
                "dd2_structural_control_plan_only",
                "unsupported_control:trajectory_control",
            ],
            suggested_actions=[
                "connect actor, trajectory, and HDMap tensor-level structural overrides",
            ],
        ),
    )

    refinement = RuleBasedRefiner().refine(request, evaluation)

    feedback = refinement.condition["runtime_control_feedback"]
    assert feedback["schema_version"] == "driveloop_runtime_control_feedback.v0"
    assert feedback["status"] == "runtime_control_unavailable"
    assert "unsupported_control:trajectory_control" in feedback["failed_reasons"]
    assert any("runtime controls are unavailable" in note for note in refinement.notes)


def test_refiner_adds_candidate70_semantic_protocol_constraints():
    request = DriveLoopRequest(prompt="night urban road with a motorcycle")
    evaluation = Evaluation(
        score=0.36,
        diagnosis=Diagnosis(
            passed=False,
            reasons=[
                "alignment_check_failed:object_presence.motorcycle_or_scooter_visible",
                "alignment_check_failed:object_consistency.target_actor_trackable_across_frames",
                "alignment_check_failed:maneuver.cut_in_from_left_toward_ego_visible",
                "alignment_check_failed:temporal_motion.lateral_displacement_visible",
                "alignment_check_failed:spatial_relation.starts_left_or_adjacent_lane_and_moves_toward_ego_path",
                "alignment_check_failed:hdmap_alignment.lane_geometry_visually_consistent_with_scene",
            ],
            suggested_actions=["inspect failed alignment checks before making semantic claims"],
        ),
    )

    refinement = RuleBasedRefiner().refine(request, evaluation)

    assert "clearly visible motorcycle or scooter target" in refinement.prompt
    assert "same target motorcycle remains trackable" in refinement.prompt
    assert "visibly cuts in from the left toward the ego path" in refinement.prompt
    assert "measurable lateral displacement" in refinement.prompt
    assert "visible lane geometry stays consistent" in refinement.prompt

    feedback = refinement.condition["alignment_feedback"]
    assert feedback["status"] == "measured_failed"
    assert "object_presence.motorcycle_or_scooter_visible" in feedback["failed_checks"]
    assert "the same target motorcycle remains trackable across frames" in feedback["requested_visual_constraints"]
