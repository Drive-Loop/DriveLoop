from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def first_dict(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def first_list(*values: Any) -> list[Any]:
    for value in values:
        if isinstance(value, list):
            return value
    return []


def nested(data: dict[str, Any], *keys: str) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def infer_paper_report_path(summary_path: Path) -> Path | None:
    candidate = summary_path.parent / "paper_alignment_report_00.json"
    return candidate if candidate.exists() else None


def runtime_hashes(runtime: dict[str, Any]) -> dict[str, Any]:
    return {
        name: nested(runtime, name, "sha256")
        for name in [
            "prompt_embed",
            "box_downsampler_input",
            "grounding_downsampler_input",
            "img_cond",
        ]
    }


def build_motion_control_gap_report(
    summary_path: Path,
    paper_alignment_report_path: Path | None = None,
) -> dict[str, Any]:
    data = load_json(summary_path)
    metadata = first_dict(data.get("metadata"))

    paper_path = paper_alignment_report_path or infer_paper_report_path(summary_path)
    paper = load_json(paper_path) if paper_path and paper_path.exists() else {}
    stage3 = first_dict(paper.get("stage_3_scene_consistent_generation"))

    exec_cond = first_dict(
        nested(data, "metadata", "dd2_executable_condition"),
        data.get("dd2_executable_condition"),
        data.get("executable_condition"),
    )
    trace = first_dict(exec_cond.get("trace_metadata"))
    structural_plan = first_dict(
        exec_cond.get("structural_input_plan"),
        data.get("dd2_structural_input_plan"),
        metadata.get("dd2_structural_input_plan"),
        stage3.get("structural_input_plan"),
    )
    runtime = first_dict(
        data.get("runtime_input_audit"),
        nested(data, "metadata", "dd2_runtime_input_audit"),
    )
    override = first_dict(
        data.get("override_audit"),
        nested(data, "metadata", "dd2_override_audit"),
    )

    changed_counts = first_dict(override.get("changed_counts"))
    motion_controls = first_list(
        exec_cond.get("motion_controls"),
        nested(data, "audit_summary", "motion_controls"),
    )

    image_hdmap = first_dict(structural_plan.get("image_hdmap"))
    image_box = first_dict(structural_plan.get("image_box"))

    return {
        "schema_version": "driveloop_motion_control_gap_audit.v0",
        "source_summary": str(summary_path),
        "source_paper_alignment_report": str(paper_path) if paper_path else None,
        "scenario_id": data.get("scenario_id") or metadata.get("scenario_id"),
        "prompt": data.get("prompt") or metadata.get("prompt"),
        "claim": {
            "lane_change_motion_tensor_control": "not_verified",
            "video_semantic_claim": "not_evaluated_by_this_audit",
            "tensor_audit_scope": "runtime_inputs_only",
        },
        "observed_signals": {
            "motion_controls": motion_controls,
            "alignment_feedback": trace.get("alignment_feedback"),
            "prompt_override": runtime.get("prompt_override"),
            "runtime_hashes": runtime_hashes(runtime),
            "override_changed_counts": changed_counts,
        },
        "control_path_status": {
            "text_prompt": "connected" if runtime.get("prompt_override") else "not_observed",
            "scene_description": "connected" if changed_counts.get("scene_description") else "not_observed",
            "boxes3d_static_actor": (
                "connected_as_static_draft_box" if changed_counts.get("boxes3d") else "not_observed"
            ),
            "image_box": image_box.get("source", "unknown"),
            "image_hdmap": image_hdmap.get("source", "unknown"),
            "trajectory_tensor": "not_implemented",
            "temporal_actor_motion": "not_implemented",
        },
        "limitations": [
            "motion_controls are metadata/trace, not verified DD2 trajectory tensors",
            "static boxes3d actor placement does not prove lane-change temporal motion",
            "runtime tensor hash changes do not prove video semantic alignment",
            "manual or perception review is required for any generated video semantic claim",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--paper-alignment-report", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    report = build_motion_control_gap_report(
        summary_path=args.summary,
        paper_alignment_report_path=args.paper_alignment_report,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
