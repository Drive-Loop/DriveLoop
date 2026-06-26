from driveloop.intent.adapter import RuleBasedIntentAdapter


def test_intent_adapter_extracts_rainy_night_cut_in_scene():
    adapter = RuleBasedIntentAdapter()

    intent = adapter.parse(
        "rainy night intersection, a pedestrian crosses in front while a car cuts in from the right"
    ).to_dict()

    assert intent["weather"] == "rain"
    assert intent["lighting"] == "night"
    assert intent["road_environment"] == "urban_intersection"
    assert {"category": "car", "attributes": {}} in intent["actors"]
    assert {"category": "pedestrian", "attributes": {}} in intent["actors"]
    assert "front" in intent["relations"]
    assert "right" in intent["relations"]
    assert "crossing" in intent["motion_primitives"]
    assert "cut_in" in intent["motion_primitives"]
    assert "heavy_rain" in intent["long_tail_tags"]
    assert "cut_in" in intent["long_tail_tags"]


def test_intent_adapter_extracts_foggy_stopped_vehicle_scene():
    adapter = RuleBasedIntentAdapter()

    intent = adapter.parse("foggy road with a parked vehicle").to_dict()

    assert intent["weather"] == "fog"
    assert intent["road_environment"] == "urban_road"
    assert {"category": "car", "attributes": {}} in intent["actors"]
    assert "stopped" in intent["motion_primitives"]
    assert "fog" in intent["long_tail_tags"]
    assert "low_visibility" in intent["long_tail_tags"]
    assert "stopped_vehicle" in intent["long_tail_tags"]
    assert "low_visibility" in intent["risk_factors"]
    assert "static_obstacle" in intent["risk_factors"]


def test_intent_adapter_preserves_multimodal_evidence():
    adapter = RuleBasedIntentAdapter()

    intent = adapter.parse(
        "foggy road with a parked vehicle",
        metadata={
            "modalities": ["text", "image", "voice"],
            "image": {"filename": "road.jpg", "status": "placeholder"},
            "voice": {"transcript": "foggy road with a parked vehicle", "status": "placeholder"},
        },
    ).to_dict()

    assert intent["multimodal_evidence"]["modalities"] == ["text", "image", "voice"]
    assert intent["multimodal_evidence"]["image"]["filename"] == "road.jpg"
    assert intent["multimodal_evidence"]["voice"]["transcript"] == "foggy road with a parked vehicle"

def test_intent_adapter_uses_voice_transcript_and_image_filename():
    adapter = RuleBasedIntentAdapter()

    intent = adapter.parse(
        "urban driving scene",
        metadata={
            "modalities": ["text", "image", "voice"],
            "image": {
                "filename": "foggy_intersection_reference.jpg",
                "status": "placeholder",
            },
            "voice": {
                "transcript": "a pedestrian crosses in front of a stopped vehicle at night",
                "status": "placeholder",
            },
        },
    ).to_dict()

    assert intent["weather"] == "fog"
    assert intent["lighting"] == "night"
    assert intent["road_environment"] == "urban_intersection"
    assert {"category": "pedestrian", "attributes": {}} in intent["actors"]
    assert {"category": "car", "attributes": {}} in intent["actors"]
    assert "crossing" in intent["motion_primitives"]
    assert "stopped" in intent["motion_primitives"]
    assert "low_visibility" in intent["long_tail_tags"]
    assert intent["multimodal_evidence"]["modalities"] == ["text", "image", "voice"]
