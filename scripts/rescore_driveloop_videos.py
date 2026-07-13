"""Offline rescoring harness for stored DriveLoop arm videos.

Rebuilds a Generation from each case's stored attempts.jsonl (first
attempt) and re-evaluates the stored video under a selected scorer
version, without touching the runtime pipeline:

  v9   - CompositePerceptionVideoEvaluator (protocol reproduction;
         compare `score` against `stored_S_perc`)
  v10a - SuperclassCompositePerceptionEvaluator (candidate protocol)

Arms are passed as repeatable --arm tag=run_dir=baseline_video. The
baseline video must exist (fail fast, mirroring the runtime guard).
Scores are S_perc-level; J recomposition is out of scope for v10a.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_first_attempt(run_dir: Path, case: str) -> dict:
    path = run_dir / case / "attempts.jsonl"
    return json.loads(path.read_text(encoding="utf-8").strip().splitlines()[0])


def build_generation(record: dict):
    from driveloop.schema import Generation

    payload = record.get("generation", {})
    return Generation(
        iteration=int(payload.get("iteration", 0)),
        prompt=str(payload.get("prompt", "")),
        artifacts=dict(payload.get("artifacts", {})),
        metadata=dict(payload.get("metadata", {})),
    )


def build_evaluator(scorer: str, weights: str, confidence: float, baseline_video: str):
    from driveloop.perception_video import UltralyticsYOLODetector

    detector = UltralyticsYOLODetector(weights, confidence_threshold=confidence)
    if scorer == "v9":
        from driveloop.composite_perception import CompositePerceptionVideoEvaluator

        cls = CompositePerceptionVideoEvaluator
    else:
        from driveloop.perception_v10 import SuperclassCompositePerceptionEvaluator

        cls = SuperclassCompositePerceptionEvaluator
    return cls(detector=detector, confidence_threshold=confidence, baseline_video=baseline_video)


REPORT_KEYS = (
    "perception_target_support_frames",
    "perception_dominant_track_length",
    "perception_selected_view",
    "perception_baseline_available",
    "perception_class_fidelity",
    "perception_superclass_detection_count",
    "perception_original_class_detection_count",
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Rescore stored DriveLoop videos offline.")
    parser.add_argument(
        "--arm", action="append", required=True,
        help="tag=run_dir=baseline_video (repeatable)",
    )
    parser.add_argument("--cases", nargs="+", required=True)
    parser.add_argument("--scorer", choices=["v9", "v10a"], default="v9")
    parser.add_argument("--weights", default="yolov8x.pt")
    parser.add_argument("--confidence", type=float, default=0.20)
    parser.add_argument("--output-jsonl", default=None)
    args = parser.parse_args(argv)

    rows = []
    for arm_spec in args.arm:
        tag, run_dir, baseline_video = arm_spec.split("=", 2)
        if not Path(baseline_video).exists():
            parser.error("baseline video does not exist: %s" % baseline_video)
        evaluator = build_evaluator(args.scorer, args.weights, args.confidence, baseline_video)
        for case in args.cases:
            record = load_first_attempt(Path(run_dir), case)
            generation = build_generation(record)
            evaluation = evaluator.evaluate(generation)
            stored = record.get("evaluation", {}).get("metrics", {})
            row = {
                "tag": tag,
                "case": case,
                "scorer": args.scorer,
                "score": round(float(evaluation.score), 6),
                "stored_S_perc": stored.get("S_perc"),
            }
            for key in REPORT_KEYS:
                if key in evaluation.metrics:
                    row[key] = evaluation.metrics[key]
            rows.append(row)
            print(json.dumps(row, sort_keys=True))
    if args.output_jsonl:
        Path(args.output_jsonl).write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
