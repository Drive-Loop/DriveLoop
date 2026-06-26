from driveloop.intent.adapter import RuleBasedIntentAdapter
from driveloop.intent.providers import (
    MultimodalPreprocessor,
    PlaceholderImageUnderstandingProvider,
    PlaceholderVoiceUnderstandingProvider,
)


def test_placeholder_image_provider_uses_filename_as_visual_hint():
    provider = PlaceholderImageUnderstandingProvider()

    evidence = provider.describe(
        {
            "filename": "foggy_night_pedestrian_crossing.png",
            "type": "image/png",
            "size": 12345,
            "status": "placeholder",
        }
    )

    assert evidence is not None
    assert evidence.modality == "image"
    assert evidence.text == "foggy night pedestrian crossing.png"
    assert evidence.metadata["filename"] == "foggy_night_pedestrian_crossing.png"
    assert evidence.status == "placeholder"


def test_placeholder_voice_provider_uses_transcript():
    provider = PlaceholderVoiceUnderstandingProvider()

    evidence = provider.transcribe(
        {
            "transcript": "a cyclist cuts in from the left near an intersection",
            "status": "placeholder",
        }
    )

    assert evidence is not None
    assert evidence.modality == "voice"
    assert evidence.text == "a cyclist cuts in from the left near an intersection"
    assert evidence.metadata["transcript"] == "a cyclist cuts in from the left near an intersection"


def test_multimodal_preprocessor_collects_image_and_voice_evidence():
    preprocessor = MultimodalPreprocessor()

    evidence = preprocessor.collect_evidence(
        {
            "image": {"filename": "foggy_intersection_reference.jpg", "status": "placeholder"},
            "voice": {
                "transcript": "a pedestrian crosses at night",
                "status": "placeholder",
            },
        }
    )

    assert [item.modality for item in evidence] == ["image", "voice"]
    assert evidence[0].text == "foggy intersection reference.jpg"
    assert evidence[1].text == "a pedestrian crosses at night"


def test_rule_based_adapter_consumes_preprocessed_multimodal_evidence():
    adapter = RuleBasedIntentAdapter()

    intent = adapter.parse(
        "urban driving scene",
        metadata={
            "modalities": ["text", "image", "voice"],
            "image": {"filename": "foggy_intersection_reference.jpg", "status": "placeholder"},
            "voice": {
                "transcript": "a pedestrian crosses at night",
                "status": "placeholder",
            },
        },
    ).to_dict()

    assert intent["weather"] == "fog"
    assert intent["lighting"] == "night"
    assert intent["road_environment"] == "urban_intersection"
    assert {"category": "pedestrian", "attributes": {}} in intent["actors"]
    assert "crossing" in intent["motion_primitives"]
