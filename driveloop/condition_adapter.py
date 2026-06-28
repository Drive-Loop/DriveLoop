from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from driveloop.schema import LongTailConditionPlan, SceneSpecification


@dataclass
class DriveDreamer2Condition:
    """Intermediate condition plan before converting to DriveDreamer-2 tensors."""

    text_prompt: str
    environment: Dict[str, str]
    actors: List[Dict[str, Any]] = field(default_factory=list)
    relations: List[str] = field(default_factory=list)
    motion_primitives: List[str] = field(default_factory=list)
    long_tail_tags: List[str] = field(default_factory=list)
    executable_controls: Dict[str, Any] = field(default_factory=dict)
    prompt_suffixes: List[str] = field(default_factory=list)
    executable_condition: Dict[str, Any] = field(default_factory=dict)


class DriveDreamer2ConditionAdapter:
    """Maps DriveLoop scene specifications to a DD2-oriented intermediate condition.

    The adapter emits an executable contract that the DD2 backend can turn into
    tensor overrides. Box tensors are supported through audited overrides; HDMap
    control remains explicit-only until a verified map source is available.
    """

    def build(
        self,
        spec: SceneSpecification,
        condition_plan: LongTailConditionPlan,
    ) -> DriveDreamer2Condition:
        text_parts = [spec.prompt]
        text_parts.extend(condition_plan.prompt_suffixes)

        text_prompt = ", ".join(part.strip().rstrip(".") for part in text_parts if part).strip() + "."
        environment = dict(spec.environment)
        actors = [
            {
                "category": obj.category,
                "attributes": dict(obj.attributes),
            }
            for obj in spec.objects
        ]
        relations = list(spec.relations)
        motion_primitives = list(spec.motion_primitives)
        long_tail_tags = list(condition_plan.tags)
        executable_controls = dict(condition_plan.executable_controls)

        executable_condition = self._build_executable_condition(
            text_prompt=text_prompt,
            environment=environment,
            actors=actors,
            relations=relations,
            motion_primitives=motion_primitives,
            long_tail_tags=long_tail_tags,
            executable_controls=executable_controls,
        )

        return DriveDreamer2Condition(
            text_prompt=text_prompt,
            environment=environment,
            actors=actors,
            relations=relations,
            motion_primitives=motion_primitives,
            long_tail_tags=long_tail_tags,
            executable_controls=executable_controls,
            prompt_suffixes=list(condition_plan.prompt_suffixes),
            executable_condition=executable_condition,
        )

    def _build_executable_condition(
        self,
        text_prompt: str,
        environment: Dict[str, str],
        actors: List[Dict[str, Any]],
        relations: List[str],
        motion_primitives: List[str],
        long_tail_tags: List[str],
        executable_controls: Dict[str, Any],
    ) -> Dict[str, Any]:
        actor_controls = [
            {
                "actor_id": f"actor_{index:02d}",
                "category": self._canonical_actor_category(str(actor["category"])),
                "source_category": actor["category"],
                "attributes": dict(actor.get("attributes", {})),
                "source": "scene_specification",
            }
            for index, actor in enumerate(actors)
        ]

        structural_input_plan = self._build_mini_structural_input_plan(
            text_prompt=text_prompt,
            actor_controls=actor_controls,
        )

        return {
            "schema_version": "dd2_executable_condition.v0",
            "target_backend": "drivedreamer2_mini",
            "text_control": {
                "prompt": text_prompt,
            },
            "structural_input_plan": structural_input_plan,
            "environment_controls": {
                "weather": environment.get("weather", "unspecified"),
                "lighting": environment.get("lighting", "unspecified"),
                "visibility": environment.get("visibility", "normal"),
            },
            "actor_controls": actor_controls,
            "relation_controls": list(relations),
            "motion_controls": list(motion_primitives),
            "risk_controls": {
                "long_tail_tags": list(long_tail_tags),
                "executable_controls": dict(executable_controls),
            },
            "trace_metadata": {
                "structural_control_level": "tensor_override_contract",
                "tensor_control_ready": True,
                "limitations": [
                    "mini_dataset_structural_inputs_required",
                    "trajectory_tensor_control_not_connected",
                    "hdmap_tensor_control_requires_explicit_verified_source",
                ],
            },
        }

    def _build_mini_structural_input_plan(
        self,
        text_prompt: str,
        actor_controls: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        labels = list(dict.fromkeys(actor["category"] for actor in actor_controls))

        return {
            "target_dataset": "drivedreamer2_mini",
            "control_level": "tensor_override_contract",
            "scene_description": {
                "source": "text_control.prompt",
                "value": text_prompt,
            },
            "labels": {
                "source": "actor_controls.category",
                "values": labels,
            },
            "image_hdmap": {
                "source": "mini_dataset_baseline",
                "override_ready": False,
                "reason": "no_verified_hdmap_override_source",
            },
            "image_box": {
                "source": "derived_from_boxes3d_override",
                "override_ready": True,
            },
            "boxes3d": {
                "source": "executable_condition_tensor_override",
                "override_ready": True,
            },
            "limitations": [
                "trajectory_tensor_override_not_implemented",
                "hdmap_tensor_override_requires_explicit_verified_source",
            ],
        }

    def _canonical_actor_category(self, category: str) -> str:
        aliases = {
            "cyclist": "bicycle",
            "cyclists": "bicycle",
            "bike": "bicycle",
            "vehicle": "car",
            "vehicles": "car",
            "delivery_van": "car",
            "van": "car",
            "traffic_barrier": "barrier",
            "traffic_barrel": "barrier",
            "person": "pedestrian",
            "people": "pedestrian",
        }
        normalized = category.lower().strip()
        return aliases.get(normalized, normalized)
