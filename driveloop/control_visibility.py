"""Automatic control-visibility score S_ctrl (paper Eq. 5).

Measures whether requested scenario controls are visible in the generated
video using detector/tracker evidence already computed by the perception
evaluator. Channels that cannot be measured automatically are listed as
unmeasured and excluded from the average; they are never counted as passed.
Only active when perception was actually measured.
"""
from __future__ import annotations

from typing import Any, Dict

from driveloop.schema import LongTailConditionPlan, SceneSpecification

_MOTION_FULL_CREDIT = 1.0


def control_visibility_score(
    metrics: Dict[str, float],
    scene_spec: SceneSpecification,
    condition_plan: LongTailConditionPlan,
) -> Dict[str, Any]:
    if metrics.get("perception_measured") != 1.0:
        return {"score": None, "channels": {}, "unmeasured": ["perception_not_measured"],
                "source": "auto_control_visibility"}

    channels: Dict[str, float] = {}
    unmeasured: list[str] = []

    if scene_spec.objects:
        # object_presence is fidelity-weighted when the super-class evaluator
        # (v10) reports class fidelity: the requested control is visible to the
        # degree its super-class detections read as the target class, so pure
        # non-target residue (fidelity 0) does not count the control as present.
        # This is caliber C (block 223): it corrects the super-class over-count
        # that would otherwise credit an anchor's pedestrian residue as control
        # visibility. When fidelity is absent (v9 metrics) it falls back to
        # binary target-class detection, so it is inert until the v10 protocol
        # is wired in.
        fidelity = metrics.get("perception_class_fidelity")
        superclass = metrics.get("perception_superclass_detection_count")
        if fidelity is not None and superclass is not None:
            channels["object_presence"] = round(float(fidelity), 6) if float(superclass) > 0 else 0.0
        else:
            channels["object_presence"] = 1.0 if metrics.get("perception_detection_count", 0.0) > 0 else 0.0

    # target_motion is scored whenever perception was measured (guaranteed
    # by the early return above), not only when the grounder parsed a motion
    # word. An empty motion_primitives is almost always a parse failure --
    # m4's prompt requests a motion the keyword table cannot read -- and
    # sparing such a case the channel gives it a single channel to divide
    # by, inflating the FT lever (+38.1 vs +28.5 percent). Scoring it from
    # the archived measurement reproduces construction C3 per case to 1e-9
    # (block 217) and repairs m4 without a re-render.
    motion = metrics.get("perception_dominant_motion_over_width", -1.0)
    if motion is None or motion < 0:
        channels["target_motion"] = 0.0  # no usable track means the motion is not visible
    else:
        channels["target_motion"] = round(min(motion / _MOTION_FULL_CREDIT, 1.0), 6)

    # Lighting is a requested control we cannot measure under source-bound
    # generation: illumination is locked to the source scene, so a
    # brightness threshold on the selected view scores the source's light,
    # not the arm's. Listed as unmeasured like weather, never scored.
    # (2026-07-18 lighting-revival records; block 217 confirmed the nine
    # runs that still carry perception_best_view_brightness are disjoint
    # from the seven arms of the three-window table, so removal is score-
    # inert on the paper's numbers.)
    lighting = scene_spec.environment.get("lighting")
    if lighting in ("night", "daytime"):
        unmeasured.append("lighting.%s" % lighting)

    weather = scene_spec.environment.get("weather")
    if weather in ("rain", "fog", "snow"):
        unmeasured.append("weather.%s" % weather)

    score = round(sum(channels.values()) / len(channels), 6) if channels else None
    return {
        "score": score,
        "channels": channels,
        "unmeasured": unmeasured,
        "source": "auto_control_visibility",
        "claim_boundary": "video-derived detector evidence; unmeasured channels are excluded, not passed",
    }
