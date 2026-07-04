from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from driveloop import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner
from driveloop.automatic_closed_loop_manifest import build_automatic_closed_loop_manifest
from driveloop.backends import MockGenerationBackend


def test_manifest_marks_real_runner_multiround_as_automatic():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = DriveLoopRunner(
            backend=MockGenerationBackend(output_dir=root / "artifacts"),
            config=DriveLoopConfig(max_iterations=3, target_score=0.8, output_dir=root / "history"),
        ).run(DriveLoopRequest(prompt="make a driving video"))

    manifest = build_automatic_closed_loop_manifest(result, target_score=0.8, source="unit_runner")

    assert manifest["automatic_loop_supported"] is True
    assert manifest["automatic_multiround_supported"] is True
    assert manifest["attempt_count"] >= 2
    assert manifest["complete_transition_count"] >= 1
    assert manifest["manual_review_dependency_detected"] is False
    assert manifest["audit_only_detected"] is False
    assert manifest["claim_boundary"]["manual_review_evidence_does_not_count_as_automatic_loop"] is True


def test_manifest_rejects_audit_only_case_summary_as_automatic_loop():
    case_summary = {
        "schema_version": "driveloop_closed_loop_case_summary.v0",
        "attempts": {
            "pre_refinement": {"video_semantic_claim": "measured_failed", "score": 0.3},
            "post_refinement_retry": {"video_semantic_claim": "measured_passed", "score": 0.9},
        },
        "evidence_chain": ["external_alignment_review", "post_retry_alignment_review"],
        "claim_boundary": {
            "summary_does_not_generate_video": True,
            "semantic_success_requires_measured_alignment_review": True,
        },
    }

    manifest = build_automatic_closed_loop_manifest(case_summary, target_score=0.8, source="case_summary")

    assert manifest["automatic_loop_supported"] is False
    assert manifest["automatic_multiround_supported"] is False
    assert "audit_only_trace_does_not_execute_generation" in manifest["blockers"]
    assert "manual_review_dependency_detected" in manifest["blockers"]


def test_manifest_accepts_history_jsonl_records_with_prompt_refinement(tmp_path: Path):
    records = [
        {
            "generation": {"iteration": 0, "prompt": "make a driving video", "artifacts": {}, "metadata": {}},
            "evaluation": {
                "score": 0.2,
                "metrics": {},
                "diagnosis": {"passed": False, "reasons": ["prompt_too_generic"], "suggested_actions": ["add realistic autonomous driving scene"]},
            },
        },
        {
            "generation": {"iteration": 1, "prompt": "realistic autonomous driving scene", "artifacts": {}, "metadata": {}},
            "evaluation": {
                "score": 0.9,
                "metrics": {},
                "diagnosis": {"passed": True, "reasons": [], "suggested_actions": []},
            },
        },
    ]
    path = tmp_path / "history.jsonl"
    path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
    output = tmp_path / "manifest.json"

    subprocess.run(
        [
            sys.executable,
            "scripts/run_automatic_closed_loop_manifest.py",
            "--history-jsonl",
            str(path),
            "--output-json",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "driveloop_automatic_closed_loop_manifest.v0"
    assert manifest["automatic_multiround_supported"] is True
    assert manifest["transitions"][0]["prompt_changed"] is True
