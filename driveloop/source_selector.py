from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol

from driveloop.schema import DriveLoopRequest, LongTailConditionPlan, SceneSpecification
from driveloop.source_sample_binding import build_source_sample_binding
from driveloop.source_ranking import rank_source_candidates


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


@dataclass(frozen=True)
class SourceSelection:
    schema_version: str = "driveloop_source_selection.v0"
    requested: bool = False
    ready: bool = False
    selector_type: str = "none"
    selector: dict[str, Any] = field(default_factory=dict)
    binding: dict[str, Any] = field(default_factory=dict)
    backend_hints: dict[str, Any] = field(default_factory=dict)
    diagnosis: dict[str, Any] = field(default_factory=dict)
    claim_boundary: dict[str, Any] = field(default_factory=lambda: {
        "source_selection_is_not_gpu_approval": True,
        "source_selection_is_not_video_semantic_success": True,
        "semantic_success_requires_generation_and_evaluation": True,
    })


class BaseSourceSelector(Protocol):
    def select(
        self,
        request: DriveLoopRequest,
        scene_specification: SceneSpecification,
        condition_plan: LongTailConditionPlan,
    ) -> SourceSelection:
        ...


class NoOpSourceSelector:
    def select(
        self,
        request: DriveLoopRequest,
        scene_specification: SceneSpecification,
        condition_plan: LongTailConditionPlan,
    ) -> SourceSelection:
        return SourceSelection(
            requested=False,
            ready=False,
            selector_type="none",
            diagnosis={
                "status": "not_requested",
                "reason": "no_source_selector_configured",
                "suggested_actions": [],
            },
        )


class DD2SourceSelector:
    def __init__(
        self,
        dataset_dir: str | Path,
        *,
        source_candidate_id: str | None = None,
        sample_token: str | None = None,
        scene_token: str | None = None,
        instance_token: str | None = None,
        identity_summary_path: str | Path | None = None,
        frame_num: int = 8,
        hz_factor: int = 3,
        video_split_rate: int = 1,
        multiview: bool = True,
    ) -> None:
        self.dataset_dir = Path(dataset_dir)
        self.source_candidate_id = source_candidate_id
        self.sample_token = sample_token
        self.scene_token = scene_token
        self.instance_token = instance_token
        self.identity_summary_path = Path(identity_summary_path) if identity_summary_path else None
        self.frame_num = frame_num
        self.hz_factor = hz_factor
        self.video_split_rate = video_split_rate
        self.multiview = multiview

    def select(
        self,
        request: DriveLoopRequest,
        scene_specification: SceneSpecification,
        condition_plan: LongTailConditionPlan,
    ) -> SourceSelection:
        metadata = _as_dict(request.metadata)
        condition = _as_dict(request.condition)
        config = _as_dict(metadata.get("source_selection"))

        selector = {
            "source_candidate_id": _first_value(
                config.get("source_candidate_id"),
                metadata.get("source_candidate_id"),
                condition.get("source_candidate_id"),
                self.source_candidate_id,
            ),
            "sample_token": _first_value(
                config.get("sample_token"),
                metadata.get("sample_token"),
                condition.get("sample_token"),
                self.sample_token,
            ),
            "scene_token": _first_value(
                config.get("scene_token"),
                metadata.get("scene_token"),
                condition.get("scene_token"),
                self.scene_token,
            ),
            "instance_token": _first_value(
                config.get("instance_token"),
                metadata.get("instance_token"),
                condition.get("instance_token"),
                self.instance_token,
            ),
            "identity_summary_path": _first_value(
                config.get("identity_summary_path"),
                config.get("source_identity_summary_path"),
                metadata.get("source_identity_summary_path"),
                condition.get("source_identity_summary_path"),
                str(self.identity_summary_path) if self.identity_summary_path else None,
            ),
        }

        ranking = None
        candidates = config.get("candidates") or metadata.get("source_candidates")
        if isinstance(candidates, list) and candidates:
            ranking = rank_source_candidates(candidates, scene_specification, condition_plan)
            if not selector.get("source_candidate_id"):
                selector["source_candidate_id"] = ranking.get("best_candidate_id")

        binding = build_source_sample_binding(
            self.dataset_dir,
            source_candidate_id=selector.get("source_candidate_id"),
            sample_token=selector.get("sample_token"),
            scene_token=selector.get("scene_token"),
            instance_token=selector.get("instance_token"),
            identity_summary_path=selector.get("identity_summary_path"),
            frame_num=self.frame_num,
            hz_factor=self.hz_factor,
            video_split_rate=self.video_split_rate,
            multiview=self.multiview,
        )
        requested = binding.get("requested") is True
        ready = binding.get("ready") is True

        backend_hints = {
            key: value
            for key, value in {
                "source_candidate_id": selector.get("source_candidate_id"),
                "sample_token": selector.get("sample_token"),
                "scene_token": selector.get("scene_token"),
                "instance_token": selector.get("instance_token"),
                "source_identity_summary_path": selector.get("identity_summary_path"),
            }.items()
            if value not in (None, "")
        }

        reason = binding.get("reason")
        diagnosis = {
            "status": "ready" if ready else ("failed" if requested else "not_requested"),
            "reason": reason,
            "suggested_actions": self._suggested_actions(requested, ready, reason),
        }
        if ranking is not None:
            diagnosis["source_ranking"] = ranking

        claim_boundary = {
            "source_selection_is_not_gpu_approval": True,
            "source_selection_is_not_video_semantic_success": True,
            "source_binding_is_not_semantic_success": True,
            "semantic_success_requires_generation_and_evaluation": True,
            "source_ranking_is_metadata_compatibility_only": ranking is not None,
        }
        binding_claim = binding.get("claim_boundary")
        if isinstance(binding_claim, dict):
            claim_boundary.update(binding_claim)

        return SourceSelection(
            requested=requested,
            ready=ready,
            selector_type="dd2_source_sample_binding",
            selector={
                **selector,
                "dataset_dir": str(self.dataset_dir),
                "frame_num": self.frame_num,
                "hz_factor": self.hz_factor,
                "video_split_rate": self.video_split_rate,
                "multiview": self.multiview,
            },
            binding=binding,
            backend_hints=backend_hints,
            diagnosis=diagnosis,
            claim_boundary=claim_boundary,
        )

    def _suggested_actions(self, requested: bool, ready: bool, reason: str | None) -> list[str]:
        if not requested:
            return []
        if ready:
            return []
        if reason == "dd2_labels_data_missing":
            return ["provide a DD2 runtime dataset with labels/data.pkl"]
        if reason == "no_dd2_candidate_contains_requested_source_tokens":
            return ["select another source candidate or rebuild the runtime dataset for the requested source tokens"]
        return ["inspect source selector inputs and runtime dataset compatibility"]
