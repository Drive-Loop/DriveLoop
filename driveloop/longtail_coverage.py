from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


SCHEMA_VERSION = "driveloop_longtail_control_coverage.v0"


def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def normalize_tag(value: Any) -> str:
    return str(value).lower().strip().replace("-", "_").replace(" ", "_")


def tag_variants(tag: str) -> set[str]:
    normalized = normalize_tag(tag)
    return {
        normalized,
        normalized.replace("_", " "),
        normalized.replace("_", "-"),
    }


def text_has_tag(text: Any, tag: str) -> bool:
    low = str(text).lower()
    return any(variant in low for variant in tag_variants(tag))


def tag_family(tag: str) -> str:
    tag = normalize_tag(tag)
    if tag in {"heavy_rain", "fog", "snow"}:
        return "weather"
    if tag == "low_visibility":
        return "visibility"
    if "cut_in" in tag or "lane_change" in tag or "crossing" in tag:
        return "motion"
    if "lane_relation" in tag:
        return "lane_relation"
    if any(token in tag for token in ["motorcycle", "pedestrian", "cyclist", "animal", "obstacle", "accident", "vulnerable"]):
        return "object"
    return "generic"


def required_channels(tag: str) -> list[str]:
    family = tag_family(tag)
    if family == "weather":
        return ["prompt_or_visual_effect"]
    if family == "visibility":
        return ["prompt_or_visual_effect", "evaluation"]
    if family == "motion":
        return ["source_or_structural", "evaluation"]
    if family in {"object", "lane_relation"}:
        return ["source_or_structural"]
    return ["prompt_or_visual_effect"]


def unwrap_condition_package(condition_package: Any) -> dict[str, Any]:
    package = as_dict(condition_package)
    executable = as_dict(package.get("executable_condition"))
    return executable if executable else package


def collect_tags(scene_spec: Any, condition_plan: Any, condition_package: Any = None) -> list[str]:
    scene = as_dict(scene_spec)
    plan = as_dict(condition_plan)
    package = unwrap_condition_package(condition_package)

    tags: list[str] = []
    tags.extend(normalize_tag(tag) for tag in as_list(plan.get("tags")))
    tags.extend(normalize_tag(tag) for tag in as_list(scene.get("long_tail_tags")))

    risk = as_dict(package.get("risk_controls"))
    tags.extend(normalize_tag(tag) for tag in as_list(risk.get("long_tail_tags")))

    env = as_dict(scene.get("environment"))
    weather = normalize_tag(env.get("weather", ""))
    if weather == "rain":
        tags.append("heavy_rain")
    elif weather in {"fog", "snow"}:
        tags.append(weather)
    if normalize_tag(env.get("visibility", "")) == "low":
        tags.append("low_visibility")

    return list(dict.fromkeys(tag for tag in tags if tag))


def control_values_match(values: Any, tag: str) -> bool:
    for value in as_list(values):
        if isinstance(value, dict):
            if any(text_has_tag(item, tag) for item in value.values()):
                return True
        elif text_has_tag(value, tag):
            return True
    return False


def has_prompt_or_visual_effect(scene: dict[str, Any], plan: dict[str, Any], package: dict[str, Any], tag: str) -> bool:
    text_items: list[Any] = []
    text_items.append(scene.get("prompt"))
    text_items.extend(as_list(plan.get("prompt_suffixes")))
    text_items.extend(as_list(plan.get("prompt_constraints")))
    text_items.append(as_dict(package.get("text_control")).get("prompt"))

    if any(text_has_tag(item, tag) for item in text_items if item):
        return True

    effects = as_list(plan.get("postprocess_effects"))
    if any(text_has_tag(effect, tag) for effect in effects):
        return True

    env_controls = as_dict(package.get("environment_controls"))
    if tag_family(tag) in {"weather", "visibility"}:
        return any(text_has_tag(value, tag) for value in env_controls.values())

    return False


def has_source_or_structural(scene: dict[str, Any], plan: dict[str, Any], package: dict[str, Any], tag: str) -> bool:
    controls = as_dict(plan.get("executable_controls"))
    risk_controls = as_dict(as_dict(package.get("risk_controls")).get("executable_controls"))

    structural_keys = [
        "objects",
        "motion",
        "maneuvers",
        "lane_relations",
        "target_object_support",
        "source_binding_requirements",
        "source_requirements",
        "source_selection",
    ]

    for source in [controls, risk_controls]:
        for key in structural_keys:
            if key in source and source.get(key):
                return True

    if as_list(package.get("actor_controls")):
        return True
    if as_list(package.get("motion_controls")) and tag_family(tag) == "motion":
        return True
    if as_list(package.get("relation_controls")) and tag_family(tag) == "lane_relation":
        return True

    structural = as_dict(package.get("structural_input_plan"))
    for key in ["boxes3d", "image_box", "image_hdmap", "labels"]:
        entry = as_dict(structural.get(key))
        if entry.get("override_ready") is True or entry.get("values"):
            return True

    trace = as_dict(package.get("trace_metadata"))
    if trace.get("tensor_control_ready") is True:
        return True

    trajectory = as_dict(package.get("trajectory_control_contract"))
    if str(trajectory.get("status", "")).startswith("runtime_connected"):
        return True

    actor_motion = as_dict(package.get("actor_motion_plan"))
    if as_dict(actor_motion.get("runtime_surface")).get("type"):
        return True

    return False


def has_evaluation(plan: dict[str, Any], package: dict[str, Any]) -> bool:
    controls = as_dict(plan.get("executable_controls"))
    risk_controls = as_dict(as_dict(package.get("risk_controls")).get("executable_controls"))

    if controls.get("perception_requirements") or risk_controls.get("perception_requirements"):
        return True
    if plan.get("evaluation_requirements"):
        return True
    if package.get("evaluation_requirements"):
        return True
    if package.get("perception_evaluation") or package.get("semantic_alignment_protocol"):
        return True
    return False


def channel_evidence(scene: dict[str, Any], plan: dict[str, Any], package: dict[str, Any], tag: str) -> dict[str, bool]:
    return {
        "prompt_or_visual_effect": has_prompt_or_visual_effect(scene, plan, package, tag),
        "source_or_structural": has_source_or_structural(scene, plan, package, tag),
        "evaluation": has_evaluation(plan, package),
    }


def build_longtail_control_coverage(
    scene_spec: Any,
    condition_plan: Any,
    condition_package: Any = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    scene = as_dict(scene_spec)
    plan = as_dict(condition_plan)
    package = unwrap_condition_package(condition_package)
    weights = weights or {}

    tag_rows = []
    weighted_score = 0.0
    total_weight = 0.0

    for tag in collect_tags(scene, plan, package):
        family = tag_family(tag)
        required = required_channels(tag)
        channels = channel_evidence(scene, plan, package, tag)
        matched = [name for name in required if channels.get(name)]
        missing = [name for name in required if not channels.get(name)]
        gamma = len(matched) / float(len(required)) if required else 1.0
        alpha = float(weights.get(tag, weights.get(family, 1.0)))

        weighted_score += alpha * gamma
        total_weight += alpha

        tag_rows.append(
            {
                "tag": tag,
                "family": family,
                "alpha": alpha,
                "gamma": round(gamma, 6),
                "covered": not missing,
                "required_channels": required,
                "matched_channels": matched,
                "missing_channels": missing,
                "channels": channels,
            }
        )

    score = weighted_score / total_weight if total_weight else 1.0

    return {
        "schema_version": SCHEMA_VERSION,
        "score": round(score, 6),
        "tag_count": len(tag_rows),
        "covered_tag_count": sum(1 for row in tag_rows if row["covered"]),
        "tags": tag_rows,
        "claim_boundary": {
            "longtail_control_coverage_is_not_video_semantic_success": True,
            "prompt_keyword_alone_is_not_executable_control_for_object_or_motion": True,
            "coverage_requires_declared_control_or_evaluation_channels": True,
        },
    }
