from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from driveloop.perception_video import PerceptionVideoEvaluator, UltralyticsYOLODetector
from driveloop.schema import Generation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DriveLoop Eq.15 perception video evaluation.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--scenario-id", default="perception_video_eval")
    parser.add_argument("--video-path", default=None)
    parser.add_argument("--detections-json", default=None)
    parser.add_argument("--target-label", action="append", default=[])
    parser.add_argument("--yolo-weights", default=None)
    parser.add_argument("--output-dir", default="outputs/driveloop/perception_video_eval")
    parser.add_argument("--pass-threshold", type=float, default=0.8)
    parser.add_argument("--confidence-threshold", type=float, default=0.25)
    parser.add_argument("--max-frames", type=int, default=None)
    return parser.parse_args()


def load_detection_payload(path: str | None) -> Dict[str, Any] | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("detections JSON must be an object")
    return data


def build_generation(args: argparse.Namespace) -> Generation:
    artifacts: Dict[str, str] = {}
    if args.video_path:
        video_path = Path(args.video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"video artifact does not exist: {video_path}")
        artifacts["video"] = str(video_path)

    metadata: Dict[str, Any] = {
        "scenario_id": args.scenario_id,
        "target_labels": list(args.target_label),
        "perception_evaluator": "PerceptionVideoEvaluator",
    }
    detections = load_detection_payload(args.detections_json)
    if detections is not None:
        metadata["perception_detections"] = detections

    return Generation(iteration=0, prompt=args.prompt, artifacts=artifacts, metadata=metadata)


def build_evaluator(args: argparse.Namespace) -> PerceptionVideoEvaluator:
    detector = None
    if args.yolo_weights:
        detector = UltralyticsYOLODetector(args.yolo_weights, confidence_threshold=args.confidence_threshold)
    return PerceptionVideoEvaluator(
        detector=detector,
        target_labels=args.target_label,
        confidence_threshold=args.confidence_threshold,
        pass_threshold=args.pass_threshold,
        max_frames=args.max_frames,
    )


def main() -> None:
    args = parse_args()
    generation = build_generation(args)
    report = build_evaluator(args).build_report(generation)
    output_dir = Path(args.output_dir) / args.scenario_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "perception_video_evaluation.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Wrote perception video evaluation: {output_path}")


if __name__ == "__main__":
    main()
