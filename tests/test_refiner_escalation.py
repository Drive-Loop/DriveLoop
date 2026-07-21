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


def test_first_round_produces_a_new_prompt_then_synthetic_rung_reverts():
    refiner = RuleBasedRefiner()
    original = "night street, a motorcycle changes lane from the left into the ego lane"
    r1 = refiner.refine(DriveLoopRequest(prompt=original), PERCEPTION_FAILURE)
    assert r1.prompt != original  # round 1: text refinement engages
    r2 = refiner.refine(
        DriveLoopRequest(prompt=r1.prompt, condition=r1.condition), PERCEPTION_FAILURE
    )
    # cr9 ablation 2026-07-21: additions suppress the synthetic actor;
    # the synthetic rung must return the original user prompt.
    assert r2.prompt == original
    assert r2.condition["synthetic_trajectory_escalation"]["level"] == 2
    assert r2.condition["driveloop_original_prompt"] == original


def test_escalation_ladder_engages_when_structural_escalation_disabled():
    refiner = RuleBasedRefiner()
    refiner.STRUCTURAL_ESCALATION_ENABLED = False
    prompt = "a motorcycle scene"
    for _ in range(2):
        prompt = refiner.refine(DriveLoopRequest(prompt=prompt), PERCEPTION_FAILURE).prompt
    assert any(
        e.format(category="motorcycle").lower() in prompt.lower()
        for e in refiner.PERCEPTION_ESCALATION
    )


def test_no_duplicate_additions_in_prompt():
    refiner = RuleBasedRefiner()
    refiner.STRUCTURAL_ESCALATION_ENABLED = False
    prompt = "a motorcycle scene"
    for _ in range(3):
        prompt = refiner.refine(DriveLoopRequest(prompt=prompt), PERCEPTION_FAILURE).prompt
    low = prompt.lower()
    fragment = "the target actor remains large, visible, and unoccluded"
    assert low.count(fragment) == 1
