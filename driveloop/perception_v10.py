"""v10 perception scoring (offline candidate protocol).

Stage 1 (v10a, 2026-07-13 v10 probe record): the injected actor flips
between motorcycle and person under yolov8x on 256x448 night crops,
so the v9 single-class filter undercounts rendered evidence. v10a
expands the target label set to a fixed super-class for existence,
support and track evidence, and reports class fidelity (share of
original-target labels among super-class detections in the selected
view) as a separate metric.

Stage 2 (v10b, 2026-07-13 v10a rescore record): super-class pooling
over all six views admits scene-pedestrian residue (m4 false-positive
mode), so v10b hard-restricts the scored views to the
maneuver-relevant set: target cams plus approach-side neighbors
derived from the surface plan's lateral_side. Cases without a surface
plan are unmeasurable under v10b and score 0 with an explicit flag.

Labels are compared in the evaluator's NORMALIZED vocabulary
(person -> pedestrian, bike/cyclist -> bicycle), matching the filter
in PerceptionVideoEvaluator.evaluate; raw detector labels are
normalized before any membership test. Offline-only until adoption
is recorded: the runtime pipeline keeps constructing the v9
composite evaluator.
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from driveloop.composite_perception import CompositePerceptionVideoEvaluator
from driveloop.schema import Diagnosis, Evaluation, Generation

SUPERCLASS_EXPANSION: Dict[str, Set[str]] = {
    "motorcycle": {"motorcycle", "bicycle", "pedestrian"},
}

APPROACH_SIDE_NEIGHBOR_CAMS: Dict[float, Tuple[str, str]] = {
    -1.0: ("cam_front_left", "cam_back_left"),
    1.0: ("cam_front_right", "cam_back_right"),
}


def expand_labels(labels: Set[str]) -> Set[str]:
    expanded = set(labels)
    for label in labels:
        expanded |= SUPERCLASS_EXPANSION.get(label, set())
    return expanded


class SuperclassCompositePerceptionEvaluator(CompositePerceptionVideoEvaluator):
    """v10a: super-class evidence pooling with class-fidelity reporting."""

    def _resolve_target_labels(self, generation: Generation) -> set:
        base_labels = super()._resolve_target_labels(generation)
        self._v10_original_labels = set(base_labels)
        return expand_labels(set(base_labels))

    def _direction_label_set(self, category: str) -> set:
        return expand_labels(super()._direction_label_set(category))

    def class_fidelity(
        self,
        view_centers: List,
        original_labels: Set[str],
        superclass_labels: Set[str],
    ) -> Tuple[float, int, int]:
        total = 0
        original = 0
        for frame_dets in view_centers or []:
            if not frame_dets:
                continue
            for label, _center in frame_dets:
                normalized = self._normalize_label(str(label))
                if normalized in superclass_labels:
                    total += 1
                    if normalized in original_labels:
                        original += 1
        share = round(original / total, 6) if total else 0.0
        return share, original, total

    def evaluate(self, generation: Generation) -> Evaluation:
        self._v10_original_labels = set()
        evaluation = super().evaluate(generation)
        metrics = dict(evaluation.metrics)
        selected = int(metrics.get("perception_selected_view", -1))
        original_labels = set(getattr(self, "_v10_original_labels", set()) or set())
        superclass_labels = expand_labels(original_labels)
        share, original, total = self.class_fidelity(
            getattr(self, "_view_centers", {}).get(selected, []),
            original_labels,
            superclass_labels,
        )
        metrics["perception_scorer_version"] = 10.0
        metrics["perception_class_fidelity"] = share
        metrics["perception_superclass_detection_count"] = float(total)
        metrics["perception_original_class_detection_count"] = float(original)
        return Evaluation(evaluation.score, metrics, evaluation.diagnosis)


class ManeuverViewRestrictedSuperclassEvaluator(SuperclassCompositePerceptionEvaluator):
    """v10b: v10a plus a hard restriction of the scored views to the
    maneuver-relevant set (target cams + approach-side neighbors)."""

    def _lateral_side(self, metadata) -> float:
        plan = (
            metadata.get("dd2_override_candidate_plan")
            if isinstance(metadata, dict)
            else None
        )
        surface = plan.get("actor_motion_surface_plan") if isinstance(plan, dict) else None
        if not isinstance(surface, dict):
            return 0.0
        try:
            return float(surface.get("lateral_side") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _views_to_evaluate(self, metadata) -> list:
        allowed = set(self._target_view_indices(metadata))
        side = self._lateral_side(metadata)
        if side:
            key = 1.0 if side > 0 else -1.0
            for cam in APPROACH_SIDE_NEIGHBOR_CAMS.get(key, ()):
                if cam in self.layout.cam_order:
                    allowed.add(self.layout.cam_order.index(cam))
        return sorted(allowed)

    def evaluate(self, generation: Generation) -> Evaluation:
        allowed = self._views_to_evaluate(generation.metadata)
        if not allowed:
            return Evaluation(
                0.0,
                {
                    "perception_scorer_version": 10.1,
                    "perception_view_restriction_active": 1.0,
                    "perception_allowed_view_count": 0.0,
                    "perception_view_restriction_unresolved": 1.0,
                },
                Diagnosis(
                    False,
                    ["no_maneuver_view_restriction_resolvable"],
                    [
                        "provide actor_motion_surface_plan with target cams"
                        " or a lateral side"
                    ],
                ),
            )
        evaluation = super().evaluate(generation)
        metrics = dict(evaluation.metrics)
        metrics["perception_scorer_version"] = 10.1
        metrics["perception_view_restriction_active"] = 1.0
        metrics["perception_allowed_view_count"] = float(len(allowed))
        return Evaluation(evaluation.score, metrics, evaluation.diagnosis)
