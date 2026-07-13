from __future__ import annotations

from pathlib import Path

import pytest

import scripts.run_driveloop_experiment as runner


def test_missing_perception_baseline_video_fails_fast(tmp_path: Path):
    missing = tmp_path / "missing.mp4"
    with pytest.raises(SystemExit) as excinfo:
        runner.main(
            [
                "--cases", str(tmp_path / "cases.json"),
                "--output-dir", str(tmp_path / "out"),
                "--perception-baseline-video", str(missing),
            ]
        )
    assert excinfo.value.code == 2


def test_existing_perception_baseline_video_passes_guard(monkeypatch, tmp_path: Path):
    baseline = tmp_path / "baseline.mp4"
    baseline.write_bytes(b"video")
    captured = {}

    class FakePipeline:
        def __init__(self, **kwargs):
            captured["config"] = kwargs["config"]

        def run_cases(self, cases):
            return {"case_count": 0, "accepted_count": 0}

    monkeypatch.setattr(runner, "ExperimentPipeline", FakePipeline)
    monkeypatch.setattr(runner, "load_experiment_cases", lambda path: [])

    result = runner.main(
        [
            "--cases", str(tmp_path / "cases.json"),
            "--output-dir", str(tmp_path / "out"),
            "--perception-baseline-video", str(baseline),
        ]
    )

    assert result == 0
    assert captured["config"].perception_baseline_video == str(baseline)


def test_absent_flag_skips_guard(monkeypatch, tmp_path: Path):
    class FakePipeline:
        def __init__(self, **kwargs):
            pass

        def run_cases(self, cases):
            return {"case_count": 0, "accepted_count": 0}

    monkeypatch.setattr(runner, "ExperimentPipeline", FakePipeline)
    monkeypatch.setattr(runner, "load_experiment_cases", lambda path: [])

    result = runner.main(
        [
            "--cases", str(tmp_path / "cases.json"),
            "--output-dir", str(tmp_path / "out"),
        ]
    )

    assert result == 0
