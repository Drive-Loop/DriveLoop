"""Run composite-layout perception evaluation on a DD2 debug video."""
import argparse
import json
from pathlib import Path

from driveloop.composite_perception import CompositePerceptionVideoEvaluator, CompositeVideoLayout
from driveloop.perception_video import UltralyticsYOLODetector
from driveloop.schema import Generation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--prompt", default="a motorcycle cut-in at night")
    parser.add_argument("--weights", default="yolov8m.pt")
    parser.add_argument("--confidence-threshold", type=float, default=0.25)
    parser.add_argument("--tracker", choices=["iou", "botsort"], default="iou")
    parser.add_argument("--out-root", default="outputs/driveloop/perception_video_eval")
    args = parser.parse_args()

    if args.tracker == "botsort":
        from driveloop.botsort_tracking import BotSortUltralyticsDetector
        detector = BotSortUltralyticsDetector(args.weights, confidence_threshold=args.confidence_threshold)
    else:
        detector = UltralyticsYOLODetector(args.weights, confidence_threshold=args.confidence_threshold)
    evaluator = CompositePerceptionVideoEvaluator(
        detector=detector,
        layout=CompositeVideoLayout(),
        confidence_threshold=args.confidence_threshold,
    )
    generation = Generation(iteration=0, prompt=args.prompt, artifacts={"video": args.video}, metadata={})
    report = evaluator.build_report(generation)
    report["scenario_id"] = args.scenario_id
    report["detector_weights"] = args.weights
    report["tracker"] = args.tracker

    out_dir = Path(args.out_root) / args.scenario_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "composite_perception_evaluation.json"
    out_path.write_text(json.dumps(report, indent=2))
    print("wrote", out_path)
    ev = report["evaluation"]
    print("score:", ev["score"], "| claim:", report["interpretation"]["perception_claim"])
    for key in sorted(ev["metrics"]):
        print("  %s: %s" % (key, ev["metrics"][key]))


if __name__ == "__main__":
    main()
