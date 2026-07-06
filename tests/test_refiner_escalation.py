from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import Diagnosis, DriveLoopRequest, Evaluation


PERCEPTION_FAILURE = Evaluation(
    0.0,
    {},
    Diagnosis(
        False,
        [
            "target_object_not_detected",
            "low_detection_coverage",
            "low_detector_confidence",
            "unstable_track_coverage",
            "identity_inconsistent",
        ],
        [],
    ),
)


def test_each_round_produces_a_new_prompt():
    refiner = RuleBasedRefiner()
    prompt = "night street, a motorcycle changes lane from the left into the ego lane"
    seen = {prompt}
    for _ in range(4):
        refinement = refiner.refine(DriveLoopRequest(prompt=prompt), PERCEPTION_FAILURE)
        assert refinement.prompt not in seen, "refiner saturated: prompt did not change"
        seen.add(refinement.prompt)
        prompt = refinement.prompt


def test_escalation_ladder_engages_when_base_additions_exhausted():
    refiner = RuleBasedRefiner()
    prompt = "a motorcycle scene"
    for _ in range(2):
        prompt = refiner.refine(DriveLoopRequest(prompt=prompt), PERCEPTION_FAILURE).prompt
    assert any(e.lower() in prompt.lower() for e in refiner.PERCEPTION_ESCALATION)


def test_no_duplicate_additions_in_prompt():
    refiner = RuleBasedRefiner()
    prompt = "a motorcycle scene"
    for _ in range(3):
        prompt = refiner.refine(DriveLoopRequest(prompt=prompt), PERCEPTION_FAILURE).prompt
    low = prompt.lower()
    fragment = "the target actor remains large, visible, and unoccluded"
    assert low.count(fragment) == 1
