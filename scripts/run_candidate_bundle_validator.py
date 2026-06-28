from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("outputs/driveloop/candidate_artifact_manifest/motorcycle_refined_candidate_manifest.json")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _artifact_exists(artifacts: dict[str, Any], name: str) -> bool:
    item = artifacts.get(name, {})
    return bool(item.get("exists")) if isinstance(item, dict) else False


def validate_bundle(manifest: dict[str, Any]) -> dict[str, Any]:
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, dict):
        artifacts = {}

    video_exists = _artifact_exists(artifacts, "video")
    runtime_audit_exists = _artifact_exists(artifacts, "runtime_audit")
    post_gpu_gate_exists = _artifact_exists(artifacts, "post_gpu_gate")
    manual_review_exists = _artifact_exists(artifacts, "manual_review_report")
    alignment_eval_exists = _artifact_exists(artifacts, "alignment_eval")

    missing_for_review_ready = [
        name
        for name, exists in {
            "video": video_exists,
            "post_gpu_gate": post_gpu_gate_exists,
            "manual_review_report": manual_review_exists,
        }.items()
        if not exists
    ]
    missing_for_measured_ready = [
        name
        for name, exists in {
            "video": video_exists,
            "runtime_audit": runtime_audit_exists,
            "post_gpu_gate": post_gpu_gate_exists,
            "manual_review_report": manual_review_exists,
            "alignment_eval": alignment_eval_exists,
        }.items()
        if not exists
    ]

    if not video_exists:
        status = "blocked"
        reason = "candidate video is missing"
    elif missing_for_review_ready:
        status = "blocked"
        reason = "post-GPU review bundle is incomplete"
    elif missing_for_measured_ready:
        status = "review_ready"
        reason = "candidate can be reviewed, but measured alignment evaluation is incomplete"
    else:
        status = "measured_ready"
        reason = "all required artifacts are present for a measured semantic claim review"

    return {
        "schema_version": "driveloop_candidate_bundle_validation.v0",
        "scenario_id": manifest.get("scenario_id"),
        "candidate_status": manifest.get("candidate_status"),
        "input_video_semantic_claim": manifest.get("video_semantic_claim"),
        "bundle_status": status,
        "status_reason": reason,
        "semantic_success_claim_allowed": False,
        "claim_boundary": {
            "bundle_status_is_not_pass_fail": True,
            "measured_ready_requires_reading_alignment_eval_result": True,
            "semantic_success_requires_measured_passed_result": True,
        },
        "checks": {
            "video_exists": video_exists,
            "runtime_audit_exists": runtime_audit_exists,
            "post_gpu_gate_exists": post_gpu_gate_exists,
            "manual_review_report_exists": manual_review_exists,
            "alignment_eval_exists": alignment_eval_exists,
        },
        "missing_for_review_ready": missing_for_review_ready,
        "missing_for_measured_ready": missing_for_measured_ready,
        "next_required_steps": next_steps(status, missing_for_review_ready, missing_for_measured_ready),
    }


def next_steps(status: str, missing_review: list[str], missing_measured: list[str]) -> list[str]:
    if status == "blocked":
        if "video" in missing_review:
            return [
                "run gated candidate GPU smoke if intentionally chosen",
                "regenerate candidate artifact manifest",
                "run this validator again",
            ]
        return [
            "run post-GPU review gate",
            "complete explicit manual/perception/VLM review report",
            "regenerate candidate artifact manifest",
            "run this validator again",
        ]

    if status == "review_ready":
        return [
            "run prompt-video alignment evaluation after completing review report",
            "preserve runtime audit metadata if missing",
            "regenerate candidate artifact manifest",
            "read the alignment evaluation result before any semantic claim",
        ]

    return [
        "inspect alignment evaluation result",
        "record measured_failed or measured_passed according to explicit evidence",
        "do not claim semantic success unless the measured result is measured_passed",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate whether a DriveLoop candidate artifact bundle is review-ready.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    validation = validate_bundle(manifest)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(args.output)
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
