import json
from pathlib import Path

from scripts.run_candidate70_retry_refinement_proposal import (
    build_retry_refinement_proposal,
    failed_alignment_checks,
    write_proposal,
)


def alignment_eval():
    return {
        "interpretation": {"video_semantic_claim": "measured_failed"},
        "generation": {
            "prompt": "night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video."
        },
        "checks": [
            {"name": "object_presence.motorcycle_or_scooter_visible", "required": True, "passed": False},
            {"name": "maneuver.cut_in_from_left_toward_ego_visible", "required": True, "passed": False},
            {"name": "temporal_motion.lateral_displacement_visible", "required": True, "passed": False},
        ],
    }


def perception_eval():
    return {
        "interpretation": {"perception_claim": "measured_failed"},
        "evaluation": {
            "diagnosis": {
                "passed": False,
                "reasons": [
                    "target_object_not_detected",
                    "low_detection_coverage",
                    "unstable_track_coverage",
                ],
                "suggested_actions": [
                    "make the target actor visible across more frames",
                    "reduce occlusion and keep motion temporally coherent",
                ],
            }
        },
    }


def gpu_gate():
    return {
        "gpu_retry_gate": {
            "status": "blocked_requires_explicit_user_approval",
            "allowed": False,
            "blockers": ["explicit_gpu_retry_approval_missing"],
        }
    }


def test_failed_alignment_checks_reads_required_failures():
    assert failed_alignment_checks(alignment_eval()) == [
        "object_presence.motorcycle_or_scooter_visible",
        "maneuver.cut_in_from_left_toward_ego_visible",
        "temporal_motion.lateral_displacement_visible",
    ]


def test_candidate70_retry_refinement_proposal_combines_alignment_and_perception_feedback():
    proposal = build_retry_refinement_proposal(
        alignment_eval(),
        {"taxonomy_labels": ["motorcycle_identity_failed", "cut_in_motion_failed"]},
        perception_eval(),
        gpu_gate(),
    )

    assert proposal["status"] == "retry_refinement_proposal_ready_blocked_on_explicit_approval"
    assert proposal["does_not_run_gpu"] is True
    assert proposal["semantic_success_claim_allowed"] is False
    assert "clearly visible motorcycle or scooter target" in proposal["refined_prompt"]
    assert "target actor remains large, visible, and unoccluded" in proposal["refined_prompt"]
    assert "alignment_feedback" in proposal["refinement_condition"]
    assert "perception_feedback" in proposal["refinement_condition"]
    assert proposal["evidence_summary"]["perception_claim"] == "measured_failed"
    assert proposal["retry_policy"]["explicit_gpu_retry_approval_required"] is True
    assert proposal["claim_boundary"]["retry_refinement_proposal_is_not_semantic_success"] is True


def test_candidate70_retry_refinement_proposal_marks_incomplete_without_perception_failure():
    data = perception_eval()
    data["interpretation"]["perception_claim"] = "not_measured"

    proposal = build_retry_refinement_proposal(
        alignment_eval(),
        {"taxonomy_labels": []},
        data,
        gpu_gate(),
    )

    assert proposal["status"] == "retry_refinement_proposal_incomplete"


def test_candidate70_retry_refinement_proposal_writes_json(tmp_path: Path):
    output = tmp_path / "proposal.json"
    proposal = build_retry_refinement_proposal(
        alignment_eval(),
        {"taxonomy_labels": []},
        perception_eval(),
        gpu_gate(),
    )

    write_proposal(output, proposal)
    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert loaded["schema_version"] == "driveloop_candidate70_retry_refinement_proposal.v0"
    assert loaded["does_not_generate_video"] is True
