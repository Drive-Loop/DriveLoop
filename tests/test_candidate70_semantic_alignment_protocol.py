import json
from pathlib import Path

from scripts.run_candidate70_semantic_alignment_protocol import (
    build_candidate70_semantic_alignment_protocol,
    build_report_template,
    required_semantic_checks,
    write_protocol_outputs,
)


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_required_semantic_checks_cover_cut_in_and_claim_boundary():
    checks = required_semantic_checks()
    names = {check["name"] for check in checks}

    assert "artifact.video_available_and_decodable" in names
    assert "object_presence.motorcycle_or_scooter_visible" in names
    assert "maneuver.cut_in_from_left_toward_ego_visible" in names
    assert "temporal_motion.lateral_displacement_visible" in names
    assert "hdmap_alignment.lane_geometry_visually_consistent_with_scene" in names
    assert all(check["required"] is True for check in checks)
    assert all(check["passed"] is False for check in checks)
    assert all(check["evidence"] == "not_reviewed" for check in checks)


def test_protocol_uses_accepted_prompt_and_keeps_claim_closed(tmp_path: Path):
    accepted_prompt = tmp_path / "accepted_prompt.json"
    gate = tmp_path / "gate.json"
    write_json(
        accepted_prompt,
        {
            "accepted_prompt_selected": True,
            "selected_prompt": {"prompt": "accepted candidate70 prompt"},
        },
    )
    write_json(
        gate,
        {
            "readiness_status": "blocked",
            "gpu_smoke_allowed": False,
            "blockers": ["semantic_success_claim_not_allowed"],
            "checks": {
                "source_bound_actor_motion_runtime_connected": True,
                "source_bound_actor_motion_sample_identity_verified": True,
                "local_map_vector_hdmap_reaches_grounding_surface": True,
                "local_map_vector_hdmap_lane_geometry_override_verified": True,
                "runtime_motion_control_connected": True,
                "true_lane_geometry_replacement_available": True,
            },
        },
    )

    protocol = build_candidate70_semantic_alignment_protocol(
        accepted_prompt_selection_path=accepted_prompt,
        readiness_gate_path=gate,
        output_dir=tmp_path / "protocol",
    )

    assert protocol["status"] == "protocol_defined"
    assert protocol["prompt"] == "accepted candidate70 prompt"
    assert protocol["readiness_gate"]["structural_evidence_ready"] is True
    assert protocol["does_not_run_gpu"] is True
    assert protocol["does_not_generate_video"] is True
    assert protocol["semantic_success_claim_allowed"] is False
    assert protocol["measurement_acceptance_rule"]["report_status_must_be_measured"] is True
    assert protocol["claim_boundary"]["protocol_definition_is_not_video_semantic_success"] is True


def test_report_template_is_not_measured_until_reviewed(tmp_path: Path):
    protocol = build_candidate70_semantic_alignment_protocol(output_dir=tmp_path)
    report = build_report_template(protocol)

    assert report["status"] == "not_measured"
    assert report["semantic_success_claim_allowed"] is False
    assert all(check["passed"] is False for check in report["checks"])
    assert report["claim_boundary"]["template_is_not_measured_review"] is True


def test_write_protocol_outputs_writes_protocol_and_template(tmp_path: Path):
    protocol = build_candidate70_semantic_alignment_protocol(output_dir=tmp_path)
    outputs = write_protocol_outputs(protocol, tmp_path)

    assert Path(outputs["protocol"]).exists()
    assert Path(outputs["report_template"]).exists()
    assert json.loads(Path(outputs["report_template"]).read_text(encoding="utf-8"))["status"] == "not_measured"
