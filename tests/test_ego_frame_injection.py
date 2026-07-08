import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = REPO_ROOT / "dreamer-train" / "projects" / "DriveDreamer2" / "drivedreamer2"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

import driveloop_ego_injection as ego

# Real record fixtures (v1.0-mini cam_all_val v0.0.2, first sample_token;
# dumped 2026-07-09, matrices rounded to 6 decimals, boxes to 4).
CAM2EGO_FRONT = [
    [0.010260, 0.008433, 0.999912, 1.722006],
    [-0.999873, 0.012316, 0.010156, 0.004755],
    [-0.012230, -0.999889, 0.008559, 1.494913],
    [0.0, 0.0, 0.0, 1.0],
]
E2G_FRONT = [
    [0.877140, 0.480056, 0.013118, 599.849792],
    [-0.479914, 0.877224, -0.012658, 1647.641113],
    [-0.017584, 0.004807, 0.999834, 0.0],
    [0.0, 0.0, 0.0, 1.0],
]
CAM2EGO_FL = [
    [0.822546, 0.006478, 0.568662, 1.575256],
    [-0.568684, 0.016434, 0.822392, 0.500519],
    [-0.004018, -0.999844, 0.017202, 1.506960],
    [0.0, 0.0, 0.0, 1.0],
]
E2G_FL = [
    [0.877241, 0.479870, 0.013138, 599.791321],
    [-0.479725, 0.877326, -0.012759, 1647.673584],
    [-0.017649, 0.004890, 0.999832, 0.0],
    [0.0, 0.0, 0.0, 1.0],
]
PAIRS = [
    ([-9.1778, 1.1333, 18.7546, 0.498, 1.761, 0.697, 0.0, 1.5725, 0.0],
     [10.4861, 1.1388, 18.0269, 0.498, 1.761, 0.697, 0.0, 2.5285, 0.0]),
    ([-12.3811, 1.8866, 27.8795, 0.783, 1.52, 0.738, 0.0, -3.0489, 0.0],
     [16.0942, 1.8876, 25.906, 0.783, 1.52, 0.738, 0.0, -2.0929, 0.0]),
]


def _ang_diff(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


@pytest.mark.parametrize("front_box,fl_box", PAIRS)
def test_cross_camera_roundtrip_reproduces_recorded_annotation(front_box, fl_box):
    entry = ego.cam_box9_to_ego_entry(front_box, CAM2EGO_FRONT)
    out = ego.ego_entry_to_cam_box9(entry, E2G_FRONT, CAM2EGO_FL, E2G_FL)
    for i in range(3):
        # Recorded cross-camera annotations of the same physical object
        # agree to ~mm; fixture rounding dominates the tolerance. Allow
        # extra slack because the two records' ego poses differ slightly
        # (different camera timestamps).
        assert abs(out[i] - fl_box[i]) < 0.8, (i, out[i], fl_box[i])
    assert out[3:6] == pytest.approx(fl_box[3:6])
    assert _ang_diff(out[7], fl_box[7]) < 5e-3
    assert out[6] == 0.0 and out[8] == 0.0


@pytest.mark.parametrize("front_box,_", PAIRS)
def test_identity_roundtrip_same_camera(front_box, _):
    entry = ego.cam_box9_to_ego_entry(front_box, CAM2EGO_FRONT)
    out = ego.ego_entry_to_cam_box9(entry, E2G_FRONT, CAM2EGO_FRONT, E2G_FRONT)
    assert out[:3] == pytest.approx(front_box[:3], abs=1e-6)
    # Heading is planarized in the ego frame by design (the camera's
    # pitch component of the heading vector is discarded); measured
    # loss on real records is ~1e-4 rad.
    assert _ang_diff(out[7], front_box[7]) < 1e-3


def test_synthetic_left_cut_in_lands_in_front_left_fov():
    # An ego-frame actor 20 m ahead, 3.5 m to the LEFT (ego x forward,
    # y left) must project into cam_front with negative x (left of
    # center) at ~20 m depth: the mirror class of bugs is structurally
    # impossible to reintroduce without failing this test.
    entry = {"center_ego": [20.0, 3.5, 1.0], "dims": [0.8, 1.4, 2.2], "heading_ego": 0.0}
    out = ego.ego_entry_to_cam_box9(entry, E2G_FRONT, CAM2EGO_FRONT, E2G_FRONT)
    assert out[2] > 15.0          # in front of the camera
    assert out[0] < -2.0          # on the LEFT side of cam_front
