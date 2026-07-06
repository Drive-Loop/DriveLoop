from __future__ import annotations

from typing import Dict, Iterable, List

from driveloop.schema import DriveLoopRequest, SceneObject, SceneSpecification


_OBJECT_KEYWORDS: Dict[str, List[str]] = {
    "car": ["car", "vehicle", "vehicles"],
    "truck": ["truck"],
    "bus": ["bus"],
    "pedestrian": ["pedestrian", "person", "people"],
    "bicycle": ["bicycle", "bike", "cyclist", "cyclists"],
    "motorcycle": ["motorcycle", "motorbike"],
    "animal": ["animal", "deer", "dog"],
    "traffic_cone": ["traffic cone", "cone"],
    "barrier": ["barrier", "warning fence", "fence"],
    "obstacle": ["obstacle", "debris", "road hazard"],
}

_MOTION_KEYWORDS: Dict[str, List[str]] = {
    "cut_in": ["cut in", "cut-in", "cuts in"],
    "lane_change": ["lane change", "lane-change", "changes lane", "changing lane"],
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

    def __init__(self, multimodal_preprocessor=None) -> None:
        self.multimodal_preprocessor = multimodal_preprocessor

    def ground(self, request: DriveLoopRequest) -> SceneSpecification:
        structured_intent = request.metadata.get("structured_intent")
        if isinstance(structured_intent, dict):
            return self._ground_structured_intent(request, structured_intent)

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

    def _ground_structured_intent(
        self,
        request: DriveLoopRequest,
        structured_intent: Dict[str, object],
    ) -> SceneSpecification:
        objects = [
            SceneObject(
                category=str(actor.get("category", "unknown")),
                attributes=dict(actor.get("attributes", {})),
            )
            for actor in structured_intent.get("actors", [])
            if isinstance(actor, dict) and actor.get("category")
        ]

        weather = str(structured_intent.get("weather") or "unspecified")
        lighting = str(structured_intent.get("lighting") or "unspecified")
        visibility = "low" if weather == "fog" or "low_visibility" in structured_intent.get("risk_factors", []) else "normal"

        return SceneSpecification(
            prompt=request.prompt,
            objects=objects,
            attributes={
                "viewpoint": "panoramic_multi_view",
                "style": "realistic",
            },
            relations=[str(item) for item in structured_intent.get("relations", [])],
            motion_primitives=[str(item) for item in structured_intent.get("motion_primitives", [])],
            environment={
                "weather": weather,
                "lighting": lighting,
                "visibility": visibility,
            },
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
        if self.multimodal_preprocessor is not None:
            for item in self.multimodal_preprocessor.collect_evidence(request.metadata):
                if item.text:
                    evidence.append(item.text)
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
