from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass(frozen=True)
class MultimodalInputBundle:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def modalities(self) -> List[str]:
        values = self.metadata.get("modalities", ["text"])
        return list(values) if isinstance(values, list) else ["text"]


class IntentUnderstandingAdapter(Protocol):
    def parse_bundle(self, bundle: MultimodalInputBundle) -> "StructuredIntent":
        ...


@dataclass
class StructuredIntent:
    weather: str = "unspecified"
    lighting: str = "unspecified"
    road_environment: str = "unspecified"
    actors: List[Dict[str, Any]] = field(default_factory=list)
    relations: List[str] = field(default_factory=list)
    motion_primitives: List[str] = field(default_factory=list)
    long_tail_tags: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    multimodal_evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weather": self.weather,
            "lighting": self.lighting,
            "road_environment": self.road_environment,
            "actors": self.actors,
            "relations": self.relations,
            "motion_primitives": self.motion_primitives,
            "long_tail_tags": self.long_tail_tags,
            "risk_factors": self.risk_factors,
            "multimodal_evidence": self.multimodal_evidence,
        }


class RuleBasedIntentAdapter:
    """Lightweight prompt-to-structured-intent adapter for reproducible API traces."""

    def parse_bundle(self, bundle: MultimodalInputBundle) -> StructuredIntent:
        return self.parse(bundle.text, metadata=bundle.metadata)

    def parse(self, prompt: str, metadata: Dict[str, Any] | None = None) -> StructuredIntent:
        metadata = metadata or {}
        text = self._compose_multimodal_text(prompt, metadata)
        intent = StructuredIntent(multimodal_evidence=self._extract_multimodal_evidence(metadata))

        if any(word in text for word in ["rain", "rainy", "wet road"]):
            intent.weather = "rain"
            intent.long_tail_tags.append("heavy_rain")
            intent.risk_factors.append("reduced_friction")
        if any(word in text for word in ["fog", "foggy", "low visibility"]):
            intent.weather = "fog"
            intent.long_tail_tags.extend(["fog", "low_visibility"])
            intent.risk_factors.append("low_visibility")
        if "snow" in text:
            intent.weather = "snow"
            intent.long_tail_tags.append("snow")
            intent.risk_factors.append("low_friction")

        if any(word in text for word in ["night", "dark", "low light"]):
            intent.lighting = "night"
            intent.risk_factors.append("low_light")
        elif any(word in text for word in ["daytime", "daylight", "sunny"]):
            intent.lighting = "daytime"

        if "intersection" in text:
            intent.road_environment = "urban_intersection"
            intent.relations.append("intersection")
        elif any(word in text for word in ["highway", "freeway"]):
            intent.road_environment = "highway"
        elif any(word in text for word in ["urban", "city", "street", "road"]):
            intent.road_environment = "urban_road"

        actor_keywords = {
            "car": ["car", "vehicle", "vehicles", "sedan", "truck", "bus"],
            "pedestrian": ["pedestrian", "person", "walker"],
            "cyclist": ["cyclist", "bike", "bicycle"],
            "animal": ["animal", "deer", "dog"],
        }
        for category, keywords in actor_keywords.items():
            if any(keyword in text for keyword in keywords):
                intent.actors.append({"category": category, "attributes": {}})

        if any(term in text for term in ["cross", "crosses", "crossing"]):
            intent.motion_primitives.append("crossing")
        if any(term in text for term in ["cut in", "cuts in", "cut-in", "cut_in"]):
            intent.motion_primitives.append("cut_in")
            intent.long_tail_tags.append("cut_in")
            intent.risk_factors.append("sudden_lane_change")
        if any(term in text for term in ["parked", "stopped", "stationary"]):
            intent.motion_primitives.append("stopped")
            intent.long_tail_tags.append("stopped_vehicle")
            intent.risk_factors.append("static_obstacle")
        if any(term in text for term in ["accident", "crash", "collision"]):
            intent.long_tail_tags.append("traffic_accident")
            intent.risk_factors.append("accident_scene")

        if "front" in text:
            intent.relations.append("front")
        if "right" in text:
            intent.relations.append("right")
        if "left" in text:
            intent.relations.append("left")

        intent.relations = self._unique(intent.relations)
        intent.motion_primitives = self._unique(intent.motion_primitives)
        intent.long_tail_tags = self._unique(intent.long_tail_tags)
        intent.risk_factors = self._unique(intent.risk_factors)
        return intent


    def _compose_multimodal_text(self, prompt: str, metadata: Dict[str, Any]) -> str:
        parts = [prompt]

        voice = metadata.get("voice", {})
        if isinstance(voice, dict) and voice.get("transcript"):
            parts.append(str(voice["transcript"]))

        image = metadata.get("image", {})
        if isinstance(image, dict) and image.get("filename"):
            filename = str(image["filename"]).replace("_", " ").replace("-", " ")
            parts.append(filename)

        return " ".join(parts).lower()

    def _extract_multimodal_evidence(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        evidence: Dict[str, Any] = {
            "modalities": metadata.get("modalities", ["text"]),
        }
        if "image" in metadata:
            evidence["image"] = {
                "filename": metadata["image"].get("filename"),
                "status": metadata["image"].get("status", "placeholder"),
            }
        if "voice" in metadata:
            evidence["voice"] = {
                "transcript": metadata["voice"].get("transcript"),
                "status": metadata["voice"].get("status", "placeholder"),
            }
        return evidence

    def _unique(self, values: List[str]) -> List[str]:
        seen = set()
        result = []
        for value in values:
            if value not in seen:
                result.append(value)
                seen.add(value)
        return result
