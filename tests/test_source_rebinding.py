from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import Diagnosis, DriveLoopRequest, Evaluation

FAILURE = Evaluation(0.1, {}, Diagnosis(False, ["target_object_not_detected"], []))


def test_rebinding_triggers_after_structural_escalation():
    refiner = RuleBasedRefiner()
    request = DriveLoopRequest(prompt="a motorcycle changes lane")
    r1 = refiner.refine(request, FAILURE)
    assert "source_rebinding" not in r1.condition  # level 1: structural escalation first
    r2 = refiner.refine(DriveLoopRequest(prompt=r1.prompt, condition=r1.condition), FAILURE)
    assert r2.condition["source_rebinding"]["candidate_offset"] == 1  # level 2: source rebinding
    r3 = refiner.refine(DriveLoopRequest(prompt=r2.prompt, condition=r2.condition), FAILURE)
    assert r3.condition["source_rebinding"]["candidate_offset"] == 2


def test_rebinding_not_added_for_non_perception_failure():
    refiner = RuleBasedRefiner()
    evaluation = Evaluation(0.1, {}, Diagnosis(False, ["low_detector_confidence"], []))
    refinement = refiner.refine(DriveLoopRequest(prompt="a motorcycle scene"), evaluation)
    assert "source_rebinding" not in refinement.condition
