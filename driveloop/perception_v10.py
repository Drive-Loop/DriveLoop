"""v10a perception scoring (offline candidate protocol).

Stage 1 of the v10 evaluator redesign (2026-07-13 v10 probe record):
the injected actor flips between motorcycle and person under yolov8x
on 256x448 night crops, so the v9 single-class filter undercounts
rendered evidence. v10a expands the target label set to a fixed
super-class for existence, support and track evidence, and reports
class fidelity (share of original-target labels among super-class
detections in the selected view) as a separate metric. Differential
baseline subtraction and view selection are unchanged from v9.

Offline-only until adoption is recorded: the runtime pipeline keeps
constructing the v9 composite evaluator. Labels are compared in
lowercase detector vocabulary (yolov8x: motorcycle, bicycle, person).
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from driveloop.composite_perception import CompositePerceptionVideoEvaluator
from driveloop.schema import Evaluation, Generation

SUPERCLASS_EXPANSION: Dict[str, Set[str]] = {
    "motorcycle": {"motorcycle", "bicycle", "person"},
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

    @staticmethod
    def class_fidelity(
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
                if label in superclass_labels:
                    total += 1
                    if label in original_labels:
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
