"""Tests for the Step A window-admission probe (C1 binding + C2 v10b measurability).

No GPU, no dataset, no video decoding. C2 exercises the real grounding ->
long-tail -> condition-adapter -> actor-motion chain; C1 is monkeypatched because
build_source_sample_binding needs a DD2 runtime dataset on disk.
"""

from __future__ import annotations

import json

import scripts.run_window_admission_probe as probe


CUT_IN_LEFT = "night urban street, a motorcycle cuts in from the left toward the ego vehicle"
LANE_CHANGE_LEFT = "night street, a clearly visible motorcycle changes lane from the left into the ego lane"
INTERSECTION_APPROACH = "urban intersection, a motorcycle approaches the ego path from the left"


def test_c2_measurable_for_left_cut_in():
    surface_plan = probe.surface_plan_for(CUT_IN_LEFT)
    c2 = probe.c2_measurability(surface_plan)
    assert c2["surface_plan_available"] is True
    assert c2["measurable"] is True
    # cam order FL=0, F=1, FR=2, BR=3, B=4, BL=5: a left maneuver scores the
    # front target plus the left-side neighbors.
    assert c2["allowed_views"] == [0, 1, 5]
    assert c2["target_cam_types"] == ["cam_front"]
    assert c2["lateral_side"] == -1.0


def test_c2_measurable_for_left_lane_change():
    c2 = probe.c2_measurability(probe.surface_plan_for(LANE_CHANGE_LEFT))
    assert c2["measurable"] is True
    assert c2["allowed_view_count"] == 3


def test_c2_unmeasurable_for_intersection_approach():
    # The "approaching" primitive builds no surface plan (m4 class), so v10b
    # resolves no scorable view: unmeasurable, not a low-score failure.
    surface_plan = probe.surface_plan_for(INTERSECTION_APPROACH)
    c2 = probe.c2_measurability(surface_plan)
    assert c2["surface_plan_available"] is False
    assert c2["measurable"] is False
    assert c2["allowed_view_count"] == 0


def test_verdict_matrix():
    ready, not_ready = {"ready": True}, {"ready": False}
    measurable, not_measurable = {"measurable": True}, {"measurable": False}
    assert probe.verdict(ready, measurable) == "ADMIT"
    assert probe.verdict(ready, not_measurable) == "WARN"
    assert probe.verdict(not_ready, measurable) == "REJECT"
    assert probe.verdict(not_ready, not_measurable) == "REJECT"


def test_c1_binding_calls_build_source_sample_binding(monkeypatch):
    captured = {}

    def fake_binding(dataset_dir, **kwargs):
        captured["dataset_dir"] = dataset_dir
        captured.update(kwargs)
        return {
            "ready": True,
            "matched_sample_tokens": ["s"],
            "matched_scene_tokens": ["sc"],
            "front_record": {"scene_token": "sc"},
            "dd2_batch_skip": 3,
        }

    monkeypatch.setattr(probe, "build_source_sample_binding", fake_binding)
    c1 = probe.c1_binding({"dataset_dir": "/data/x", "sample_token": "s", "scene_token": "sc"})
    assert c1["ready"] is True
    assert captured["dataset_dir"] == "/data/x"
    assert captured["sample_token"] == "s"
    assert captured["scene_token"] == "sc"


def test_report_rejects_when_binding_not_ready(monkeypatch):
    monkeypatch.setattr(
        probe, "build_source_sample_binding",
        lambda dataset_dir, **kwargs: {"ready": False, "reason": "dd2_labels_data_missing"},
    )
    report = probe.build_report(
        "candidateX", {"dataset_dir": "/data/x"}, [{"name": "m1", "prompt": CUT_IN_LEFT}]
    )
    assert report["cases"][0]["verdict"] == "REJECT"


def test_report_admits_measurable_and_warns_approach_when_bound(monkeypatch):
    monkeypatch.setattr(
        probe, "build_source_sample_binding",
        lambda dataset_dir, **kwargs: {
            "ready": True, "matched_sample_tokens": [], "matched_scene_tokens": [],
            "front_record": {}, "dd2_batch_skip": 0,
        },
    )
    report = probe.build_report(
        "candidateX", {"dataset_dir": "/data/x"},
        [{"name": "m1", "prompt": CUT_IN_LEFT}, {"name": "m4", "prompt": INTERSECTION_APPROACH}],
    )
    verdicts = {row["case"]: row["verdict"] for row in report["cases"]}
    assert verdicts["m1"] == "ADMIT"
    assert verdicts["m4"] == "WARN"


def test_source_config_from_baseline_dir(tmp_path):
    meta = {
        "best_generation": {"metadata": {"dd2_source_sample_binding": {
            "dataset_dir": "/mnt/x/candidate162_source_bound/cam_all_train/v0.0.1",
            "selector": {
                "source_candidate_id": "candidate162",
                "sample_token": "758",
                "scene_token": "1d4",
                "instance_token": "23ee",
                "identity_summary_path": "outputs/x/summary.json",
            },
        }}}
    }
    directory = tmp_path / "v10w_candidate162_baseline_official"
    directory.mkdir()
    (directory / "result.json").write_text(json.dumps(meta), encoding="utf-8")
    config = probe.source_config_from_baseline_dir(directory)
    assert config["source_candidate_id"] == "candidate162"
    assert config["dataset_dir"].endswith("candidate162_source_bound/cam_all_train/v0.0.1")
    assert config["scene_token"] == "1d4"


def test_load_cases(tmp_path):
    manifest = tmp_path / "cases.json"
    manifest.write_text(json.dumps({"cases": [{"name": "m1", "prompt": CUT_IN_LEFT}]}), encoding="utf-8")
    assert probe.load_cases(manifest) == [{"name": "m1", "prompt": CUT_IN_LEFT}]
