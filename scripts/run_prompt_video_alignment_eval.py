from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Dict

from driveloop.evaluators import PromptVideoAlignmentEvaluator
from driveloop.schema import Generation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate prompt-video alignment from an external report.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--scenario-id", default="prompt_video_alignment_eval")
    parser.add_argument("--video-path", default=None)
    parser.add_argument("--alignment-report", default=None)
    parser.add_argument("--output-dir", default="outputs/driveloop/prompt_video_alignment_eval")
    parser.add_argument("--pass-threshold", type=float, default=0.8)
    return parser.parse_args()


def load_alignment_report(path: str | None) -> Dict[str, Any] | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("alignment report must be a JSON object")
    for key in ("prompt_video_alignment", "video_alignment_report", "perception_alignment"):
        value = data.get(key)
        if isinstance(value, dict):
            return value
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
        "alignment_evaluator": "PromptVideoAlignmentEvaluator",
        "alignment_evaluator_mode": "external_report_only",
    }
    report = load_alignment_report(args.alignment_report)
    if report is not None:
        metadata["prompt_video_alignment"] = report

    return Generation(iteration=0, prompt=args.prompt, artifacts=artifacts, metadata=metadata)


def evaluate_generation(generation: Generation, pass_threshold: float) -> Dict[str, Any]:
    evaluation = PromptVideoAlignmentEvaluator(pass_threshold=pass_threshold).evaluate(generation)
    measured = evaluation.metrics.get("alignment_measured") == 1.0
    if not measured:
        video_semantic_claim = "not_measured"
    elif evaluation.diagnosis.passed:
        video_semantic_claim = "measured_passed"
    else:
        video_semantic_claim = "measured_failed"

    return {
        "generation": asdict(generation),
        "evaluation": asdict(evaluation),
        "interpretation": {
            "tensor_audit_claim": "not_evaluated_by_this_script",
            "video_semantic_claim": video_semantic_claim,
            "claim_boundary": (
                "This script does not inspect video pixels. It only scores an explicit "
                "perception, VLM, or human-review report attached to generation metadata."
            ),
        },
    }


def main() -> None:
    args = parse_args()
    payload = evaluate_generation(build_generation(args), args.pass_threshold)
    output_dir = Path(args.output_dir) / args.scenario_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "prompt_video_alignment_evaluation.json"
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote prompt-video alignment evaluation: {output_path}")


if __name__ == "__main__":
    main()
