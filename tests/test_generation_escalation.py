"""v9 finding (2026-07-09): under real-track ego injection and DD2's
canned-prompt collapse, prompt additions and synthetic-geometry
escalation never reach the conditioning, so closed-loop attempts were
bit-identical under a frozen seed. The generation-parameter lever
(seed offset per attempt + steps/guidance escalation) must reach the
DD2 tester env."""
from driveloop.backends.drivedreamer2 import DriveDreamer2Backend
from driveloop.refiner import RuleBasedRefiner
from driveloop.schema import Diagnosis, DriveLoopRequest, Evaluation


def _backend():
    return object.__new__(DriveDreamer2Backend)


def test_seed_offset_follows_iteration_and_defaults_do_not_override_generation():
    env0 = _backend()._build_generation_parameter_env({}, 0)
    env2 = _backend()._build_generation_parameter_env(None, 2)

    assert env0 == {"DRIVELOOP_DD2_SEED_OFFSET": "0"}
    assert env2 == {"DRIVELOOP_DD2_SEED_OFFSET": "2"}


def test_generation_escalation_maps_to_dd2_env_overrides():
    condition = {
        "generation_escalation": {
            "level": 2,
            "num_inf_steps": 50,
            "max_guidance_scale": 7.0,
        }
    }
    env = _backend()._build_generation_parameter_env(condition, 1)

    assert env["DRIVELOOP_DD2_SEED_OFFSET"] == "1"
    assert env["DRIVELOOP_DD2_NUM_INF_STEPS"] == "50"
    assert env["DRIVELOOP_DD2_MAX_GUIDANCE"] == "7.0"
    assert "DRIVELOOP_DD2_MIN_GUIDANCE" not in env


def _failed_perception_evaluation():
    return Evaluation(
        score=0.2,
        metrics={},
        diagnosis=Diagnosis(
            passed=False,
            reasons=["target_object_not_detected"],
            suggested_actions=[],
        ),
    )


def test_refiner_adds_generation_escalation_ladder():
    refiner = RuleBasedRefiner()
    request = DriveLoopRequest(prompt="night urban street, a motorcycle cuts in from the left")

    refinement = refiner.refine(request, _failed_perception_evaluation())
    escalation = refinement.condition["generation_escalation"]
    assert escalation["level"] == 1
    assert escalation["num_inf_steps"] == 50
    assert "max_guidance_scale" not in escalation
    assert "generation_escalation_level_1" in refinement.notes

    request2 = DriveLoopRequest(
        prompt=request.prompt,
        condition=dict(refinement.condition),
    )
    refinement2 = refiner.refine(request2, _failed_perception_evaluation())
    escalation2 = refinement2.condition["generation_escalation"]
    assert escalation2["level"] == 2
    assert escalation2["num_inf_steps"] == 50
    assert escalation2["max_guidance_scale"] == 7.0


def test_saturated_refiner_ablation_does_not_add_generation_escalation():
    refiner = RuleBasedRefiner()
    refiner.PERCEPTION_ESCALATION = []
    refiner.STRUCTURAL_ESCALATION_ENABLED = False
    request = DriveLoopRequest(prompt="night urban street, a motorcycle cuts in from the left")

    refinement = refiner.refine(request, _failed_perception_evaluation())
    assert "generation_escalation" not in refinement.condition
