from driveloop.perception_video import Detection, PerceptionVideoEvaluator
from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import Diagnosis, DriveLoopRequest, Evaluation, Generation

MOTION_META = {"scene_specification": {"motion_primitives": ["lane_change"]}}


def _gen(dets, frames, metadata=None):
    payload = {"frames": [
        {"frame_index": i,
         "detections": [
             {"frame_index": d.frame_index, "label": d.label, "confidence": d.confidence, "box": list(d.box)}
             for d in dets if d.frame_index == i
         ]} for i in range(frames)
    ], "frame_count": frames}
    return Generation(iteration=0, prompt="a motorcycle changes lane",
                      artifacts={}, metadata={**(metadata or {}), "perception_detections": payload})


def _static_dets(n=4):
    return [Detection(i, "motorcycle", 0.9, (100, 100, 150, 150)) for i in range(n)]


def _moving_dets(n=4):
    return [Detection(i, "motorcycle", 0.9, (100 + 40 * i, 100, 150 + 40 * i, 150)) for i in range(n)]


def test_static_target_flagged_when_motion_requested():
    ev = PerceptionVideoEvaluator(target_labels=["motorcycle"]).evaluate(_gen(_static_dets(), 4, MOTION_META))
    assert "target_appears_static" in ev.diagnosis.reasons
    assert ev.metrics["perception_dominant_motion_over_width"] == 0.0


def test_moving_target_not_flagged():
    ev = PerceptionVideoEvaluator(target_labels=["motorcycle"]).evaluate(_gen(_moving_dets(), 4, MOTION_META))
    assert "target_appears_static" not in ev.diagnosis.reasons
    assert ev.metrics["perception_dominant_motion_over_width"] > 2.0


def test_static_ok_when_no_motion_requested():
    ev = PerceptionVideoEvaluator(target_labels=["motorcycle"]).evaluate(_gen(_static_dets(), 4))
    assert "target_appears_static" not in ev.diagnosis.reasons


def test_refiner_responds_to_static_reason():
    refinement = RuleBasedRefiner().refine(
        DriveLoopRequest(prompt="a motorcycle changes lane"),
        Evaluation(0.3, {}, Diagnosis(False, ["target_appears_static"], [])),
    )
    assert "not parked and not stationary" in refinement.prompt
