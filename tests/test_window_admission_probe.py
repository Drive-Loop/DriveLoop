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


def test_source_config_from_history_jsonl(tmp_path):
    # Older v9 baselines archive the binding in history.jsonl, not result.json.
    directory = tmp_path / "v9_no_injection_baseline"
    directory.mkdir()
    line = {"dd2_source_sample_binding": {
        "dataset_dir": "/mnt/x/candidate70_source_bound/cam_all_train/v0.0.1",
        "selector": {
            "source_candidate_id": "candidate70",
            "sample_token": "b4c2",
            "scene_token": None,
            "instance_token": "21cd",
            "identity_summary_path": "outputs/x/summary.json",
        },
    }}
    (directory / "history.jsonl").write_text(json.dumps(line) + "\n", encoding="utf-8")
    config = probe.source_config_from_baseline_dir(directory)
    assert config["source_candidate_id"] == "candidate70"
    assert config["dataset_dir"].endswith("candidate70_source_bound/cam_all_train/v0.0.1")
    assert config["sample_token"] == "b4c2"


def test_source_config_prefers_binding_with_nonnull_token(tmp_path):
    # A record may carry an all-null selector alongside the real one; the
    # extractor must skip the empty one and return the populated binding.
    directory = tmp_path / "baseline"
    directory.mkdir()
    empty = {"dd2_source_sample_binding": {"dataset_dir": "/mnt/x/win/v0.0.1", "selector": {
        "source_candidate_id": None, "sample_token": None, "scene_token": None, "instance_token": None}}}
    real = {"dd2_source_sample_binding": {"dataset_dir": "/mnt/x/win/v0.0.1", "selector": {
        "source_candidate_id": "candidateX", "sample_token": "tok"}}}
    (directory / "history.jsonl").write_text(
        json.dumps(empty) + "\n" + json.dumps(real) + "\n", encoding="utf-8"
    )
    config = probe.source_config_from_baseline_dir(directory)
    assert config["source_candidate_id"] == "candidateX"
    assert config["sample_token"] == "tok"


def test_load_cases(tmp_path):
    manifest = tmp_path / "cases.json"
    manifest.write_text(json.dumps({"cases": [{"name": "m1", "prompt": CUT_IN_LEFT}]}), encoding="utf-8")
    assert probe.load_cases(manifest) == [{"name": "m1", "prompt": CUT_IN_LEFT}]


# ---- Step B: C3 (baseline sanity) and C4 (baseline super-class presence, diagnostic) ----

def test_resolve_baseline_video_prefers_no_injection_iteration(tmp_path):
    artifacts = tmp_path / "v10w_no_injection_baseline" / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "iteration_00.mp4").write_bytes(b"x")
    resolved = probe.resolve_baseline_video(tmp_path)
    assert resolved is not None
    assert resolved.name == "iteration_00.mp4"
    assert "no_injection" in str(resolved)


def test_resolve_baseline_video_none_when_empty(tmp_path):
    assert probe.resolve_baseline_video(tmp_path) is None


def test_c3_pass_for_no_injection_baseline(tmp_path, monkeypatch):
    video = tmp_path / "v9_no_injection_baseline" / "artifacts" / "iteration_00.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"x")
    monkeypatch.setattr(probe, "source_row_fingerprint", lambda *a, **k: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    c3 = probe.c3_baseline_check(video, "candidate70", {"source_candidate_id": "candidate70"})
    assert c3["pass"] is True
    assert c3["is_no_injection"] is True
    assert c3["flags"] == []
    assert c3["source_row_fingerprint"] == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_c3_flags_missing_baseline(tmp_path):
    c3 = probe.c3_baseline_check(tmp_path / "nope.mp4", "candidate70", {"source_candidate_id": "candidate70"})
    assert c3["pass"] is False
    assert "baseline_missing" in c3["flags"]


def test_c3_flags_staging_video_not_no_injection(tmp_path, monkeypatch):
    # The block-220 trap: a per-run staging video, not a persisted no-injection baseline.
    video = tmp_path / "drivedreamer2_img_cond_mini" / "iteration_00.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"x")
    monkeypatch.setattr(probe, "source_row_fingerprint", lambda *a, **k: None)
    c3 = probe.c3_baseline_check(video, "candidate70", {"source_candidate_id": "candidate70"})
    assert c3["pass"] is False
    assert "baseline_not_no_injection" in c3["flags"]


def test_c3_flags_window_candidate_mismatch(tmp_path, monkeypatch):
    video = tmp_path / "v9_no_injection_baseline" / "iteration_00.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"x")
    monkeypatch.setattr(probe, "source_row_fingerprint", lambda *a, **k: None)
    c3 = probe.c3_baseline_check(video, "candidate162", {"source_candidate_id": "candidate70"})
    assert c3["pass"] is False
    assert "window_candidate_mismatch" in c3["flags"]


def test_verdict_with_c3():
    ready = {"ready": True}
    measurable = {"measurable": True}
    unmeasurable = {"measurable": False}
    c3_pass, c3_fail = {"pass": True}, {"pass": False}
    assert probe.verdict(ready, measurable, c3_pass) == "ADMIT"
    assert probe.verdict(ready, unmeasurable, c3_pass) == "WARN"
    assert probe.verdict(ready, measurable, c3_fail) == "BASELINE_SUSPECT"
    assert probe.verdict({"ready": False}, measurable, c3_pass) == "REJECT"


class _StubEvaluation:
    def __init__(self, count):
        self.metrics = {
            "perception_superclass_detection_count": count,
            "perception_selected_view": 1,
            "perception_allowed_view_count": 3,
        }


class _StubEvaluator:
    def __init__(self, count):
        self._count = count

    def evaluate(self, generation):
        return _StubEvaluation(self._count)


def test_c4_baseline_superclass_presence():
    present = probe.c4_baseline_superclass(_StubEvaluator(2.0), "b.mp4", {"available": True})
    assert present["superclass_actor_present"] is True
    assert present["superclass_detection_count"] == 2.0
    absent = probe.c4_baseline_superclass(_StubEvaluator(0.0), "b.mp4", {"available": True})
    assert absent["superclass_actor_present"] is False


def test_source_row_fingerprint_from_synthetic_frame():
    import numpy as np

    class _Reader:
        def read(self, path, max_frames=None):
            # 512 tall x (448*6) wide: top 256 is the source row, brightness 100.
            frame = np.zeros((512, 448 * 6, 3), dtype=np.uint8)
            frame[0:256, :, :] = 100
            return [frame]

    fingerprint = probe.source_row_fingerprint("x.mp4", reader=_Reader())
    assert fingerprint == [100.0, 100.0, 100.0, 100.0, 100.0, 100.0]


def test_build_report_c4_is_diagnostic_not_gate(monkeypatch):
    monkeypatch.setattr(
        probe, "build_source_sample_binding",
        lambda dataset_dir, **kwargs: {"ready": True, "matched_sample_tokens": [],
                                       "matched_scene_tokens": [], "front_record": {}, "dd2_batch_skip": 0},
    )
    monkeypatch.setattr(
        probe, "c3_baseline_check",
        lambda *a, **k: {"pass": True, "flags": [], "is_no_injection": True,
                         "source_candidate_id": "candidateX", "source_row_fingerprint": None},
    )
    report = probe.build_report(
        "candidateX", {"dataset_dir": "/data/x"}, [{"name": "m1", "prompt": CUT_IN_LEFT}],
        baseline_video="b.mp4", superclass_check=True, superclass_evaluator=_StubEvaluator(3.0),
    )
    # C4 detects a super-class actor, but it is diagnostic only: verdict stays ADMIT.
    assert report["cases"][0]["c4_superclass_actor_present"] is True
    assert report["cases"][0]["verdict"] == "ADMIT"
