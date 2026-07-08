"""Ego-frame injection helpers for DriveLoop overrides.

DriveLoop emits ONE ego-frame trajectory entry per video frame; each
camera record converts it into its own camera-frame box9 using the
record's calib (cam2ego, ego2global). This yields true per-view
projections (no clones) and removes camera-frame sign guessing.

Conventions (verified against real cross-camera annotation pairs,
zero-error round trip, 2026-07-08/09 audit):
- box9 layout: [cx, cy, cz, w, h, l, 0, ry, 0]; ry is rotation about
  camera y axis at index 7.
- calib chain: p_global = ego2global @ cam2ego @ p_cam.
- Ego heading psi is about ego z; heading direction in camera frame is
  (sin ry, 0, cos ry).
"""
from __future__ import annotations

import numpy as np


def cam_to_global_matrix(cam2ego, ego2global) -> np.ndarray:
    return np.asarray(ego2global, dtype=np.float64) @ np.asarray(cam2ego, dtype=np.float64)


def cam_box9_to_ego_entry(box9, cam2ego) -> dict:
    """Camera-frame box9 -> ego-frame entry (of that record's ego pose)."""
    box9 = np.asarray(box9, dtype=np.float64)
    T = np.asarray(cam2ego, dtype=np.float64)
    center = (T @ np.append(box9[:3], 1.0))[:3]
    ry = float(box9[7])
    h_cam = np.array([np.sin(ry), 0.0, np.cos(ry), 0.0])
    h_ego = (T @ h_cam)[:3]
    heading = float(np.arctan2(h_ego[1], h_ego[0]))
    return {
        "center_ego": [float(v) for v in center],
        "dims": [float(v) for v in box9[3:6]],
        "heading_ego": heading,
    }


def ego_entry_to_cam_box9(entry, ref_ego2global, cam2ego_dst, ego2global_dst) -> list:
    """Ego-frame entry (in the reference record's ego pose) -> camera-frame
    box9 of the destination record."""
    T_dst = cam_to_global_matrix(cam2ego_dst, ego2global_dst)
    M = np.linalg.inv(T_dst) @ np.asarray(ref_ego2global, dtype=np.float64)
    cx, cy, cz = entry["center_ego"]
    center = (M @ np.array([cx, cy, cz, 1.0]))[:3]
    psi = float(entry["heading_ego"])
    h_ego = np.array([np.cos(psi), np.sin(psi), 0.0, 0.0])
    h_cam = (M @ h_ego)[:3]
    ry = float(np.arctan2(h_cam[0], h_cam[2]))
    dims = entry["dims"]
    return [
        float(center[0]), float(center[1]), float(center[2]),
        float(dims[0]), float(dims[1]), float(dims[2]),
        0.0, ry, 0.0,
    ]
