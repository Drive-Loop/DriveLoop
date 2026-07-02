from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
        alignment_feedback: Optional[Dict[str, Any]] = None,
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
            alignment_feedback=alignment_feedback,
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
        alignment_feedback: Optional[Dict[str, Any]] = None,
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

        trace_metadata: Dict[str, Any] = {
            "structural_control_level": "runtime_surface_contract",
            "tensor_control_ready": False,
            "limitations": [
                "runtime_structural_surfaces_observed_not_overridden",
                "boxes3d_override_not_applied",
                "trajectory_tensor_control_not_connected",
                "actor_track_identity_not_observed",
                "hdmap_tensor_control_requires_explicit_verified_source",
            ],
        }
        if isinstance(alignment_feedback, dict) and alignment_feedback:
            trace_metadata["alignment_feedback"] = {
                "schema_version": alignment_feedback.get("schema_version"),
                "status": alignment_feedback.get("status"),
                "control_level": alignment_feedback.get("control_level", "text_feedback_only"),
                "failed_checks": list(alignment_feedback.get("failed_checks", [])),
                "requested_visual_constraints": list(
                    alignment_feedback.get("requested_visual_constraints", [])
                ),
                "claim_boundary": (
                    "Alignment feedback is carried for audit and text refinement only; "
                    "it is not verified tensor-level DD2 control."
                ),
            }

        trajectory_control_contract = self._build_trajectory_control_contract(
            actor_controls=actor_controls,
            relations=relations,
            motion_primitives=motion_primitives,
        )

        return {
            "schema_version": "dd2_executable_condition.v0",
            "target_backend": "drivedreamer2_runtime",
            "text_control": {
                "prompt": text_prompt,
            },
            "structural_input_plan": structural_input_plan,
            "trajectory_control_contract": trajectory_control_contract,
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
            "trace_metadata": trace_metadata,
        }

    def _build_trajectory_control_contract(
        self,
        actor_controls: List[Dict[str, Any]],
        relations: List[str],
        motion_primitives: List[str],
    ) -> Dict[str, Any]:
        requested_motions = list(dict.fromkeys(motion_primitives))
        requested_relations = list(dict.fromkeys(relations))
        requested_maneuvers = []
        if "lane_change" in requested_motions or "cut_in" in requested_motions:
            requested_maneuvers.append(
                {
                    "type": "lane_change_or_cut_in",
                    "source": "motion_primitives",
                    "required_evidence": [
                        "per_frame_actor_identity",
                        "per_frame_actor_boxes3d",
                        "lateral_displacement_across_frames",
                        "lane_geometry_or_hdmap_reference",
                    ],
                }
            )

        return {
            "schema_version": "driveloop_trajectory_control_contract.v0",
            "status": "not_runtime_connected",
            "control_level": "contract_only",
            "actor_refs": [actor["actor_id"] for actor in actor_controls],
            "requested_motions": requested_motions,
            "requested_relations": requested_relations,
            "requested_maneuvers": requested_maneuvers,
            "required_runtime_surfaces": [
                "actor_track_identity",
                "per_frame_actor_boxes3d",
                "velocity_or_displacement_tensor",
                "hdmap_lane_geometry",
                "temporal_consistency_audit",
            ],
            "current_runtime_surfaces": {
                "boxes3d": "runtime_dataset_surface_observed_not_override",
                "image_box": "derived_from_runtime_boxes3d_canvas_not_target_control",
                "velocities": "dataset_surface_observed_not_dd2_condition_tensor",
                "actor_track_identity": "not_observed",
                "hdmap_lane_geometry": "runtime_dataset_baseline",
            },
            "claim_boundary": (
                "This contract records the evidence required for trajectory control; "
                "it is not connected to DD2 runtime tensors and cannot prove lane-change video semantics."
            ),
        }

    def _build_mini_structural_input_plan(
        self,
        text_prompt: str,
        actor_controls: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        labels = list(dict.fromkeys(actor["category"] for actor in actor_controls))

        return {
            "target_dataset": "drivedreamer2_runtime",
            "control_level": "runtime_surface_contract",
            "scene_description": {
                "source": "text_control.prompt",
                "value": text_prompt,
            },
            "labels": {
                "source": "actor_controls.category",
                "values": labels,
            },
            "image_hdmap": {
                "source": "runtime_dataset_baseline",
                "override_ready": False,
                "reason": "no_verified_hdmap_override_source",
            },
            "image_box": {
                "source": "derived_from_runtime_boxes3d_canvas",
                "override_ready": False,
                "reason": "derived_from_baseline_runtime_boxes3d_not_target_override",
            },
            "boxes3d": {
                "source": "runtime_dataset_baseline",
                "override_ready": False,
                "reason": "target_boxes3d_override_not_implemented",
            },
            "limitations": [
                "boxes3d_override_not_applied",
                "trajectory_tensor_override_not_implemented",
                "actor_track_identity_not_observed",
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
