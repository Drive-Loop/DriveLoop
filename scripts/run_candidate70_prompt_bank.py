from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_PROMPT_BANK_OUTPUT = Path("outputs/driveloop/prompt_bank/candidate70_prompt_bank_v0.json")
DEFAULT_SUPPORT_AUDIT_OUTPUT = Path("outputs/driveloop/prompt_bank/candidate70_prompt_bank_support_audit_v0.json")


def build_candidate70_prompt_bank() -> dict[str, Any]:
    candidate = {
        "candidate": "candidate70",
        "candidate_id": "nuscenes_train_candidate70_cam_front_9935",
        "scene": "scene-1100",
        "map": "singapore-hollandvillage",
        "target_raw_instance_token": "21cdc9f24c614a6197fd044379697197",
        "category": "vehicle.motorcycle",
        "supported_tags": [
            "motorcycle",
            "scooter",
            "night",
            "dark",
            "urban",
            "street",
            "intersection",
            "lane_change",
            "cut_in",
        ],
    }
    prompts = [
        {
            "id": "c70_pos_001",
            "split": "candidate70_positive",
            "support_expectation": "candidate_supported",
            "prompt": "night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.",
            "tags": ["motorcycle", "night", "urban", "cut_in", "left", "ego_vehicle"],
            "accepted_for_generate": False,
        },
        {
            "id": "c70_pos_002",
            "split": "candidate70_positive",
            "support_expectation": "candidate_supported",
            "prompt": "dark city intersection with a scooter changing lane from the left into the ego vehicle's path, panoramic multi-view video.",
            "tags": ["scooter", "night", "intersection", "lane_change", "left", "ego_vehicle"],
            "accepted_for_generate": False,
        },
        {
            "id": "c70_pos_003",
            "split": "candidate70_positive",
            "support_expectation": "candidate_supported",
            "prompt": "nighttime urban road where a motorcycle or scooter performs a left-side lane-change or cut-in near the ego vehicle, panoramic multi-view video.",
            "tags": ["motorcycle", "scooter", "night", "urban", "lane_change", "cut_in"],
            "accepted_for_generate": False,
        },
        {
            "id": "c70_neighbor_001",
            "split": "near_neighbor",
            "support_expectation": "partially_supported_or_requires_new_candidate",
            "prompt": "night urban street with a bicycle cutting in from the left toward the ego vehicle, panoramic multi-view video.",
            "tags": ["bicycle", "night", "urban", "cut_in", "left"],
            "accepted_for_generate": False,
        },
        {
            "id": "c70_neighbor_002",
            "split": "near_neighbor",
            "support_expectation": "partially_supported_or_requires_new_candidate",
            "prompt": "night urban street with a car changing lane from the left in front of the ego vehicle, panoramic multi-view video.",
            "tags": ["car", "night", "urban", "lane_change", "left"],
            "accepted_for_generate": False,
        },
        {
            "id": "c70_neg_001",
            "split": "negative_control",
            "support_expectation": "blocked_for_candidate70",
            "prompt": "daytime urban road with a motorcycle performing a visible lane change from the left, panoramic multi-view video.",
            "tags": ["motorcycle", "daytime", "urban", "lane_change"],
            "accepted_for_generate": False,
        },
        {
            "id": "c70_neg_002",
            "split": "negative_control",
            "support_expectation": "blocked_for_candidate70",
            "prompt": "night urban street with no motorcycle or scooter, only parked cars beside the ego vehicle, panoramic multi-view video.",
            "tags": ["night", "urban", "no_motorcycle", "parked_cars"],
            "accepted_for_generate": False,
        },
        {
            "id": "c70_holdout_001",
            "split": "evaluation_holdout",
            "support_expectation": "candidate_supported_but_holdout",
            "prompt": "dark urban intersection where a two-wheeled vehicle moves from the left lane toward the ego vehicle's lane, panoramic multi-view video.",
            "tags": ["two_wheeled_vehicle", "night", "urban", "intersection", "lane_change", "left"],
            "accepted_for_generate": False,
        },
    ]
    return {
        "schema_version": "driveloop_prompt_bank.v0",
        "purpose": "non_gpu_prompt_bank_for_candidate70_training_and_experiment_design",
        "does_not_run_gpu": True,
        "does_not_generate_video": True,
        "does_not_modify_business_logic": True,
        "candidate": candidate,
        "prompt_policy": {
            "raw_prompt_preserved": True,
            "suggested_prompts_are_not_accepted_prompts": True,
            "accepted_prompt_required_before_generate": True,
            "randomization_policy": "controlled_stratified_prompt_sampling",
            "semantic_success_claim_allowed": False,
        },
        "prompts": prompts,
        "claim_boundary": {
            "prompt_bank_is_not_candidate_selection_success": True,
            "prompt_bank_is_not_runtime_motion_control": True,
            "prompt_bank_is_not_video_semantic_success": True,
            "gpu_requires_separate_readiness_gate_and_user_approval": True,
        },
    }


def audit_prompt_bank(bank: dict[str, Any]) -> dict[str, Any]:
    results = []
    for item in bank["prompts"]:
        tags = set(item["tags"])
        blocked_reasons = []
        if "daytime" in tags:
            blocked_reasons.append("candidate70_is_night_not_daytime")
        if "no_motorcycle" in tags:
            blocked_reasons.append("prompt_requests_no_motorcycle_or_scooter")
        if "bicycle" in tags:
            blocked_reasons.append("candidate70_target_is_motorcycle_not_bicycle")
        if "car" in tags:
            blocked_reasons.append("candidate70_target_is_motorcycle_not_car")

        allowed = not blocked_reasons and item["split"] in {"candidate70_positive", "evaluation_holdout"}
        results.append({
            "id": item["id"],
            "split": item["split"],
            "support_expectation": item["support_expectation"],
            "allowed_for_candidate70": allowed,
            "blocked_reasons": blocked_reasons,
            "tags": item["tags"],
            "prompt": item["prompt"],
            "accepted_for_generate": item["accepted_for_generate"],
        })

    return {
        "schema_version": "driveloop_prompt_bank_candidate_support_audit.v0",
        "does_not_run_gpu": True,
        "does_not_generate_video": True,
        "accepted_for_generate_count": sum(1 for r in results if r["accepted_for_generate"]),
        "candidate70_allowed_count": sum(1 for r in results if r["allowed_for_candidate70"]),
        "candidate70_blocked_count": sum(1 for r in results if not r["allowed_for_candidate70"]),
        "results": results,
        "claim_boundary": {
            "prompt_bank_audit_is_not_video_semantic_success": True,
            "candidate_support_is_not_runtime_motion_control": True,
            "accepted_prompt_required_before_generate": True,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_outputs(prompt_bank_output: Path, support_audit_output: Path) -> dict[str, Any]:
    bank = build_candidate70_prompt_bank()
    audit = audit_prompt_bank(bank)
    audit["bank_path"] = str(prompt_bank_output)
    write_json(prompt_bank_output, bank)
    write_json(support_audit_output, audit)
    return {
        "prompt_bank_output": str(prompt_bank_output),
        "support_audit_output": str(support_audit_output),
        "prompt_count": len(bank["prompts"]),
        "candidate70_allowed_count": audit["candidate70_allowed_count"],
        "candidate70_blocked_count": audit["candidate70_blocked_count"],
        "accepted_for_generate_count": audit["accepted_for_generate_count"],
        "does_not_run_gpu": bank["does_not_run_gpu"],
        "semantic_success_claim_allowed": bank["prompt_policy"]["semantic_success_claim_allowed"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and audit the candidate70 non-GPU prompt bank.")
    parser.add_argument("--prompt-bank-output", type=Path, default=DEFAULT_PROMPT_BANK_OUTPUT)
    parser.add_argument("--support-audit-output", type=Path, default=DEFAULT_SUPPORT_AUDIT_OUTPUT)
    args = parser.parse_args()

    summary = write_outputs(
        prompt_bank_output=args.prompt_bank_output,
        support_audit_output=args.support_audit_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
