from driveloop.grounding import RuleBasedGrounder
from driveloop.perception_video import Detection, PerceptionVideoEvaluator
from driveloop.schema import DriveLoopRequest, Generation


def _gen_with_car_detections(prompt):
    payload = {"frames": [
        {"frame_index": i,
         "detections": [{"frame_index": i, "label": "car", "confidence": 0.9, "box": [10, 10, 60, 60]}]}
        for i in range(4)
    ], "frame_count": 4}
    return Generation(iteration=0, prompt=prompt, artifacts={},
                      metadata={"perception_detections": payload})


def test_ego_vehicle_does_not_make_car_a_target():
    prompt = "a motorcycle cuts in from the left toward the ego vehicle"
    ev = PerceptionVideoEvaluator().evaluate(_gen_with_car_detections(prompt))
    # 只有 car 检出而目标是 motorcycle,得分必须为 0
    assert ev.metrics["perception_detection_count"] == 0.0
    assert "target_object_not_detected" in ev.diagnosis.reasons


def test_explicit_car_prompt_still_targets_car():
    prompt = "a car drives in front of us"
    ev = PerceptionVideoEvaluator().evaluate(_gen_with_car_detections(prompt))
    assert ev.metrics["perception_detection_count"] == 4.0


def test_grounder_does_not_extract_car_from_ego_vehicle():
    spec = RuleBasedGrounder().ground(
        DriveLoopRequest(prompt="a motorcycle cuts in toward the ego vehicle at night")
    )
    assert [o.category for o in spec.objects] == ["motorcycle"]
