from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from driveloop.perception_video import PerceptionVideoEvaluator
from driveloop.schema import Diagnosis, Evaluation, Generation


@dataclass(frozen=True)
class CompositeVideoLayout:
    """Layout of the DD2 tester debug mosaic.

    The DD2 tester saves a composite video: source frames and condition
    visualization rows are stacked above the generated row, and camera views
    are tiled horizontally. Perception must only see the generated row,
    split into per-camera views.
    """

    view_width: int = 448
    generated_row_height: int = 256
    num_views: int = 6
    generated_row_at_bottom: bool = True

    def extract_view(self, frame: Any, view_index: int) -> Any:
        height = frame.shape[0]
        y0 = height - self.generated_row_height if self.generated_row_at_bottom else 0
        x0 = view_index * self.view_width
        return frame[y0:y0 + self.generated_row_height, x0:x0 + self.view_width]

    def matches(self, frame: Any) -> bool:
        height, width = frame.shape[:2]
        return width >= self.view_width * self.num_views and height > self.generated_row_height


class CompositePerceptionVideoEvaluator(PerceptionVideoEvaluator):
    """Perception evaluator that crops the generated row of a DD2 composite
    video and evaluates each camera view independently, reporting the best
    view. Falls back to whole-frame evaluation for non-composite videos."""

    def __init__(self, *args: Any, layout: CompositeVideoLayout | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.layout = layout or CompositeVideoLayout()

    def evaluate(self, generation: Generation) -> Evaluation:
        if self._detections_from_metadata(generation.metadata) is not None:
            return super().evaluate(generation)
        video_path = generation.artifacts.get("video")
        if not video_path or self.detector is None:
            return super().evaluate(generation)

        frames = self.frame_reader.read(Path(video_path), max_frames=self.max_frames)
        if not frames:
            return Evaluation(
                0.0,
                {"perception_measured": 1.0, "perception_frame_count": 0.0},
                Diagnosis(False, ["video_has_no_readable_frames"], ["verify video decoding"]),
            )
        if not self.layout.matches(frames[0]):
            return super().evaluate(generation)

        best_evaluation: Evaluation | None = None
        best_view = -1
        view_scores: Dict[int, float] = {}
        for view_index in range(self.layout.num_views):
            reset = getattr(self.detector, "reset", None)
            if callable(reset):
                reset()
            payload_frames = []
            for frame_index, frame in enumerate(frames):
                view = self.layout.extract_view(frame, view_index)
                detections = self.detector.detect(view, frame_index)
                payload_frames.append({
                    "frame_index": frame_index,
                    "detections": [
                        {
                            "frame_index": d.frame_index,
                            "label": d.label,
                            "confidence": d.confidence,
                            "box": list(d.box),
                            "track_id": d.track_id,
                        }
                        for d in detections
                    ],
                })
            view_generation = Generation(
                iteration=generation.iteration,
                prompt=generation.prompt,
                artifacts=dict(generation.artifacts),
                metadata={
                    **generation.metadata,
                    "perception_detections": {"frames": payload_frames, "frame_count": len(frames)},
                },
            )
            evaluation = super().evaluate(view_generation)
            view_scores[view_index] = evaluation.score
            if best_evaluation is None or evaluation.score > best_evaluation.score:
                best_evaluation = evaluation
                best_view = view_index

        metrics = dict(best_evaluation.metrics)
        for view_index, score in view_scores.items():
            metrics["perception_view%d_score" % view_index] = score
        metrics["perception_best_view"] = float(best_view)
        metrics["perception_layout_views"] = float(self.layout.num_views)
        metrics["perception_generated_row_height"] = float(self.layout.generated_row_height)
        return Evaluation(best_evaluation.score, metrics, best_evaluation.diagnosis)
