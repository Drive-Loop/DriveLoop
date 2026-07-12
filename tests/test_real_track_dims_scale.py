from driveloop.backends.drivedreamer2 import real_track_dims_scale


def test_default_is_identity(monkeypatch):
    monkeypatch.delenv("DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE", raising=False)
    assert real_track_dims_scale() == 1.0


def test_env_sets_scale(monkeypatch):
    monkeypatch.setenv("DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE", "1.5")
    assert real_track_dims_scale() == 1.5


def test_invalid_env_falls_back(monkeypatch):
    monkeypatch.setenv("DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE", "abc")
    assert real_track_dims_scale() == 1.0


def test_nonpositive_env_falls_back(monkeypatch):
    monkeypatch.setenv("DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE", "0")
    assert real_track_dims_scale() == 1.0


def test_negative_env_falls_back(monkeypatch):
    monkeypatch.setenv("DRIVELOOP_EGO_REAL_TRACK_DIMS_SCALE", "-2")
    assert real_track_dims_scale() == 1.0
