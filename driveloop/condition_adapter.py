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


class DriveDreamer2ConditionAdapter:
    """Maps DriveLoop scene specifications to a DD2-oriented intermediate condition.

    This first version intentionally does not synthesize DD2 tensors yet.
    It defines the contract needed before implementing actor boxes, HDMap/lane
    controls, trajectories, and weather/light conditioning.
    """

    def build(
        self,
        spec: SceneSpecification,
        condition_plan: LongTailConditionPlan,
    ) -> DriveDreamer2Condition:
        text_parts = [spec.prompt]
        text_parts.extend(condition_plan.prompt_suffixes)

        return DriveDreamer2Condition(
            text_prompt=", ".join(part.strip().rstrip(".") for part in text_parts if part).strip() + ".",
            environment=dict(spec.environment),
            actors=[
                {
                    "category": obj.category,
                    "attributes": dict(obj.attributes),
                }
                for obj in spec.objects
            ],
            relations=list(spec.relations),
            motion_primitives=list(spec.motion_primitives),
            long_tail_tags=list(condition_plan.tags),
            executable_controls=dict(condition_plan.executable_controls),
            prompt_suffixes=list(condition_plan.prompt_suffixes),
        )
