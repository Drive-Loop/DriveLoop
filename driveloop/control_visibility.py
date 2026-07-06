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

_NIGHT_BRIGHTNESS_MAX = 90.0
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
        channels["object_presence"] = 1.0 if metrics.get("perception_detection_count", 0.0) > 0 else 0.0

    if scene_spec.motion_primitives:
        motion = metrics.get("perception_dominant_motion_over_width", -1.0)
        if motion is None or motion < 0:
            channels["target_motion"] = 0.0  # 无可用轨迹 = 运动不可见
        else:
            channels["target_motion"] = round(min(motion / _MOTION_FULL_CREDIT, 1.0), 6)

    lighting = scene_spec.environment.get("lighting")
    brightness = metrics.get("perception_best_view_brightness", -1.0)
    if lighting in ("night", "daytime"):
        if brightness is None or brightness < 0:
            unmeasured.append("lighting.%s" % lighting)
        elif lighting == "night":
            channels["lighting_night"] = 1.0 if brightness < _NIGHT_BRIGHTNESS_MAX else 0.0
        else:
            channels["lighting_daytime"] = 1.0 if brightness >= _NIGHT_BRIGHTNESS_MAX else 0.0

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
