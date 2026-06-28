import json
from pathlib import Path

from scripts.run_gpu_smoke_readiness_gate import build_readiness_report


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_gpu_smoke_readiness_gate_allows_candidate_video_only(tmp_path: Path):
    runtime_compare = tmp_path / "runtime_compare.json"
    motion_gap = tmp_path / "motion_gap.json"
    velocity_surface = tmp_path / "velocity_surface.json"
    trajectory_contract = tmp_path / "trajectory_contract.md"
    config = tmp_path / "config.py"
    labels = tmp_path / "data.pkl"
    weights = tmp_path / "weights.bin"

    write_json(
        runtime_compare,
        {
            "runtime_tensor_hash_changed": {
                "prompt_embed": True,
                "box_downsampler_input": False,
                "grounding_downsampler_input": False,
                "img_cond": False,
            }
        },
    )
    write_json(motion_gap, {"claim": {"lane_change_motion_tensor_control": "not_verified"}})
    write_json(velocity_surface, {"claim": {"velocity_consumed_by_dd2_runtime": False}})
    trajectory_contract.write_text("contract", encoding="utf-8")
    config.write_text("config", encoding="utf-8")
    labels.write_bytes(b"labels")
    weights.write_bytes(b"weights")

    report = build_readiness_report(
        prompt="daytime urban road with a motorcycle",
        scenario_id="unit_gpu_gate",
        runtime_compare=runtime_compare,
        motion_gap=motion_gap,
        velocity_surface=velocity_surface,
        trajectory_contract_doc=trajectory_contract,
        config_path=config,
        labels_path=labels,
        weights_path=weights,
    )

    assert report["gpu_smoke_allowed"] is True
    assert report["semantic_claim_allowed"] is False
    assert report["allowed_claim_after_gpu"] == "candidate_video_generated_only"
    assert report["evidence_checks"]["runtime_boundary_ok"] is True
    assert "does not prove lane-change control" in report["claim_boundary"]


def test_gpu_smoke_readiness_gate_blocks_when_motion_gap_missing(tmp_path: Path):
    runtime_compare = tmp_path / "runtime_compare.json"
    velocity_surface = tmp_path / "velocity_surface.json"
    trajectory_contract = tmp_path / "trajectory_contract.md"
    config = tmp_path / "config.py"
    labels = tmp_path / "data.pkl"
    weights = tmp_path / "weights.bin"

    write_json(
        runtime_compare,
        {
            "runtime_tensor_hash_changed": {
                "prompt_embed": True,
                "box_downsampler_input": False,
                "grounding_downsampler_input": False,
                "img_cond": False,
            }
        },
    )
    write_json(velocity_surface, {"claim": {"velocity_consumed_by_dd2_runtime": False}})
    trajectory_contract.write_text("contract", encoding="utf-8")
    config.write_text("config", encoding="utf-8")
    labels.write_bytes(b"labels")
    weights.write_bytes(b"weights")

    report = build_readiness_report(
        prompt="daytime urban road with a motorcycle",
        scenario_id="unit_gpu_gate_blocked",
        runtime_compare=runtime_compare,
        motion_gap=tmp_path / "missing_motion_gap.json",
        velocity_surface=velocity_surface,
        trajectory_contract_doc=trajectory_contract,
        config_path=config,
        labels_path=labels,
        weights_path=weights,
    )

    assert report["gpu_smoke_allowed"] is False
    assert report["semantic_claim_allowed"] is False
    assert report["required_evidence"]["motion_control_gap_audit"]["exists"] is False
