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

    assert report["status"] == "measured"
    assert report["source"] == "manual_review_frame_pack_v0"
    assert report["review_scope"]["video"] == "outputs/example/iteration_00.mp4"
    assert report["review_scope"]["contact_sheet"] == "outputs/example/contact_sheet.jpg"
    assert report["checks"][0]["name"] == "object_presence.motorcycle"
