"""Tests for select_source_from_prompt (prompt -> source window ranking). No GPU."""

from __future__ import annotations

import json

import scripts.select_source_from_prompt as sel


DIVERSE = [
    {"candidate_id": "moto_cut_in_night", "objects": ["motorcycle"], "motions": ["cut_in"],
     "tags": ["night"], "has_hdmap": True, "has_actor_identity": True},
    {"candidate_id": "pedestrian_crossing_day", "objects": ["pedestrian"], "motions": ["crossing"],
     "tags": ["daytime"], "has_hdmap": True, "has_actor_identity": True},
    {"candidate_id": "truck_highway_day", "objects": ["truck"], "motions": ["cut_in"],
     "tags": ["daytime"], "has_hdmap": True, "has_actor_identity": True},
]


def test_selects_motorcycle_window_for_motorcycle_prompt():
    ranking = sel.select_source("night urban street, a motorcycle cuts in from the left", DIVERSE)
    assert ranking["best_candidate_id"] == "moto_cut_in_night"


def test_selects_pedestrian_window_for_pedestrian_prompt():
    ranking = sel.select_source("a pedestrian crossing the road in daytime", DIVERSE)
    assert ranking["best_candidate_id"] == "pedestrian_crossing_day"


def test_selects_truck_window_for_truck_prompt():
    ranking = sel.select_source("a truck cuts in ahead on the highway", DIVERSE)
    assert ranking["best_candidate_id"] == "truck_highway_day"


def test_rankable_scene_exposes_weather_and_lighting_as_tags():
    spec, _ = sel.ground_prompt("rainy night, a motorcycle cuts in from the left")
    scene = sel._rankable_scene(spec)
    assert scene["weather"] == "rain"
    assert scene["lighting"] == "night"
    assert "rain" in scene["tags"] and "night" in scene["tags"]


def test_resolve_selected_binding_reads_baseline_dir(monkeypatch):
    ranking = {
        "best_candidate_id": "candidate162",
        "ranked_candidates": [
            {"candidate_id": "candidate162",
             "candidate": {"source_from_baseline_dir": "outputs/driveloop/v10w_candidate162_baseline_official"}},
        ],
    }
    import scripts.run_window_admission_probe as probe
    monkeypatch.setattr(probe, "source_config_from_baseline_dir",
                        lambda d: {"dataset_dir": "/mnt/x/ds", "source_candidate_id": "candidate162"})
    binding = sel.resolve_selected_binding(ranking)
    assert binding["source_candidate_id"] == "candidate162"


def test_load_pool_accepts_candidates_key(tmp_path):
    pool_path = tmp_path / "pool.json"
    pool_path.write_text(json.dumps({"candidates": DIVERSE}), encoding="utf-8")
    assert [c["candidate_id"] for c in sel.load_pool(pool_path)] == \
        ["moto_cut_in_night", "pedestrian_crossing_day", "truck_highway_day"]
