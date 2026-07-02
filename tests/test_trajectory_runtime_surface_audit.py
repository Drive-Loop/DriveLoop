from scripts.run_trajectory_runtime_surface_audit import build_audit


def backend_summary_with_static_boxes():
    return {
        "runtime_input_audit": {
            "box_downsampler_input": {"available": True},
            "grounding_downsampler_input": {"available": True},
        },
        "paper_alignment_stage_3": {
            "status": "tensor_control_ready",
            "tensor_control_ready": True,
        },
    }


def test_lane_change_motion_is_not_runtime_connected_with_static_boxes_only():
    audit = build_audit(
        "daytime road where a vehicle performs a lane change",
        backend_summary_with_static_boxes(),
        velocity_audit={"claim": {"velocity_consumed_by_dd2_runtime": False}},
        motion_gap={"claim": {"lane_change_motion_tensor_control": "not_verified"}},
    )

    assert audit["requested_motions"] == ["lane_change"]
    assert audit["status"] == "not_runtime_connected"
    assert "trajectory_tensor_not_observed_in_runtime_audit" in audit["blockers"]
    assert "static_box_condition_available_but_not_temporal_motion_control" in audit["blockers"]
    assert audit["claim_boundary"]["static_boxes_are_not_temporal_motion_control"] is True


def test_prompt_without_motion_is_not_applicable():
    audit = build_audit(
        "daytime urban road with regular traffic",
        backend_summary_with_static_boxes(),
        velocity_audit={},
        motion_gap={},
    )

    assert audit["requested_motions"] == []
    assert audit["status"] == "not_applicable"


def test_velocity_claim_does_not_clear_blocker_without_runtime_tensor():
    audit = build_audit(
        "vehicle lane change",
        backend_summary_with_static_boxes(),
        velocity_audit={"claim": {"velocity_consumed_by_dd2_runtime": True}},
        motion_gap={},
    )

    assert audit["surfaces"]["velocity_tensor"]["available_in_runtime_audit"] is False
    assert audit["surfaces"]["velocity_tensor"]["velocity_consumed_by_dd2_runtime"] is False
    assert audit["surfaces"]["velocity_tensor"]["velocity_consumed_claimed_by_velocity_audit"] is True
    assert "velocity_or_displacement_tensor_not_consumed_by_runtime" in audit["blockers"]


def test_runtime_connected_when_required_surfaces_are_present_and_no_motion_requested_blockers():
    summary = {
        "runtime_input_audit": {
            "trajectory_tensor": {"available": True},
            "actor_velocity": {"available": True},
        }
    }
    audit = build_audit(
        "vehicle lane change",
        summary,
        velocity_audit={"claim": {"velocity_consumed_by_dd2_runtime": True}},
        motion_gap={},
    )

    assert audit["surfaces"]["trajectory_tensor"]["available"] is True
    assert audit["surfaces"]["velocity_tensor"]["available_in_runtime_audit"] is True
    assert "trajectory_tensor_not_observed_in_runtime_audit" not in audit["blockers"]
    assert "velocity_or_displacement_tensor_not_consumed_by_runtime" not in audit["blockers"]
    assert audit["status"] == "not_runtime_connected"
    assert "per_frame_actor_identity_not_observed" in audit["blockers"]


def test_actor_track_audit_clears_identity_and_per_frame_box_blockers():
    audit = build_audit(
        "vehicle lane change",
        backend_summary_with_static_boxes(),
        velocity_audit={"claim": {"velocity_consumed_by_dd2_runtime": False}},
        motion_gap={},
        actor_track_audit={
            "status": "per_frame_actor_tracks_observed",
            "track_surface": {"persistent_track_count": 2},
            "claim": {
                "per_frame_actor_identity_observed": True,
                "per_frame_actor_boxes3d_grouped_by_identity": True,
            },
        },
    )

    assert audit["status"] == "not_runtime_connected"
    assert audit["surfaces"]["actor_track_identity"]["per_frame_actor_identity_observed"] is True
    assert audit["surfaces"]["actor_track_identity"]["persistent_track_count"] == 2
    assert audit["surfaces"]["per_frame_actor_boxes3d"]["verified"] is True
    assert audit["surfaces"]["per_frame_actor_boxes3d"]["current_surface"] == "grouped_by_instance_token"
    assert "per_frame_actor_identity_not_observed" not in audit["blockers"]
    assert "per_frame_actor_boxes3d_not_verified" not in audit["blockers"]
    assert "trajectory_tensor_not_observed_in_runtime_audit" in audit["blockers"]
