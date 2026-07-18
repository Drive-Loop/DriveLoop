from __future__ import annotations

import unittest

from driveloop.grounding import RuleBasedGrounder
from driveloop.longtail import LongTailController
from driveloop.schema import DriveLoopRequest


class GroundingLongTailTest(unittest.TestCase):
    def test_grounder_extracts_scene_specification(self) -> None:
        request = DriveLoopRequest(
            prompt="rainy night scene where a truck cuts in from the left front",
            metadata={"auxiliary_inputs": {"image": "panoramic multi-view reference"}},
        )

        spec = RuleBasedGrounder().ground(request)

        self.assertIn("truck", {obj.category for obj in spec.objects})
        self.assertIn("cut_in", spec.motion_primitives)
        self.assertIn("left", spec.relations)
        self.assertEqual(spec.environment["weather"], "rain")
        self.assertEqual(spec.environment["lighting"], "night")
        self.assertEqual(spec.attributes["viewpoint"], "panoramic_multi_view")

    def test_longtail_controller_builds_condition_plan(self) -> None:
        request = DriveLoopRequest(
            prompt="foggy scene with debris obstacle ahead",
            condition={"long_tail_tags": ["traffic accident"]},
        )
        spec = RuleBasedGrounder().ground(request)

        plan = LongTailController().build(
            spec,
            requested_tags=request.condition["long_tail_tags"],
        )

        self.assertIn("traffic_accident", plan.tags)
        self.assertIn("fog", plan.tags)
        self.assertIn("road_obstacle", plan.tags)
        self.assertIn("fog_overlay", plan.postprocess_effects)
        self.assertIn("visibility", plan.executable_controls)


if __name__ == "__main__":
    unittest.main()

def test_pedestrian_crossing_does_not_trigger_animal_crossing():
    from driveloop import DriveLoopRequest
    from driveloop.grounding import RuleBasedGrounder
    from driveloop.longtail import LongTailController

    request = DriveLoopRequest(
        prompt="rainy night intersection, a pedestrian crosses in front of the ego vehicle"
    )
    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)

    assert "pedestrian" in {obj.category for obj in spec.objects}
    assert "crossing" in spec.motion_primitives
    assert "animal_crossing" not in plan.tags
    assert all("animal crossing" not in suffix for suffix in plan.prompt_suffixes)


def test_longtail_controller_structures_motorcycle_cut_in_lane_controls():
    request = DriveLoopRequest(
        prompt="foggy night road where a motorcycle cuts in from the left adjacent lane"
    )

    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)

    assert "motorcycle" in {obj.category for obj in spec.objects}
    assert "cut_in" in spec.motion_primitives
    assert "left" in spec.relations

    assert "vulnerable_road_user" in plan.tags
    assert "motorcycle_cut_in" in plan.tags
    assert "left_lane_relation" in plan.tags
    assert "low_visibility" in plan.tags

    controls = plan.executable_controls
    assert "motorcycle" in controls["objects"]
    assert "cut_in" in controls["motion"]
    assert controls["target_object_support"]["category"] == "motorcycle"
    assert controls["maneuvers"][0]["type"] == "cut_in"
    assert controls["maneuvers"][0]["requires_lane_geometry"] is True
    assert controls["lane_relations"][0]["from"] == "left_adjacent_lane"
    assert "target_motorcycle_detectable" in controls["perception_requirements"]


def test_intersection_approach_grounds_to_approaching_not_a_maneuver():
    # m4's prompt requests a motion the keyword table previously could not
    # read, so it grounded to an empty list and was spared the target_motion
    # channel (blocks 217/218). "approaching" records the requested motion
    # without asserting a lateral maneuver: an intersection approach toward
    # the ego path need not be a cut-in, so it deliberately builds no
    # trajectory and no maneuver suffix.
    request = DriveLoopRequest(
        prompt="night urban intersection, a motorcycle approaches from the left adjacent lane toward the ego path"
    )
    spec = RuleBasedGrounder().ground(request)
    plan = LongTailController().build(spec)

    assert "approaching" in spec.motion_primitives
    assert "cut_in" not in spec.motion_primitives
    assert "lane_change" not in spec.motion_primitives
    assert "motorcycle_cut_in" not in plan.tags
    assert not plan.executable_controls.get("maneuvers")


def test_approach_noun_does_not_ground_a_motion():
    # Matched on verb forms only ("approaches"/"approaching"), so a location
    # like "the approach lane" is not read as a requested motion.
    spec = RuleBasedGrounder().ground(
        DriveLoopRequest(prompt="a truck stopped on the approach lane at night")
    )
    assert "approaching" not in spec.motion_primitives
