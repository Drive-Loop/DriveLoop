from driveloop.perception_video import Detection, PerceptionVideoEvaluator
from driveloop.schema import Generation


def _gen(dets, frames):
    payload = {"frames": [
        {"frame_index": i,
         "detections": [
             {"frame_index": d.frame_index, "label": d.label, "confidence": d.confidence,
              "box": list(d.box), "track_id": d.track_id}
             for d in dets if d.frame_index == i
         ]} for i in range(frames)
    ], "frame_count": frames}
    return Generation(iteration=0, prompt="a motorcycle scene",
                      artifacts={}, metadata={"perception_detections": payload})


def test_provided_track_ids_override_iou_grouping():
    # 同一位置交替两个 id:IoU tracker 会并成 1 条,id 分轨必须是 2 条
    dets = [
        Detection(0, "motorcycle", 0.9, (10, 10, 60, 60), track_id=1),
        Detection(1, "motorcycle", 0.9, (10, 10, 60, 60), track_id=2),
        Detection(2, "motorcycle", 0.9, (10, 10, 60, 60), track_id=1),
        Detection(3, "motorcycle", 0.9, (10, 10, 60, 60), track_id=2),
    ]
    ev = PerceptionVideoEvaluator(target_labels=["motorcycle"]).evaluate(_gen(dets, 4))
    assert ev.metrics["perception_track_count"] == 2.0
    assert ev.metrics["perception_dominant_track_length"] == 2.0


def test_no_track_ids_falls_back_to_iou():
    dets = [Detection(i, "motorcycle", 0.9, (10, 10, 60, 60)) for i in range(4)]
    ev = PerceptionVideoEvaluator(target_labels=["motorcycle"]).evaluate(_gen(dets, 4))
    assert ev.metrics["perception_track_count"] == 1.0
    assert ev.metrics["perception_dominant_track_length"] == 4.0


def test_detection_from_dict_roundtrips_track_id():
    d = Detection.from_dict({"label": "motorcycle", "confidence": 0.5,
                             "box": [1, 2, 3, 4], "track_id": 7}, frame_index=0)
    assert d.track_id == 7
