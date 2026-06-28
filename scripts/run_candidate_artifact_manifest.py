from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_PROMPT = "daytime urban road with a motorcycle, the motorcycle performs a visible lane change from the left, panoramic multi-view video."
DEFAULT_SCENARIO_ID = "motorcycle_refined_candidate_gpu_smoke"
DEFAULT_VIDEO_PATH = Path("outputs/driveloop/motorcycle_refined_candidate_gpu_smoke/artifacts/motorcycle_refined_candidate_gpu_smoke/iteration_00.mp4")
DEFAULT_READINESS_GATE = Path("outputs/driveloop/gpu_smoke_readiness/motorcycle_refined_candidate_gate.json")
DEFAULT_COMMAND_PLAN = Path("outputs/driveloop/gpu_smoke_command_plan/motorcycle_refined_candidate_plan.json")
DEFAULT_RUNBOOK = Path("outputs/driveloop/gpu_smoke_runbook/motorcycle_refined_candidate_runbook.md")
DEFAULT_POST_GPU_GATE = Path("outputs/driveloop/post_gpu_review_gate/motorcycle_refined_candidate_gpu_smoke/post_gpu_review_gate.json")
DEFAULT_MANUAL_REPORT = Path("outputs/driveloop/post_gpu_review_gate/motorcycle_refined_candidate_gpu_smoke/manual_review_pack/manual_alignment_report.json")
DEFAULT_ALIGNMENT_EVAL = Path("outputs/driveloop/prompt_video_alignment_eval/motorcycle_refined_candidate_gpu_smoke_manual_review.json")


def artifact_entry(path: Path, role: str, required_for_claim: bool = False) -> dict[str, Any]:
    return {
        "role": role,
        "path": str(path),
        "exists": path.exists(),
        "required_for_semantic_claim": required_for_claim,
    }


def build_manifest(
    prompt: str = DEFAULT_PROMPT,
    scenario_id: str = DEFAULT_SCENARIO_ID,
    video_path: Path = DEFAULT_VIDEO_PATH,
    readiness_gate: Path = DEFAULT_READINESS_GATE,
    command_plan: Path = DEFAULT_COMMAND_PLAN,
    runbook: Path = DEFAULT_RUNBOOK,
    post_gpu_gate: Path = DEFAULT_POST_GPU_GATE,
    manual_report: Path = DEFAULT_MANUAL_REPORT,
    alignment_eval: Path = DEFAULT_ALIGNMENT_EVAL,
    runtime_audit: Path | None = None,
) -> dict[str, Any]:
    artifacts = {
        "video": artifact_entry(video_path, "candidate_video", required_for_claim=True),
        "readiness_gate": artifact_entry(readiness_gate, "pre_gpu_gate"),
        "command_plan": artifact_entry(command_plan, "pre_gpu_command_plan"),
        "runbook": artifact_entry(runbook, "human_runbook"),
        "post_gpu_gate": artifact_entry(post_gpu_gate, "post_gpu_not_measured_gate", required_for_claim=True),
        "manual_review_report": artifact_entry(manual_report, "explicit_review_report", required_for_claim=True),
        "alignment_eval": artifact_entry(alignment_eval, "prompt_video_alignment_eval", required_for_claim=True),
    }

    if runtime_audit is not None:
        artifacts["runtime_audit"] = artifact_entry(runtime_audit, "dd2_runtime_input_audit", required_for_claim=True)

    required_claim_artifacts = [
        name for name, item in artifacts.items() if item["required_for_semantic_claim"]
    ]
    missing_required_claim_artifacts = [
        name for name in required_claim_artifacts if not artifacts[name]["exists"]
    ]

    semantic_claim_ready = not missing_required_claim_artifacts

    return {
        "schema_version": "driveloop_candidate_artifact_manifest.v0",
        "scenario_id": scenario_id,
        "prompt": prompt,
        "candidate_status": "candidate_video_only" if video_path.exists() else "candidate_not_generated",
        "video_semantic_claim": "not_measured",
        "semantic_claim_ready": semantic_claim_ready,
        "claim_boundary": {
            "video_exists_is_not_semantic_success": True,
            "tensor_audit_is_not_video_semantic_success": True,
            "measured_claim_requires_explicit_review": True,
            "allowed_without_review": "candidate_video_generated_only" if video_path.exists() else "no_video_generated",
        },
        "artifacts": artifacts,
        "missing_required_claim_artifacts": missing_required_claim_artifacts,
        "next_required_steps": [
            "generate candidate video if missing",
            "preserve DD2 runtime input audit metadata",
            "run post-GPU review gate",
            "complete explicit manual/perception/VLM review report",
            "run prompt-video alignment evaluation",
            "record measured_failed or measured_passed from explicit review evidence",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a manifest for one DriveLoop candidate video artifact bundle.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--scenario-id", default=DEFAULT_SCENARIO_ID)
    parser.add_argument("--video-path", type=Path, default=DEFAULT_VIDEO_PATH)
    parser.add_argument("--readiness-gate", type=Path, default=DEFAULT_READINESS_GATE)
    parser.add_argument("--command-plan", type=Path, default=DEFAULT_COMMAND_PLAN)
    parser.add_argument("--runbook", type=Path, default=DEFAULT_RUNBOOK)
    parser.add_argument("--post-gpu-gate", type=Path, default=DEFAULT_POST_GPU_GATE)
    parser.add_argument("--manual-report", type=Path, default=DEFAULT_MANUAL_REPORT)
    parser.add_argument("--alignment-eval", type=Path, default=DEFAULT_ALIGNMENT_EVAL)
    parser.add_argument("--runtime-audit", type=Path, default=None)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = build_manifest(
        prompt=args.prompt,
        scenario_id=args.scenario_id,
        video_path=args.video_path,
        readiness_gate=args.readiness_gate,
        command_plan=args.command_plan,
        runbook=args.runbook,
        post_gpu_gate=args.post_gpu_gate,
        manual_report=args.manual_report,
        alignment_eval=args.alignment_eval,
        runtime_audit=args.runtime_audit,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(args.output)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
