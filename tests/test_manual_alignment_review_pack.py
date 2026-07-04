from pathlib import Path

from scripts.run_manual_alignment_review_pack import build_report, default_checks, sample_frame_indices


def test_sample_frame_indices_spans_video():
    assert sample_frame_indices(frame_count=8, num_frames=8) == [0, 1, 2, 3, 4, 5, 6, 7]
    assert sample_frame_indices(frame_count=16, num_frames=4) == [0, 5, 10, 15]


def test_sample_frame_indices_handles_short_or_empty_video():
    assert sample_frame_indices(frame_count=0, num_frames=8) == []
    assert sample_frame_indices(frame_count=1, num_frames=8) == [0]
    assert sample_frame_indices(frame_count=8, num_frames=1) == [0]


def test_default_checks_are_failed_until_reviewed():
    checks = default_checks()

    assert checks
    assert all(check["required"] is True for check in checks)
    assert all(check["passed"] is False for check in checks)
    assert all(check["score"] == 0.0 for check in checks)
    assert all(check["evidence"] == "not_reviewed" for check in checks)


def test_build_report_points_to_video_and_contact_sheet():
    report = build_report(
        video_path=Path("outputs/example/iteration_00.mp4"),
        contact_sheet=Path("outputs/example/contact_sheet.jpg"),
        prompt="daytime urban road with a motorcycle changing lane from the left",
    )

    assert report["status"] == "not_measured"
    assert report["source"] == "manual_review_frame_pack_v0"
    assert report["review_scope"]["video"] == "outputs/example/iteration_00.mp4"
    assert report["review_scope"]["contact_sheet"] == "outputs/example/contact_sheet.jpg"
    assert report["checks"][0]["name"] == "object_presence.motorcycle"
    assert report["semantic_success_claim_allowed"] is False
    assert report["claim_boundary"]["template_is_not_measured_review"] is True


def test_build_report_uses_candidate70_protocol_for_night_cut_in():
    report = build_report(
        video_path=Path("outputs/example/iteration_00.mp4"),
        contact_sheet=Path("outputs/example/contact_sheet.jpg"),
        prompt="night urban street with a motorcycle making a visible cut-in from the left toward the ego vehicle, panoramic multi-view video.",
    )

    names = {check["name"] for check in report["checks"]}

    assert "artifact.video_available_and_decodable" in names
    assert "maneuver.cut_in_from_left_toward_ego_visible" in names
    assert "temporal_motion.lateral_displacement_visible" in names
    assert "road_context.night_urban_multilane_or_lane_markings_visible" in names
    assert "hdmap_alignment.lane_geometry_visually_consistent_with_scene" in names
    assert "lighting.daytime" not in names
    assert len(report["checks"]) == 9
    assert report["semantic_success_claim_allowed"] is False
