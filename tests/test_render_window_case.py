"""Tests for render_window_case (token-safe window render wrapper). No GPU."""

from __future__ import annotations

import argparse
import json

import scripts.render_window_case as render


def _args(**kw):
    defaults = dict(cases="m.json", output_dir="out", config_name="mini",
                    max_iterations=1, target_score=0.99, perception_weights=None,
                    perception_confidence=0.20, use_task_utility=False)
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def test_build_experiment_argv_binds_from_config():
    config = {"source_candidate_id": "candidate162", "dataset_dir": "/mnt/x/ds",
              "scene_token": "sc", "sample_token": "sa", "instance_token": "in",
              "identity_summary_path": "id.json"}
    argv = render.build_experiment_argv(config, "b.mp4",
                                        _args(perception_weights="yolov8x.pt", use_task_utility=True))
    joined = " ".join(argv)
    assert "--backend drivedreamer2" in joined
    assert "--source-candidate-id candidate162" in joined
    assert "--baseline-dataset-dir /mnt/x/ds" in joined
    assert "--scene-token sc" in joined
    assert "--sample-token sa" in joined
    assert "--instance-token in" in joined
    assert "--source-identity-summary id.json" in joined
    assert "--perception-baseline-video b.mp4" in joined
    assert "--perception-weights yolov8x.pt" in joined
    assert "--use-task-utility" in joined


def test_build_experiment_argv_omits_absent_tokens():
    config = {"source_candidate_id": "candidate70", "dataset_dir": "/mnt/x/ds",
              "scene_token": None, "sample_token": "sa", "instance_token": None,
              "identity_summary_path": None}
    joined = " ".join(render.build_experiment_argv(config, None, _args()))
    assert "--sample-token sa" in joined
    assert "--scene-token" not in joined
    assert "--instance-token" not in joined
    assert "--perception-baseline-video" not in joined


def test_print_only_does_not_render(tmp_path, monkeypatch, capsys):
    directory = tmp_path / "v10w_candidate162_baseline_official"
    directory.mkdir()
    meta = {"best_generation": {"metadata": {"dd2_source_sample_binding": {
        "dataset_dir": "/mnt/x/candidate162_source_bound/cam_all_train/v0.0.1",
        "selector": {"source_candidate_id": "candidate162", "sample_token": "sa",
                     "scene_token": "sc", "instance_token": "in",
                     "identity_summary_path": "id.json"}}}}}
    (directory / "result.json").write_text(json.dumps(meta), encoding="utf-8")

    def _boom(argv):
        raise AssertionError("experiment_main must not run under --print-only")

    monkeypatch.setattr(render, "experiment_main", _boom)
    rc = render.main([
        "--source-from-baseline-dir", str(directory),
        "--cases", "m.json", "--output-dir", str(tmp_path / "out"), "--print-only",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "candidate162" in out
    assert "--baseline-dataset-dir" in out
