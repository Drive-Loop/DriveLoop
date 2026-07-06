import numpy as np

from driveloop.composite_perception import CompositeVideoLayout, CompositePerceptionVideoEvaluator
from driveloop.perception_video import Detection
from driveloop.schema import Generation


class FakeReader:
    def __init__(self, frames):
        self.frames = frames

    def read(self, video_path, max_frames=None):
        return self.frames


class BrightMotorcycleDetector:
    """Returns one motorcycle detection when the crop is bright."""

    def detect(self, frame, frame_index):
        if float(frame.mean()) > 10.0:
            return [Detection(frame_index=frame_index, label="motorcycle", confidence=0.9, box=(10, 10, 60, 60))]
        return []


def _composite_frames(n=4):
    frames = []
    for _ in range(n):
        frame = np.zeros((784, 2688, 3), dtype=np.uint8)
        frame[784 - 256:784, 0:448] = 255  # generated row, view 0 bright
        frame[0:256, 448:896] = 255  # source row bright elsewhere (must be ignored)
        frames.append(frame)
    return frames


def _generation():
    return Generation(iteration=0, prompt="a motorcycle cut-in at night", artifacts={"video": "fake.mp4"}, metadata={})


def test_composite_picks_generated_row_view0():
    evaluator = CompositePerceptionVideoEvaluator(
        detector=BrightMotorcycleDetector(),
        frame_reader=FakeReader(_composite_frames()),
        target_labels=["motorcycle"],
        pass_threshold=0.5,
    )
    evaluation = evaluator.evaluate(_generation())
    assert evaluation.metrics["perception_best_view"] == 0.0
    assert evaluation.score > 0.5
    assert evaluation.metrics["Q_cov"] == 1.0
    assert evaluation.metrics["perception_view1_score"] == 0.0


def test_non_composite_falls_back_to_whole_frame():
    frames = [np.full((100, 100, 3), 255, dtype=np.uint8) for _ in range(3)]
    evaluator = CompositePerceptionVideoEvaluator(
        detector=BrightMotorcycleDetector(),
        frame_reader=FakeReader(frames),
        target_labels=["motorcycle"],
        pass_threshold=0.5,
    )
    evaluation = evaluator.evaluate(_generation())
    assert "perception_best_view" not in evaluation.metrics
    assert evaluation.score > 0.5


def test_layout_extract_view_geometry():
    layout = CompositeVideoLayout()
    frame = np.zeros((784, 2688, 3), dtype=np.uint8)
    view = layout.extract_view(frame, 5)
    assert view.shape == (256, 448, 3)
