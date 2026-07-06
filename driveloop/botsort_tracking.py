"""BoT-SORT tracking detector via ultralytics model.track (paper Sec. 3.6)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, List

from driveloop.perception_video import Detection


class BotSortUltralyticsDetector:
    """YOLO detection + BoT-SORT association. Emits Detection with track_id.

    Requires ultralytics >= 8.1 (model.track with tracker="botsort.yaml").
    """

    def __init__(
        self,
        weights: str | Path,
        confidence_threshold: float = 0.25,
        tracker_config: str = "botsort.yaml",
    ) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("ultralytics is required for BoT-SORT tracking") from exc
        self.model = YOLO(str(weights))
        self.confidence_threshold = confidence_threshold
        self.tracker_config = tracker_config

    def reset(self) -> None:
        """Drop tracker state so separate view sequences do not share tracks."""
        self.model.predictor = None

    def detect(self, frame: Any, frame_index: int) -> List[Detection]:
        results = self.model.track(
            source=frame,
            conf=self.confidence_threshold,
            tracker=self.tracker_config,
            persist=True,
            verbose=False,
        )
        result = results[0] if isinstance(results, (list, tuple)) else results
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return []
        names = getattr(result, "names", {}) or {}
        detections: List[Detection] = []
        for box in boxes:
            confidence = float(box.conf[0]) if box.conf is not None else 0.0
            if confidence < self.confidence_threshold:
                continue
            xyxy = box.xyxy[0].tolist()
            track_id = int(box.id[0]) if getattr(box, "id", None) is not None else None
            detections.append(
                Detection(
                    frame_index=frame_index,
                    label=str(names.get(int(box.cls[0]), int(box.cls[0]))),
                    confidence=confidence,
                    box=(float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])),
                    track_id=track_id,
                )
            )
        return detections
