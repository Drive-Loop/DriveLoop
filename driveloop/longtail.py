from __future__ import annotations

from typing import Any, Dict, Iterable, List

from driveloop.schema import LongTailConditionPlan, SceneSpecification


_SUPPORTED_TAGS = {
    "traffic_accident",
    "heavy_rain",
    "fog",
    "snow",
    "animal_crossing",
    "road_obstacle",
    "low_visibility",
    "vulnerable_road_user",
    "motorcycle_cut_in",
    "motorcycle_lane_change",
    "left_lane_relation",
    "right_lane_relation",
}

_TAG_ALIASES = {
    "accident": "traffic_accident",
    "traffic accident": "traffic_accident",
    "rain": "heavy_rain",
    "rainy": "heavy_rain",
    "heavy rain": "heavy_rain",
    "foggy": "fog",
    "animal": "animal_crossing",
    "deer": "animal_crossing",
    "obstacle": "road_obstacle",
    "debris": "road_obstacle",
    "poor visibility": "low_visibility",
    "vulnerable road user": "vulnerable_road_user",
    "motorcycle": "vulnerable_road_user",
    "motorbike": "vulnerable_road_user",
    "cut in": "motorcycle_cut_in",
    "cut-in": "motorcycle_cut_in",
    "lane change": "motorcycle_lane_change",
    "lane-change": "motorcycle_lane_change",
    "left lane": "left_lane_relation",
    "right lane": "right_lane_relation",
}


class LongTailController:
    """Paper-aligned long-tail condition planner for Sec. 3.4.

    It returns ct = (Tt, P+t, Ut): resolved tags, prompt suffixes, and visual or
    post-processing controls.
    """

    def build(
        self,
        spec: SceneSpecification,
        requested_tags: Iterable[str] | None = None,
        history: Any | None = None,
    ) -> LongTailConditionPlan:
        tags = self._resolve_tags(spec, requested_tags)
        prompt_suffixes: List[str] = []
        postprocess_effects: List[str] = []
        executable_controls: Dict[str, Any] = {}

        for tag in tags:
            if tag == "traffic_accident":
                prompt_suffixes.append(
                    "traffic accident scene with stopped vehicles, warning cones, and emergency avoidance behavior"
                )
                executable_controls.setdefault("objects", []).extend(["stopped_vehicle", "traffic_cone", "barrier"])
            elif tag == "heavy_rain":
                prompt_suffixes.append("heavy rain with wet road surface and visible rain streaks")
                postprocess_effects.append("rain_overlay")
                executable_controls["weather"] = "heavy_rain"
            elif tag == "fog":
                prompt_suffixes.append("dense fog with low visibility and reduced contrast")
                postprocess_effects.append("fog_overlay")
                executable_controls["visibility"] = "low"
            elif tag == "snow":
                prompt_suffixes.append("snowy road with falling snow and low tire-road contrast")
                postprocess_effects.append("snow_overlay")
                executable_controls["weather"] = "snow"
            elif tag == "animal_crossing":
                prompt_suffixes.append("animal crossing from roadside into the ego lane")
                executable_controls.setdefault("objects", []).append("animal")
                executable_controls.setdefault("motion", []).append("crossing")
            elif tag == "road_obstacle":
                prompt_suffixes.append("visible road obstacle ahead requiring vehicle avoidance")
                executable_controls.setdefault("objects", []).append("road_obstacle")
            elif tag == "low_visibility":
                prompt_suffixes.append("low visibility conditions with difficult object perception")
                postprocess_effects.append("low_visibility_filter")
                executable_controls["visibility"] = "low"
                executable_controls.setdefault("perception_requirements", []).append("target_object_visible_across_frames")
            elif tag == "vulnerable_road_user":
                prompt_suffixes.append("clear vulnerable road user visibility with the target actor unoccluded")
                executable_controls.setdefault("objects", []).append("motorcycle")
                executable_controls.setdefault("target_object_support", {})["category"] = "motorcycle"
                executable_controls.setdefault("perception_requirements", []).append("target_motorcycle_detectable")
            elif tag == "motorcycle_cut_in":
                prompt_suffixes.append("a motorcycle performs a visible cut-in maneuver near the ego vehicle")
                executable_controls.setdefault("objects", []).append("motorcycle")
                executable_controls.setdefault("motion", []).append("cut_in")
                executable_controls.setdefault("maneuvers", []).append(
                    {
                        "actor": "motorcycle",
                        "type": "cut_in",
                        "relation": "adjacent_lane_to_ego_lane",
                        "requires_lane_geometry": True,
                        "requires_temporal_evidence": True,
                    }
                )
            elif tag == "motorcycle_lane_change":
                prompt_suffixes.append("a motorcycle performs a visible lane change with lateral displacement")
                executable_controls.setdefault("objects", []).append("motorcycle")
                executable_controls.setdefault("motion", []).append("lane_change")
                executable_controls.setdefault("maneuvers", []).append(
                    {
                        "actor": "motorcycle",
                        "type": "lane_change",
                        "relation": "adjacent_lane",
                        "requires_lane_geometry": True,
                        "requires_temporal_evidence": True,
                    }
                )
            elif tag == "left_lane_relation":
                prompt_suffixes.append("the target actor starts from the left adjacent lane")
                executable_controls.setdefault("lane_relations", []).append(
                    {
                        "actor": "target",
                        "from": "left_adjacent_lane",
                        "to": "ego_lane",
                    }
                )
            elif tag == "right_lane_relation":
                prompt_suffixes.append("the target actor starts from the right adjacent lane")
                executable_controls.setdefault("lane_relations", []).append(
                    {
                        "actor": "target",
                        "from": "right_adjacent_lane",
                        "to": "ego_lane",
                    }
                )

        for key in ("objects", "motion", "perception_requirements"):
            if key in executable_controls and isinstance(executable_controls[key], list):
                executable_controls[key] = list(dict.fromkeys(executable_controls[key]))

        return LongTailConditionPlan(
            tags=tags,
            prompt_suffixes=list(dict.fromkeys(prompt_suffixes)),
            postprocess_effects=list(dict.fromkeys(postprocess_effects)),
            executable_controls=executable_controls,
        )

    def _resolve_tags(
        self,
        spec: SceneSpecification,
        requested_tags: Iterable[str] | None,
    ) -> List[str]:
        resolved: List[str] = []

        for tag in requested_tags or []:
            normalized = self._normalize_tag(str(tag))
            if normalized in _SUPPORTED_TAGS:
                resolved.append(normalized)

        env = spec.environment
        if env.get("weather") == "rain":
            resolved.append("heavy_rain")
        elif env.get("weather") == "fog":
            resolved.append("fog")
        elif env.get("weather") == "snow":
            resolved.append("snow")
        if env.get("visibility") == "low":
            resolved.append("low_visibility")

        categories = {obj.category for obj in spec.objects}
        motions = set(spec.motion_primitives)
        if "motorcycle" in categories:
            resolved.append("vulnerable_road_user")
            if "cut_in" in motions:
                resolved.append("motorcycle_cut_in")
            if "lane_change" in motions:
                resolved.append("motorcycle_lane_change")

        if "left" in spec.relations and ("cut_in" in motions or "lane_change" in motions):
            resolved.append("left_lane_relation")
        if "right" in spec.relations and ("cut_in" in motions or "lane_change" in motions):
            resolved.append("right_lane_relation")

        if "animal" in categories and "crossing" in motions:
            resolved.append("animal_crossing")
        if "obstacle" in categories:
            resolved.append("road_obstacle")
        if "stopped" in motions and ("car" in categories or "truck" in categories or "bus" in categories):
            resolved.append("traffic_accident")

        return list(dict.fromkeys(resolved))

    def _normalize_tag(self, tag: str) -> str:
        tag = tag.lower().strip().replace("-", "_").replace(" ", "_")
        return _TAG_ALIASES.get(tag, tag)


_WEATHER_TAGS = {"heavy_rain", "fog", "snow", "low_visibility"}
_OBJECT_TAGS = {"vulnerable_road_user", "road_obstacle", "animal_crossing", "traffic_accident"}
_MOTION_TAGS = {"motorcycle_cut_in", "motorcycle_lane_change"}
_LANE_RELATION_TAGS = {"left_lane_relation", "right_lane_relation"}


def _tag_supported(tag: str, plan: LongTailConditionPlan) -> bool:
    """Gamma_r in Eq. (10): check tag r maps to at least one executable channel."""
    controls = plan.executable_controls
    has_suffix = bool(plan.prompt_suffixes)
    if tag in _WEATHER_TAGS:
        return has_suffix and (
            bool(plan.postprocess_effects)
            or "weather" in controls
            or "visibility" in controls
        )
    if tag in _OBJECT_TAGS:
        return bool(controls.get("objects"))
    if tag in _MOTION_TAGS:
        return bool(controls.get("motion")) and bool(controls.get("maneuvers"))
    if tag in _LANE_RELATION_TAGS:
        return bool(controls.get("lane_relations"))
    return False


def control_coverage(
    plan: LongTailConditionPlan,
    tag_weights: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """Compute C_lt = sum_r alpha_r * Gamma_r over resolved long-tail tags (Eq. 10).

    Returns a dict with the scalar score, per-tag support, and unsupported tags.
    A keyword in the prompt alone is never counted as an executable channel.
    """
    tags = list(plan.tags)
    if not tags:
        return {
            "schema_version": "driveloop_control_coverage.v0",
            "score": 1.0,
            "tag_support": {},
            "unsupported_tags": [],
            "tag_count": 0,
        }

    weights = tag_weights or {}
    total_weight = 0.0
    supported_weight = 0.0
    tag_support: Dict[str, bool] = {}
    unsupported: List[str] = []

    for tag in tags:
        alpha = float(weights.get(tag, 1.0))
        total_weight += alpha
        supported = _tag_supported(tag, plan)
        tag_support[tag] = supported
        if supported:
            supported_weight += alpha
        else:
            unsupported.append(tag)

    score = supported_weight / total_weight if total_weight > 0 else 0.0
    return {
        "schema_version": "driveloop_control_coverage.v0",
        "score": round(score, 6),
        "tag_support": tag_support,
        "unsupported_tags": unsupported,
        "tag_count": len(tags),
    }
