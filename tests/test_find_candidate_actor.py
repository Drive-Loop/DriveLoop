"""Tests for find_candidate_actor (actor identity discovery for source windows). No GPU."""

from __future__ import annotations

import scripts.find_candidate_actor as fca


def test_category_joins_list_and_passes_string():
    assert fca._category([["pedestrian", "adult"]], 0) == "pedestrian.adult"
    assert fca._category(["vehicle.car"], 0) == "vehicle.car"
    assert fca._category([], 0) == ""


def test_instances_across_frames_finds_full_coverage():
    front = [
        {"instance_tokens": ["ped_A", "car_X"], "labels3d": ["pedestrian.adult", "vehicle.car"]},
        {"instance_tokens": ["ped_A", "ped_B"], "labels3d": ["pedestrian.adult", "pedestrian.child"]},
        {"instance_tokens": ["ped_A", "ped_B"], "labels3d": ["pedestrian.adult", "pedestrian.child"]},
    ]
    presence, category = fca.instances_across_frames(front, "pedestrian")
    assert presence["ped_A"] == {0, 1, 2}
    assert presence["ped_B"] == {1, 2}
    assert "car_X" not in presence
    assert category["ped_A"] == "pedestrian.adult"


def test_find_actor_reports_full_coverage_instance(monkeypatch):
    records = [{"sample_token": "s0", "scene_token": "sc", "scene_description": "peds crossing",
                "instance_tokens": ["ped_A"], "labels3d": ["pedestrian.adult"]} for _ in range(24)]
    monkeypatch.setattr(fca, "load_records", lambda p: records)
    monkeypatch.setattr(fca, "candidate_camera_starts", lambda records, **k: [[0, 1, 2, 3, 4, 5]])
    out = fca.find_actor("x.pkl", 0, "pedestrian", frame_num=8, hz_factor=3)
    assert out["f0_sample_token"] == "s0"
    assert out["scene_token"] == "sc"
    assert out["instances_present_all_frames"][0]["instance_token"] == "ped_A"
    assert out["instances_present_all_frames"][0]["frames"] == [0, 1, 2, 3, 4, 5, 6, 7]
