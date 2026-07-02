#!/usr/bin/env python3
"""Build a non-GPU readiness gate for candidate70 source-sample binding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_IDENTITY_SUMMARY = Path(
    "outputs/driveloop/candidate70_converter_identity_probe/cam_front_8/v0.0.1/labels/summary.json"
)
DEFAULT_FAILED_ALIGNMENT = Path(
    "outputs/driveloop/prompt_video_alignment_eval/"
    "candidate70_night_cut_in_gpu_smoke_manual_review/"
    "prompt_video_alignment_evaluation.json"
)
DEFAULT_RUNNER = Path("scripts/run_driveloop_drivedreamer2.py")
DEFAULT_BACKEND = Path("driveloop/backends/drivedreamer2.py")
DEFAULT_OUTPUT = Path(
    "outputs/driveloop/source_sample_binding_readiness/"
    "candidate70_source_sample_binding_readiness.json"
)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def has_runtime_sample_selector(text: str) -> bool:
    selector_terms = [
        "--source-candidate-id",
        "--scene-token",
        "--sample-token",
        "--instance-token",
        "DRIVELOOP_DD2_SAMPLE_TOKEN",
        "DRIVELOOP_DD2_SCENE_TOKEN",
        "source_candidate_id",
        "sample_token_selector",
        "scene_token_selector",
    ]
    return any(term in text for term in selector_terms)


def build_gate(
    identity_summary_path: Path = DEFAULT_IDENTITY_SUMMARY,
    failed_alignment_path: Path = DEFAULT_FAILED_ALIGNMENT,
    runner_path: Path = DEFAULT_RUNNER,
    backend_path: Path = DEFAULT_BACKEND,
) -> Dict[str, Any]:
    identity = load_json(identity_summary_path)
    failed_alignment = load_json(failed_alignment_path)
    runner_text = read_text(runner_path)
    backend_text = read_text(backend_path)

    frames = identity.get("frame_summaries", [])
    sample_tokens = [
        frame.get("sample_token")
        for frame in frames
        if isinstance(frame, dict) and frame.get("sample_token")
    ]
    cam_tokens = [
        frame.get("cam_token")
        for frame in frames
        if isinstance(frame, dict) and frame.get("cam_token")
    ]

    runner_has_selector = has_runtime_sample_selector(runner_text)
    backend_has_selector = has_runtime_sample_selector(backend_text)

    checks = {
        "identity_summary_exists": identity_summary_path.exists(),
        "candidate_is_candidate70": identity.get("candidate") == "candidate70",
        "converter_identity_subset_created": identity.get("claim", {}).get(
            "candidate70_converter_derived_identity_subset_created"
        )
        is True,
        "all_frames_have_target": identity.get("all_frames_have_target") is True,
        "all_frames_have_instance_tokens": identity.get("all_frames_have_instance_tokens") is True,
        "all_frames_have_sample_annotation_tokens": identity.get(
            "all_frames_have_sample_annotation_tokens"
        )
        is True,
        "sample_tokens_available": len(sample_tokens) == identity.get("frame_count"),
        "target_raw_instance_token_available": bool(identity.get("target_raw_instance_token")),
        "runner_has_runtime_sample_selector": runner_has_selector,
        "backend_has_runtime_sample_selector": backend_has_selector,
        "failed_alignment_is_measured_failed": failed_alignment.get("interpretation", {}).get(
            "video_semantic_claim"
        )
        == "measured_failed",
    }

    blockers: List[str] = []
    if not checks["identity_summary_exists"]:
        blockers.append("candidate70_identity_summary_missing")
    if not checks["sample_tokens_available"]:
        blockers.append("candidate70_sample_tokens_missing_or_incomplete")
    if not checks["runner_has_runtime_sample_selector"]:
        blockers.append("runner_has_no_candidate70_source_sample_selector")
    if not checks["backend_has_runtime_sample_selector"]:
        blockers.append("backend_has_no_verified_runtime_sample_selector")
    if not (checks["runner_has_runtime_sample_selector"] and checks["backend_has_runtime_sample_selector"]):
        blockers.append("blocked_no_verified_runtime_sample_selector")

    readiness_status = "ready" if not blockers else "blocked_no_verified_runtime_sample_selector"

    return {
        "schema_version": "driveloop_candidate70_source_sample_binding_readiness.v0",
        "candidate": "candidate70",
        "readiness_status": readiness_status,
        "gpu_smoke_allowed": False,
        "does_not_run_gpu": True,
        "does_not_generate_video": True,
        "checks": checks,
        "blockers": blockers,
        "candidate70_source_evidence": {
            "source": identity.get("source"),
            "raw_root": identity.get("raw_root"),
            "output_label_path": identity.get("output_label_path"),
            "target_raw_instance_token": identity.get("target_raw_instance_token"),
            "frame_count": identity.get("frame_count"),
            "first_sample_token": sample_tokens[0] if sample_tokens else None,
            "last_sample_token": sample_tokens[-1] if sample_tokens else None,
            "unique_sample_token_count": len(set(sample_tokens)),
            "unique_cam_token_count": len(set(cam_tokens)),
        },
        "runtime_binding_assessment": {
            "runner_path": str(runner_path),
            "backend_path": str(backend_path),
            "runtime_sample_selector_verified": runner_has_selector and backend_has_selector,
            "current_failure_interpretation": (
                "candidate70 source evidence exists upstream, but no verified DD2 runtime "
                "selector was observed for candidate/source/sample tokens."
            ),
        },
        "claim_boundary": {
            "source_sample_binding_gate_is_not_gpu_approval": True,
            "converter_identity_subset_is_not_runtime_binding": True,
            "sample_tokens_available_is_not_video_semantic_success": True,
            "measured_failed_video_is_not_semantic_success": True,
            "semantic_success_claim_allowed": False,
        },
        "next_required_steps": [
            "add or verify a DD2 runtime sample selector before another GPU run",
            "prove candidate70 source sample is selected by runtime, not only converter/audit outputs",
            "keep GPU blocked until source-sample binding is readiness-gated",
        ],
        "sources": {
            "identity_summary": {"path": str(identity_summary_path), "exists": identity_summary_path.exists()},
            "failed_alignment": {"path": str(failed_alignment_path), "exists": failed_alignment_path.exists()},
            "runner": {"path": str(runner_path), "exists": runner_path.exists()},
            "backend": {"path": str(backend_path), "exists": backend_path.exists()},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build candidate70 source-sample binding readiness gate."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gate = build_gate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(gate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)
    print(json.dumps(gate, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
