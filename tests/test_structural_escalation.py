from driveloop.actor_motion import build_actor_motion_plan, build_actor_motion_surface_plan
from driveloop.backends.mock import MockGenerationBackend
from driveloop.evaluators import BaseEvaluator
from driveloop.refiner import RuleBasedRefiner
from driveloop.runner import DriveLoopRunner
from driveloop.schema import Diagnosis, DriveLoopConfig, DriveLoopRequest, Evaluation

ACTORS = [{"actor_id": "actor_01", "category": "motorcycle", "source_category": "motorcycle"}]
FAILURE = Evaluation(0.1, {}, Diagnosis(False, ["target_object_not_detected"], []))


def _plan(escalation=None):
    controls = {"structural_escalation": escalation} if escalation else {}
    return build_actor_motion_plan(
        actor_controls=ACTORS,
        relations=["left"],
        motion_primitives=["lane_change"],
        executable_controls=controls,
    )


def test_surface_plan_unchanged_without_escalation():
    surface = build_actor_motion_surface_plan(_plan())
    assert surface["escalation_applied"]["proximity_scale"] == 1.0
    assert surface["escalation_applied"]["size_scale"] == 1.0
    assert surface["escalation_applied"]["lateral_base_m"] == 3.5  # left default 3.5/20 (2026-07-08 record)
    assert surface["escalation_applied"]["longitudinal_base_m"] == 20.0  # left default 3.5/20 (2026-07-08 record)
    box = surface["per_frame_boxes3d"][0]["box3d"]
    assert abs(box[2] - (20.0 + 1.8)) < 1e-6  # left lon base 20.0 (2026-07-08 record)


def test_surface_plan_applies_proximity_and_size():
    surface = build_actor_motion_surface_plan(
        _plan({"proximity_scale": 0.5, "size_scale": 1.5})
    )
    assert surface["escalation_applied"]["proximity_scale"] == 0.5
    box = surface["per_frame_boxes3d"][0]["box3d"]
    assert abs(box[2] - (10.0 + 1.8)) < 1e-6  # closer (left lon base 20.0 * proximity 0.5)
    assert abs(box[3] - 0.8 * 1.5) < 1e-6  # larger


def test_refiner_increments_escalation_level():
    refiner = RuleBasedRefiner()
    r1 = refiner.refine(DriveLoopRequest(prompt="a motorcycle changes lane"), FAILURE)
    assert r1.condition["structural_escalation"]["level"] == 1
    r2 = refiner.refine(
        DriveLoopRequest(prompt=r1.prompt, condition=r1.condition), FAILURE
    )
    assert r2.condition["structural_escalation"]["level"] == 2
    assert r1.condition["structural_escalation"]["size_scale"] == 1.5
    assert r2.condition["structural_escalation"]["proximity_scale"] == 1.0


class AlwaysFail(BaseEvaluator):
    def evaluate(self, generation):
        return FAILURE


def test_runner_carries_escalation_into_next_condition_plan(tmp_path):
    runner = DriveLoopRunner(
        backend=MockGenerationBackend(output_dir=tmp_path / "mock"),
        evaluator=AlwaysFail(),
        config=DriveLoopConfig(max_iterations=3, output_dir=tmp_path, use_task_utility=True),
    )
    result = runner.run(DriveLoopRequest(prompt="a motorcycle changes lane from the left"))
    plan2 = result.attempt_history[1].long_tail_condition_plan
    assert plan2.executable_controls["structural_escalation"]["level"] == 1
    plan3 = result.attempt_history[2].long_tail_condition_plan
    assert plan3.executable_controls["structural_escalation"]["level"] == 2


def test_absolute_geometry_bases_override_proximity():
    surface = build_actor_motion_surface_plan(
        _plan({"lateral_base_m": 3.2, "longitudinal_base_m": 12.0})
    )
    box = surface["per_frame_boxes3d"][0]["box3d"]
    # relations ["left"]: side=-1, magnitude starts at +1.6
    # box x = side*base + side*magnitude = -(3.2 + 1.6)
    assert abs(box[0] - (-(3.2 + 1.6))) < 1e-6
    # lane_change longitudinal start offset is 1.8
    assert abs(box[2] - (12.0 + 1.8)) < 1e-6
