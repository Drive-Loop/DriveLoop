from __future__ import annotations

from typing import Dict, Iterable, List

from driveloop.schema import DriveLoopRequest, SceneObject, SceneSpecification


_OBJECT_KEYWORDS: Dict[str, List[str]] = {
    "car": ["car", "vehicle", "vehicles"],
    "truck": ["truck"],
    "bus": ["bus"],
    "pedestrian": ["pedestrian", "person", "people"],
    "bicycle": ["bicycle", "bike"],
    "motorcycle": ["motorcycle", "motorbike"],
    "animal": ["animal", "deer", "dog"],
    "traffic_cone": ["traffic cone", "cone"],
    "barrier": ["barrier", "warning fence", "fence"],
    "obstacle": ["obstacle", "debris", "road hazard"],
}

_MOTION_KEYWORDS: Dict[str, List[str]] = {
    "cut_in": ["cut in", "cut-in", "cuts in"],
    "lane_change": ["lane change", "lane-change", "changes lane"],
    "crossing": ["crossing", "crosses", "cross the road"],
    "stopped": ["stopped", "parked", "stationary"],
    "turning": ["left turn", "right turn", "turning"],
}

_RELATION_KEYWORDS = [
    "front",
    "behind",
    "left",
    "right",
    "same lane",
    "adjacent lane",
    "intersection",
    "crosswalk",
]


class RuleBasedGrounder:
    """Paper-aligned prompt grounding placeholder.

    This module implements the schema in Sec. 3.3:
    s0 = (O0, A0, R0, P0, E0).

    Later this can be replaced by ASR/VLM/LLM grounding while keeping the same
    SceneSpecification interface.
    """

    def ground(self, request: DriveLoopRequest) -> SceneSpecification:
        evidence = self._collect_evidence(request)
        text = " ".join(evidence).lower()

        objects = [
            SceneObject(category=category)
            for category, keywords in _OBJECT_KEYWORDS.items()
            if any(keyword in text for keyword in keywords)
        ]

        motion_primitives = [
            motion
            for motion, keywords in _MOTION_KEYWORDS.items()
            if any(keyword in text for keyword in keywords)
        ]

        relations = [relation for relation in _RELATION_KEYWORDS if relation in text]
        environment = self._parse_environment(text)

        attributes = {
            "viewpoint": "panoramic_multi_view"
            if any(word in text for word in ["panoramic", "multi-view", "six camera"])
            else "unspecified",
            "style": "realistic" if "realistic" in text else "unspecified",
        }

        return SceneSpecification(
            prompt=request.prompt,
            objects=objects,
            attributes=attributes,
            relations=relations,
            motion_primitives=motion_primitives,
            environment=environment,
        )

    def _collect_evidence(self, request: DriveLoopRequest) -> List[str]:
        evidence = [request.prompt]
        auxiliary = request.metadata.get("auxiliary_inputs", {})
        if isinstance(auxiliary, dict):
            for value in auxiliary.values():
                if isinstance(value, str):
                    evidence.append(value)
                elif isinstance(value, Iterable):
                    evidence.extend(str(item) for item in value)
        return evidence

    def _parse_environment(self, text: str) -> Dict[str, str]:
        weather = "unspecified"
        lighting = "unspecified"
        visibility = "normal"

        if "rain" in text or "rainy" in text:
            weather = "rain"
        elif "fog" in text or "foggy" in text:
            weather = "fog"
            visibility = "low"
        elif "snow" in text or "snowy" in text:
            weather = "snow"

        if "night" in text:
            lighting = "night"
        elif "daytime" in text or "day" in text:
            lighting = "daytime"

        if "low visibility" in text or "poor visibility" in text:
            visibility = "low"

        return {
            "weather": weather,
            "lighting": lighting,
            "visibility": visibility,
        }
