import json
import math
import os
from collections import Counter, defaultdict

import numpy as np

from driveloop.evaluation.evaluator import BaseEvaluator, EvaluationError, EvaluationResult


COCO_TRAFFIC_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    9: "traffic light",
    11: "stop sign",
}


def parse_class_ids(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]

    text = str(value).strip()
    if not text or text.lower() in {"none", "all"}:
        return None

    class_ids = []
    for item in text.split(","):
        item = item.strip()
        if item:
            class_ids.append(int(item))
    return class_ids


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, float(value)))


def _to_numpy(value):
    if value is None:
        return None
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        return value.numpy()
    return np.asarray(value)


class PerceptionEvaluator(BaseEvaluator):
    """
    Evaluate a generated video with YOLO detection and BoT-SORT tracking.

    The score is a perception-oriented proxy for whether the rendered traffic
    participant can be stably detected and tracked by an autonomous-driving
    perception stack. It does not replace a full planner or simulator benchmark.
    """

    DEFAULT_WEIGHTS = {
        "detection_coverage": 0.30,
        "mean_confidence": 0.25,
        "dominant_track_coverage": 0.20,
        "id_consistency": 0.15,
        "bbox_stability": 0.10,
    }

    def __init__(
        self,
        threshold,
        output_dir,
        model_name="yolo11m.pt",
        tracker="botsort.yaml",
        class_ids=None,
        confidence=0.25,
        iou=0.50,
        image_size=1280,
        device=None,
        weights=None,
    ):
        self.threshold = float(threshold)
        self.output_dir = output_dir
        self.model_name = model_name
        self.tracker = tracker
        self.class_ids = parse_class_ids(class_ids)
        self.confidence = float(confidence)
        self.iou = float(iou)
        self.image_size = int(image_size)
        self.device = device
        self.weights = dict(self.DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)

    def evaluate(self, video_path, prompt, metadata):
        if not os.path.exists(video_path):
            raise EvaluationError(f"Video path does not exist: {video_path}")

        frame_records = self._run_tracker(video_path)
        payload = self._compute_payload(
            frame_records=frame_records,
            threshold=self.threshold,
            prompt=prompt,
            metadata=metadata,
            model_name=self.model_name,
            tracker=self.tracker,
            class_ids=self.class_ids,
            weights=self.weights,
        )
        self._write_details(payload, metadata)
        return EvaluationResult.from_mapping(payload, threshold=self.threshold)

    def _run_tracker(self, video_path):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise EvaluationError(
                "Perception evaluator requires Ultralytics. Install it with "
                "`pip install ultralytics` in the ChatSim environment."
            ) from exc

        model = YOLO(self.model_name)
        track_kwargs = {
            "source": video_path,
            "stream": True,
            "persist": True,
            "tracker": self.tracker,
            "classes": self.class_ids,
            "conf": self.confidence,
            "iou": self.iou,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device:
            track_kwargs["device"] = self.device

        frame_records = []
        try:
            results = model.track(**track_kwargs)
            for frame_index, result in enumerate(results):
                frame_records.append(self._result_to_frame_record(frame_index, result))
        except Exception as exc:
            raise EvaluationError(f"YOLO/BoT-SORT perception evaluation failed: {exc}") from exc

        if not frame_records:
            raise EvaluationError("Perception evaluator received no frames from YOLO tracking.")
        return frame_records

    def _result_to_frame_record(self, frame_index, result):
        height, width = self._extract_shape(result)
        boxes = getattr(result, "boxes", None)
        detections = []

        if boxes is not None and len(boxes) > 0:
            xyxy = _to_numpy(getattr(boxes, "xyxy", None))
            conf = _to_numpy(getattr(boxes, "conf", None))
            cls = _to_numpy(getattr(boxes, "cls", None))
            track_ids = _to_numpy(getattr(boxes, "id", None))

            if track_ids is None:
                track_ids = [None] * len(xyxy)
            if conf is None:
                conf = np.ones(len(xyxy), dtype=np.float32)
            if cls is None:
                cls = np.full(len(xyxy), -1, dtype=np.int32)

            for det_index, box in enumerate(xyxy):
                x1, y1, x2, y2 = [float(v) for v in box[:4]]
                area_ratio = self._box_area_ratio((x1, y1, x2, y2), width, height)
                track_id = track_ids[det_index]
                if track_id is not None and not np.isnan(track_id):
                    track_id = int(track_id)
                else:
                    track_id = None

                class_id = int(cls[det_index])
                detections.append(
                    {
                        "track_id": track_id,
                        "class_id": class_id,
                        "class_name": COCO_TRAFFIC_CLASSES.get(class_id, str(class_id)),
                        "confidence": float(conf[det_index]),
                        "xyxy": [x1, y1, x2, y2],
                        "area_ratio": float(area_ratio),
                    }
                )

        primary = self._select_primary_detection(detections)
        return {
            "frame_index": int(frame_index),
            "width": int(width),
            "height": int(height),
            "detections": detections,
            "primary": primary,
        }

    def _extract_shape(self, result):
        shape = getattr(result, "orig_shape", None)
        if shape and len(shape) >= 2:
            return int(shape[0]), int(shape[1])
        image = getattr(result, "orig_img", None)
        if image is not None and hasattr(image, "shape") and len(image.shape) >= 2:
            return int(image.shape[0]), int(image.shape[1])
        return 1, 1

    def _box_area_ratio(self, box, width, height):
        x1, y1, x2, y2 = box
        area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        frame_area = max(1.0, float(width) * float(height))
        return _clamp(area / frame_area)

    def _select_primary_detection(self, detections):
        if not detections:
            return None
        return max(
            detections,
            key=lambda det: det["confidence"] * (1.0 + math.sqrt(max(det["area_ratio"], 0.0))),
        )

    def _write_details(self, payload, metadata):
        if not self.output_dir:
            return
        os.makedirs(self.output_dir, exist_ok=True)
        attempt_id = int(metadata.get("attempt_id", 0))
        output_path = os.path.join(
            self.output_dir,
            f"attempt_{attempt_id:02d}_perception_evaluation.json",
        )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @classmethod
    def _compute_payload(
        cls,
        frame_records,
        threshold,
        prompt="",
        metadata=None,
        model_name="yolo11m.pt",
        tracker="botsort.yaml",
        class_ids=None,
        weights=None,
    ):
        metadata = metadata or {}
        weights = dict(cls.DEFAULT_WEIGHTS if weights is None else weights)
        total_weight = sum(max(0.0, value) for value in weights.values()) or 1.0
        total_frames = len(frame_records)

        primary_detections = [
            record["primary"] for record in frame_records if record.get("primary") is not None
        ]
        frames_with_detection = len(primary_detections)
        detection_coverage = frames_with_detection / max(1, total_frames)
        mean_confidence = (
            float(np.mean([det["confidence"] for det in primary_detections]))
            if primary_detections else 0.0
        )

        primary_ids = [
            det["track_id"] for det in primary_detections if det.get("track_id") is not None
        ]
        id_counter = Counter(primary_ids)
        id_consistency = (
            max(id_counter.values()) / max(1, len(primary_ids))
            if primary_ids else 0.0
        )
        estimated_id_switches = cls._count_id_switches(primary_ids)

        tracks = cls._collect_tracks(frame_records)
        dominant_track_id, dominant_track = cls._select_dominant_track(tracks)
        dominant_track_coverage = (
            len(dominant_track) / max(1, total_frames) if dominant_track else 0.0
        )
        bbox_stability, bbox_jitter = cls._compute_bbox_stability(dominant_track)
        occlusion_recovery = cls._compute_occlusion_recovery(dominant_track, total_frames)
        class_consistency = cls._compute_class_consistency(primary_detections)

        normalized_metrics = {
            "detection_coverage": _clamp(detection_coverage),
            "mean_confidence": _clamp(mean_confidence),
            "dominant_track_coverage": _clamp(dominant_track_coverage),
            "id_consistency": _clamp(id_consistency),
            "bbox_stability": _clamp(bbox_stability),
        }
        score = sum(
            normalized_metrics[name] * max(0.0, weights.get(name, 0.0))
            for name in normalized_metrics
        ) / total_weight
        score = _clamp(score)

        metrics = {
            "total_frames": total_frames,
            "frames_with_detection": frames_with_detection,
            "detection_coverage": normalized_metrics["detection_coverage"],
            "mean_confidence": normalized_metrics["mean_confidence"],
            "dominant_track_id": dominant_track_id,
            "dominant_track_coverage": normalized_metrics["dominant_track_coverage"],
            "id_consistency": normalized_metrics["id_consistency"],
            "estimated_id_switches": estimated_id_switches,
            "bbox_stability": normalized_metrics["bbox_stability"],
            "bbox_jitter": float(bbox_jitter),
            "occlusion_recovery": float(occlusion_recovery),
            "class_consistency": float(class_consistency),
            "detected_track_count": len(tracks),
            "score_weights": weights,
        }
        failure_reasons, suggestions = cls._build_feedback(metrics, threshold, score)
        class_names = [
            COCO_TRAFFIC_CLASSES.get(class_id, str(class_id))
            for class_id in class_ids
        ] if class_ids else ["all classes"]
        summary = (
            f"Perception score {score:.3f} using {model_name} with {tracker}. "
            f"Detected target-like objects in {frames_with_detection}/{total_frames} frames."
        )

        return {
            "score": score,
            "passed": score >= threshold,
            "threshold": float(threshold),
            "summary": summary,
            "failure_reasons": failure_reasons,
            "suggestions": suggestions,
            "metrics": metrics,
            "raw": {
                "prompt": prompt,
                "attempt_id": metadata.get("attempt_id"),
                "model_name": model_name,
                "tracker": tracker,
                "class_ids": class_ids,
                "class_names": class_names,
            },
        }

    @staticmethod
    def _count_id_switches(primary_ids):
        if len(primary_ids) < 2:
            return 0
        switches = 0
        previous = primary_ids[0]
        for track_id in primary_ids[1:]:
            if track_id != previous:
                switches += 1
            previous = track_id
        return switches

    @staticmethod
    def _collect_tracks(frame_records):
        tracks = defaultdict(list)
        for record in frame_records:
            frame_index = record["frame_index"]
            for det in record.get("detections", []):
                track_id = det.get("track_id")
                if track_id is None:
                    continue
                item = dict(det)
                item["frame_index"] = frame_index
                item["width"] = record.get("width", 1)
                item["height"] = record.get("height", 1)
                tracks[track_id].append(item)
        return dict(tracks)

    @staticmethod
    def _select_dominant_track(tracks):
        if not tracks:
            return None, []

        def track_score(items):
            confidence = np.mean([item["confidence"] for item in items])
            area = np.mean([item["area_ratio"] for item in items])
            return len(items) * (0.75 + 0.25 * confidence) * (1.0 + math.sqrt(max(area, 0.0)))

        track_id = max(tracks, key=lambda key: track_score(tracks[key]))
        return int(track_id), sorted(tracks[track_id], key=lambda item: item["frame_index"])

    @staticmethod
    def _compute_bbox_stability(track_items):
        if len(track_items) < 3:
            return (0.0, 1.0) if not track_items else (0.5, 0.5)

        jitter_values = []
        for previous, current in zip(track_items[:-1], track_items[1:]):
            if current["frame_index"] - previous["frame_index"] > 1:
                continue
            prev_box = previous["xyxy"]
            curr_box = current["xyxy"]
            width = max(1.0, float(current.get("width", 1)))
            height = max(1.0, float(current.get("height", 1)))
            diagonal = math.sqrt(width * width + height * height)

            prev_cx, prev_cy, prev_area = PerceptionEvaluator._box_center_area(prev_box)
            curr_cx, curr_cy, curr_area = PerceptionEvaluator._box_center_area(curr_box)
            center_shift = math.sqrt((curr_cx - prev_cx) ** 2 + (curr_cy - prev_cy) ** 2) / diagonal
            area_shift = abs(math.log((curr_area + 1.0) / (prev_area + 1.0)))
            jitter_values.append(min(1.0, center_shift * 6.0 + area_shift * 0.35))

        if not jitter_values:
            return 0.5, 0.5
        jitter = float(np.mean(jitter_values))
        stability = 1.0 - _clamp(jitter / 0.35)
        return stability, jitter

    @staticmethod
    def _box_center_area(box):
        x1, y1, x2, y2 = box
        width = max(0.0, x2 - x1)
        height = max(0.0, y2 - y1)
        return x1 + width / 2.0, y1 + height / 2.0, width * height

    @staticmethod
    def _compute_occlusion_recovery(track_items, total_frames):
        if not track_items or total_frames <= 0:
            return 0.0
        present = {item["frame_index"] for item in track_items}
        first = min(present)
        last = max(present)
        if last <= first:
            return 1.0
        internal_span = list(range(first, last + 1))
        missing = sum(1 for frame_index in internal_span if frame_index not in present)
        return 1.0 - _clamp(missing / max(1, len(internal_span)))

    @staticmethod
    def _compute_class_consistency(primary_detections):
        if not primary_detections:
            return 0.0
        classes = [det.get("class_id") for det in primary_detections]
        counts = Counter(classes)
        return max(counts.values()) / max(1, len(classes))

    @staticmethod
    def _build_feedback(metrics, threshold, score):
        failure_reasons = []
        suggestions = []

        if metrics["frames_with_detection"] == 0:
            return (
                ["No target-like traffic participant was detected in the rendered video."],
                [
                    "Make the requested traffic participant visible, larger, and less occluded while preserving the original request."
                ],
            )

        if metrics["detection_coverage"] < 0.75:
            failure_reasons.append(
                "The target-like object is not detected in enough frames."
            )
            suggestions.append(
                "Keep the requested object visible for more of the video and avoid long occlusions."
            )
        if metrics["mean_confidence"] < 0.55:
            failure_reasons.append("Detection confidence is low.")
            suggestions.append(
                "Improve visual clarity by making the object less blurred, better lit, and more recognizable."
            )
        if metrics["dominant_track_coverage"] < 0.65:
            failure_reasons.append("The main track is too fragmented.")
            suggestions.append(
                "Use smoother object motion and avoid swapping the target with visually similar objects."
            )
        if metrics["id_consistency"] < 0.75:
            failure_reasons.append("The tracker changes IDs too often.")
            suggestions.append(
                "Reduce abrupt target motion, heavy occlusion, and crowding near the requested object."
            )
        if metrics["bbox_stability"] < 0.55:
            failure_reasons.append("The tracked bounding box is unstable.")
            suggestions.append(
                "Reduce motion blur and sudden scale changes while keeping the original scenario."
            )
        if score < threshold and not failure_reasons:
            failure_reasons.append("The weighted perception score is below the target threshold.")
            suggestions.append(
                "Clarify the requested object position, visibility, and motion without changing the user's intent."
            )

        return failure_reasons, suggestions
