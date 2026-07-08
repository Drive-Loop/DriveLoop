import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from driveloop.actor_motion import derive_target_cam_types


def test_default_stays_cam_front_only(monkeypatch):
    monkeypatch.delenv("DRIVELOOP_INJECT_ALL_CAM_TYPES", raising=False)
    assert derive_target_cam_types(["left"]) == ["cam_front"]


def test_probe_env_restores_all_views(monkeypatch):
    monkeypatch.setenv("DRIVELOOP_INJECT_ALL_CAM_TYPES", "1")
    cams = derive_target_cam_types(["left"])
    assert len(cams) == 6
    assert "cam_front_left" in cams and "cam_back" in cams


def test_probe_env_other_values_ignored(monkeypatch):
    monkeypatch.setenv("DRIVELOOP_INJECT_ALL_CAM_TYPES", "0")
    assert derive_target_cam_types([]) == ["cam_front"]
