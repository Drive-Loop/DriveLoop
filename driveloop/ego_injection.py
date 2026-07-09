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


def apply_trajectory_tangent_heading(mapped_entries: list) -> str:
    """Replace each entry's plan heading with the tangent of the actor's
    GLOBAL trajectory, re-expressed in that frame's reference ego frame.

    Rationale: the motion plan carries a constant yaw, so a cutting-in
    actor slides sideways without turning (physically inconsistent
    conditioning). The tangent must be taken on the GLOBAL positions
    (ego motion + relative motion): the ego usually moves faster than
    the relative drift, so a relative-frame tangent would point
    backwards. Entries with tiny global displacement keep the plan
    heading. Mutates entries in place; returns the resulting mode."""
    ordered = sorted(mapped_entries, key=lambda e: int(e.get("relative_frame_idx", 0)))
    if len(ordered) < 2:
        return "plan_yaw_single_frame"
    transforms = [np.asarray(e["ref_ego2global"], dtype=np.float64) for e in ordered]
    centers = [
        (transforms[i] @ np.append(np.asarray(ordered[i]["ego"]["center_ego"], dtype=np.float64), 1.0))[:3]
        for i in range(len(ordered))
    ]
    changed = 0
    for i, entry in enumerate(ordered):
        j = i + 1 if i + 1 < len(ordered) else i
        k = i if i + 1 < len(ordered) else i - 1
        displacement = centers[j] - centers[k]
        if float(np.linalg.norm(displacement[:2])) < 0.05:
            entry["heading"] = {"mode": "plan_yaw_kept_small_displacement"}
            continue
        rotation = transforms[i][:3, :3]
        v_ego = rotation.T @ displacement
        entry["heading"] = {
            "mode": "trajectory_tangent_global",
            "plan_heading_ego": float(entry["ego"]["heading_ego"]),
        }
        entry["ego"]["heading_ego"] = float(np.arctan2(v_ego[1], v_ego[0]))
        changed += 1
    return "trajectory_tangent_global" if changed else "plan_yaw_kept_small_displacement"


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
