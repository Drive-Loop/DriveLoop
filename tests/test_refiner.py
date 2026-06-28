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
    request = DriveLoopRequest(prompt="daytime urban road")
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
