from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import Diagnosis, DriveLoopRequest, Evaluation

FAILURE = Evaluation(0.1, {}, Diagnosis(False, ["target_object_not_detected"], []))


def test_synthetic_escalation_triggers_after_structural_escalation():
    refiner = RuleBasedRefiner()
    request = DriveLoopRequest(prompt="a motorcycle changes lane")
    r1 = refiner.refine(request, FAILURE)
    assert "synthetic_trajectory_escalation" not in r1.condition  # level 1 first
    r2 = refiner.refine(DriveLoopRequest(prompt=r1.prompt, condition=r1.condition), FAILURE)
    assert r2.condition["synthetic_trajectory_escalation"]["level"] == 2
    r3 = refiner.refine(DriveLoopRequest(prompt=r2.prompt, condition=r2.condition), FAILURE)
    assert r3.condition["synthetic_trajectory_escalation"]["level"] == 3


def test_synthetic_escalation_not_added_below_level_two():
    refiner = RuleBasedRefiner()
    evaluation = Evaluation(0.1, {}, Diagnosis(False, ["low_detector_confidence"], []))
    refinement = refiner.refine(DriveLoopRequest(prompt="a motorcycle scene"), evaluation)
    assert "synthetic_trajectory_escalation" not in refinement.condition


def test_ablation_gate_disables_structural_and_synthetic_escalation():
    refiner = RuleBasedRefiner()
    refiner.STRUCTURAL_ESCALATION_ENABLED = False
    request = DriveLoopRequest(prompt="a motorcycle changes lane")
    refinement = refiner.refine(request, FAILURE)
    assert "structural_escalation" not in refinement.condition
    assert "synthetic_trajectory_escalation" not in refinement.condition


def test_synthetic_escalation_uses_close_range_for_small_actors():
    refiner = RuleBasedRefiner()
    r1 = refiner.refine(DriveLoopRequest(prompt="a motorcycle changes lane"), FAILURE)
    r2 = refiner.refine(DriveLoopRequest(prompt=r1.prompt, condition=r1.condition), FAILURE)
    assert r2.condition["structural_escalation"]["longitudinal_base_m"] == 9.0


def test_synthetic_escalation_keeps_default_range_for_large_actors():
    refiner = RuleBasedRefiner()
    r1 = refiner.refine(DriveLoopRequest(prompt="a truck cuts in from the left"), FAILURE)
    r2 = refiner.refine(DriveLoopRequest(prompt=r1.prompt, condition=r1.condition), FAILURE)
    assert "longitudinal_base_m" not in r2.condition["structural_escalation"]


def test_disable_synthetic_rung_env_flag(monkeypatch):
    monkeypatch.setenv("DRIVELOOP_DISABLE_SYNTHETIC_RUNG", "1")
    refiner = RuleBasedRefiner()
    r1 = refiner.refine(
        DriveLoopRequest(prompt="a truck cuts in from the left"), FAILURE
    )
    r2 = refiner.refine(
        DriveLoopRequest(prompt=r1.prompt, condition=r1.condition), FAILURE
    )
    assert "synthetic_trajectory_escalation" not in r2.condition
    assert r2.condition["structural_escalation"]["level"] == 2
