from __future__ import annotations

from driveloop.composite_perception import CompositePerceptionVideoEvaluator
from driveloop.perception_v10 import (
    ManeuverViewRestrictedSuperclassEvaluator,
    SuperclassCompositePerceptionEvaluator,
)
from driveloop.schema import Generation


def _metadata(target_cams, side):
    return {
        "dd2_override_candidate_plan": {
            "actor_motion_surface_plan": {
                "maneuver": "cut_in",
                "lateral_side": side,
                "target_cam_types": target_cams,
            }
        }
    }


def test_default_hook_scores_every_view():
    assert CompositePerceptionVideoEvaluator()._views_to_evaluate({}) == [0, 1, 2, 3, 4, 5]
    assert SuperclassCompositePerceptionEvaluator()._views_to_evaluate({}) == [0, 1, 2, 3, 4, 5]


def test_left_maneuver_restricts_to_front_and_left_views():
    evaluator = ManeuverViewRestrictedSuperclassEvaluator()
    assert evaluator._views_to_evaluate(_metadata(["cam_front"], -1.0)) == [0, 1, 5]


def test_right_maneuver_restricts_to_front_and_right_views():
    evaluator = ManeuverViewRestrictedSuperclassEvaluator()
    assert evaluator._views_to_evaluate(_metadata(["cam_front"], 1.0)) == [1, 2, 3]


def test_missing_surface_plan_yields_no_views_and_zero_score():
    evaluator = ManeuverViewRestrictedSuperclassEvaluator()
    generation = Generation(
        iteration=0, prompt="a motorcycle cuts in", artifacts={}, metadata={}
    )
    assert evaluator._views_to_evaluate({}) == []
    evaluation = evaluator.evaluate(generation)
    assert evaluation.score == 0.0
    assert evaluation.metrics["perception_view_restriction_unresolved"] == 1.0
    assert evaluation.diagnosis.passed is False


def test_restriction_metrics_reported_on_allowed_path():
    evaluator = ManeuverViewRestrictedSuperclassEvaluator()
    generation = Generation(
        iteration=0,
        prompt="a motorcycle cuts in",
        artifacts={},
        metadata=_metadata(["cam_front"], -1.0),
    )
    evaluation = evaluator.evaluate(generation)
    assert evaluation.metrics["perception_view_restriction_active"] == 1.0
    assert evaluation.metrics["perception_allowed_view_count"] == 3.0
