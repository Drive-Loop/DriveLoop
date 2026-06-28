from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


DEFAULT_PROMPT = "daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video."
DEFAULT_SCENARIO_ID = "motorcycle_refined_candidate_gpu_smoke"
DEFAULT_OUTPUT_DIR = Path("outputs/driveloop/motorcycle_refined_candidate_gpu_smoke")
DEFAULT_READINESS_OUTPUT = Path("outputs/driveloop/gpu_smoke_readiness/motorcycle_refined_candidate_gate.json")
DEFAULT_POST_GATE_DIR = Path("outputs/driveloop/post_gpu_review_gate/motorcycle_refined_candidate_gpu_smoke")
DEFAULT_ALIGNMENT_EVAL_DIR = Path("outputs/driveloop/prompt_video_alignment_eval")
DEFAULT_CONFIG_NAME = "drivedreamer2_img_cond_mini_local"


def shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def expected_video_path(output_dir: Path, scenario_id: str) -> Path:
    return output_dir / "artifacts" / scenario_id / "iteration_00.mp4"


def build_command_plan(
    prompt: str = DEFAULT_PROMPT,
    scenario_id: str = DEFAULT_SCENARIO_ID,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    readiness_output: Path = DEFAULT_READINESS_OUTPUT,
    post_gate_dir: Path = DEFAULT_POST_GATE_DIR,
    alignment_eval_dir: Path = DEFAULT_ALIGNMENT_EVAL_DIR,
    config_name: str = DEFAULT_CONFIG_NAME,
    max_iterations: int = 1,
    target_score: float = 0.9,
    manual_report_path: Path | None = None,
) -> dict[str, Any]:
    video_path = expected_video_path(output_dir, scenario_id)
    review_report = manual_report_path or post_gate_dir / "manual_review_pack" / "manual_alignment_report.json"

    readiness_command = shell_command(
        [
            "python",
            "scripts/run_gpu_smoke_readiness_gate.py",
            "--prompt",
            prompt,
            "--scenario-id",
            scenario_id,
            "--output",
            str(readiness_output),
        ]
    )
    gpu_smoke_command = shell_command(
        [
            "python",
            "scripts/run_driveloop_drivedreamer2.py",
            "--prompt",
            prompt,
            "--scenario-id",
            scenario_id,
            "--max-iterations",
            str(max_iterations),
            "--target-score",
            str(target_score),
            "--output-dir",
            str(output_dir),
            "--config-name",
            config_name,
        ]
    )
    post_gpu_review_gate_command = shell_command(
        [
            "python",
            "scripts/run_post_gpu_review_gate.py",
            "--prompt",
            prompt,
            "--scenario-id",
            scenario_id,
            "--video-path",
            str(video_path),
            "--output-dir",
            str(post_gate_dir),
        ]
    )
    alignment_eval_command_template = shell_command(
        [
            "python",
            "scripts/run_prompt_video_alignment_eval.py",
            "--prompt",
            prompt,
            "--scenario-id",
            f"{scenario_id}_manual_review",
            "--video-path",
            str(video_path),
            "--alignment-report",
            str(review_report),
            "--output-dir",
            str(alignment_eval_dir),
        ]
    )

    return {
        "schema_version": "driveloop_single_gpu_smoke_command_plan.v0",
        "does_not_run_gpu": True,
        "scenario_id": scenario_id,
        "prompt": prompt,
        "expected_video_path": str(video_path),
        "commands": {
            "readiness_gate": readiness_command,
            "gpu_smoke_candidate_generation": gpu_smoke_command,
            "post_gpu_review_gate": post_gpu_review_gate_command,
            "alignment_eval_after_completed_review": alignment_eval_command_template,
        },
        "execution_order": [
            "readiness_gate",
            "gpu_smoke_candidate_generation",
            "post_gpu_review_gate",
            "alignment_eval_after_completed_review",
        ],
        "claim_boundary": {
            "gpu_smoke_generates": "candidate_video_only",
            "semantic_claim_allowed_after_gpu": False,
            "lane_change_control_claim_allowed": False,
            "required_before_semantic_claim": "explicit manual/perception/VLM review report followed by prompt-video alignment evaluation",
        },
        "notes": [
            "Run gpu_smoke_candidate_generation only if the readiness gate reports gpu_smoke_allowed true.",
            "The generated video remains not_measured until an explicit review report is attached.",
            "Runtime tensor/hash changes do not prove video semantics or lane-change motion.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate audited commands for a single DD2 GPU smoke candidate.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--scenario-id", default=DEFAULT_SCENARIO_ID)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--readiness-output", type=Path, default=DEFAULT_READINESS_OUTPUT)
    parser.add_argument("--post-gate-dir", type=Path, default=DEFAULT_POST_GATE_DIR)
    parser.add_argument("--alignment-eval-dir", type=Path, default=DEFAULT_ALIGNMENT_EVAL_DIR)
    parser.add_argument("--config-name", default=DEFAULT_CONFIG_NAME)
    parser.add_argument("--max-iterations", type=int, default=1)
    parser.add_argument("--target-score", type=float, default=0.9)
    parser.add_argument("--manual-report-path", type=Path, default=None)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    plan = build_command_plan(
        prompt=args.prompt,
        scenario_id=args.scenario_id,
        output_dir=args.output_dir,
        readiness_output=args.readiness_output,
        post_gate_dir=args.post_gate_dir,
        alignment_eval_dir=args.alignment_eval_dir,
        config_name=args.config_name,
        max_iterations=args.max_iterations,
        target_score=args.target_score,
        manual_report_path=args.manual_report_path,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(args.output)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
