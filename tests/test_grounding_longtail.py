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
