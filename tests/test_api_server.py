from fastapi.testclient import TestClient

from driveloop.api.server import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_endpoint_with_mock_backend():
    response = client.post(
        "/generate",
        json={
            "prompt": "rainy night intersection, a pedestrian crosses in front while a car cuts in from the right",
            "scenario_id": "api_test_mock",
            "max_iterations": 2,
            "target_score": 0.9,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["scenario_id"] == "api_test_mock"
    assert body["accepted"] is True
    assert body["best_score"] >= 0.9
    assert body["iterations"] >= 1
    assert "best_generation" in body
    assert "best_evaluation" in body
    assert "history" in body
    assert body["history"]


def test_generate_endpoint_rejects_unknown_backend():
    response = client.post(
        "/generate",
        json={
            "prompt": "daytime urban driving scene with surrounding vehicles",
            "scenario_id": "api_test_unknown_backend",
            "backend": "unknown",
            "max_iterations": 1,
            "target_score": 0.9,
        },
    )

    assert response.status_code == 422


def test_history_endpoint_returns_jsonl_records_after_generation():
    scenario_id = "api_test_history"

    generate_response = client.post(
        "/generate",
        json={
            "prompt": "rainy night road with surrounding vehicles",
            "scenario_id": scenario_id,
            "backend": "mock",
            "max_iterations": 1,
            "target_score": 0.5,
        },
    )
    assert generate_response.status_code == 200

    history_response = client.get(f"/history/{scenario_id}")
    assert history_response.status_code == 200

    body = history_response.json()
    assert body["scenario_id"] == scenario_id
    assert body["iterations"] == 1
    assert len(body["history"]) == 1
    assert "generation" in body["history"][0]
    assert "evaluation" in body["history"][0]


def test_history_endpoint_returns_404_for_missing_scenario():
    response = client.get("/history/does_not_exist")
    assert response.status_code == 404


def test_artifact_endpoint_returns_generated_file():
    scenario_id = "api_test_artifact"

    generate_response = client.post(
        "/generate",
        json={
            "prompt": "daytime road with a car",
            "scenario_id": scenario_id,
            "backend": "mock",
            "max_iterations": 1,
            "target_score": 0.5,
        },
    )
    assert generate_response.status_code == 200

    body = generate_response.json()
    artifact_path = body["best_generation"]["artifacts"]["mock_video"]
    filename = artifact_path.split("/")[-1]

    artifact_response = client.get(f"/artifacts/{scenario_id}/{filename}")
    assert artifact_response.status_code == 200
    assert artifact_response.text


def test_artifact_endpoint_returns_404_for_missing_file():
    response = client.get("/artifacts/api_test_artifact/missing.mp4")
    assert response.status_code == 404


def test_summary_endpoint_returns_frontend_friendly_record():
    scenario_id = "api_test_summary"

    generate_response = client.post(
        "/generate",
        json={
            "prompt": "rainy night intersection with a car",
            "scenario_id": scenario_id,
            "backend": "mock",
            "max_iterations": 2,
            "target_score": 0.9,
        },
    )
    assert generate_response.status_code == 200

    summary_response = client.get(f"/summary/{scenario_id}")
    assert summary_response.status_code == 200

    body = summary_response.json()
    assert body["scenario_id"] == scenario_id
    assert body["iterations"] >= 1
    assert body["best_score"] >= 0.9
    assert body["accepted"] is True
    assert body["backend"] == "mock"
    assert body["artifacts"]
    assert body["diagnosis"]["passed"] is True
    assert "condition_trace" in body


def test_summary_endpoint_returns_404_for_missing_scenario():
    response = client.get("/summary/does_not_exist")
    assert response.status_code == 404


def test_generate_and_summary_preserve_multimodal_metadata():
    scenario_id = "api_test_multimodal_metadata"

    generate_response = client.post(
        "/generate",
        json={
            "prompt": "foggy road with a parked vehicle",
            "scenario_id": scenario_id,
            "backend": "mock",
            "max_iterations": 1,
            "target_score": 0.5,
            "metadata": {
                "modalities": ["text", "image", "voice"],
                "image": {
                    "filename": "reference_intersection.png",
                    "status": "placeholder",
                },
                "voice": {
                    "transcript": "foggy road with a parked vehicle",
                    "status": "placeholder",
                },
            },
        },
    )
    assert generate_response.status_code == 200

    summary_response = client.get(f"/summary/{scenario_id}")
    assert summary_response.status_code == 200

    body = summary_response.json()
    assert body["multimodal_inputs"]["modalities"] == ["text", "image", "voice"]
    assert body["multimodal_inputs"]["image"]["filename"] == "reference_intersection.png"
    assert body["multimodal_inputs"]["voice"]["transcript"] == "foggy road with a parked vehicle"


def test_summary_returns_structured_intent():
    scenario_id = "api_test_structured_intent"

    generate_response = client.post(
        "/generate",
        json={
            "prompt": "rainy night intersection, a pedestrian crosses in front while a car cuts in from the right",
            "scenario_id": scenario_id,
            "backend": "mock",
            "max_iterations": 2,
            "target_score": 0.9,
            "metadata": {
                "modalities": ["text"],
            },
        },
    )
    assert generate_response.status_code == 200

    summary_response = client.get(f"/summary/{scenario_id}")
    assert summary_response.status_code == 200

    structured_intent = summary_response.json()["structured_intent"]
    assert structured_intent["weather"] == "rain"
    assert structured_intent["lighting"] == "night"
    assert structured_intent["road_environment"] == "urban_intersection"
    assert {"category": "pedestrian", "attributes": {}} in structured_intent["actors"]
    assert "crossing" in structured_intent["motion_primitives"]
    assert "cut_in" in structured_intent["motion_primitives"]
    assert "heavy_rain" in structured_intent["long_tail_tags"]

def test_summary_structured_intent_uses_multimodal_metadata():
    scenario_id = "api_test_multimodal_structured_intent"

    generate_response = client.post(
        "/generate",
        json={
            "prompt": "urban driving scene",
            "scenario_id": scenario_id,
            "backend": "mock",
            "max_iterations": 1,
            "target_score": 0.5,
            "metadata": {
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
        },
    )
    assert generate_response.status_code == 200

    summary_response = client.get(f"/summary/{scenario_id}")
    assert summary_response.status_code == 200

    intent = summary_response.json()["structured_intent"]
    assert intent["weather"] == "fog"
    assert intent["lighting"] == "night"
    assert intent["road_environment"] == "urban_intersection"
    assert "crossing" in intent["motion_primitives"]
    assert "stopped" in intent["motion_primitives"]
    assert "low_visibility" in intent["long_tail_tags"]
    assert intent["multimodal_evidence"]["modalities"] == ["text", "image", "voice"]

    scene_specification = summary_response.json()["condition_trace"]["scene_specification"]
    assert scene_specification["environment"]["weather"] == "fog"
    assert scene_specification["environment"]["lighting"] == "night"
    assert scene_specification["environment"]["visibility"] == "low"
    assert {"category": "pedestrian", "attributes": {}} in scene_specification["objects"]
    assert "intersection" in scene_specification["relations"]
    assert "crossing" in scene_specification["motion_primitives"]
    assert "stopped" in scene_specification["motion_primitives"]


def test_generate_and_summary_record_intent_backend():
    scenario_id = "api_test_intent_backend"

    generate_response = client.post(
        "/generate",
        json={
            "prompt": "foggy road with a pedestrian",
            "scenario_id": scenario_id,
            "backend": "mock",
            "intent_backend": "rule_based",
            "max_iterations": 1,
            "target_score": 0.5,
        },
    )
    assert generate_response.status_code == 200

    summary_response = client.get(f"/summary/{scenario_id}")
    assert summary_response.status_code == 200

    body = summary_response.json()
    assert body["intent_backend"] == "rule_based"


def test_generate_rejects_unknown_intent_backend():
    response = client.post(
        "/generate",
        json={
            "prompt": "daytime urban driving scene",
            "scenario_id": "api_test_unknown_intent_backend",
            "backend": "mock",
            "intent_backend": "unknown",
        },
    )

    assert response.status_code == 422


def test_transcribe_endpoint_returns_asr_transcript():
    from pathlib import Path
    from driveloop.api.server import set_asr_provider_for_testing
    from driveloop.intent.providers import TranscriptionResult

    class FakeASRProvider:
        def transcribe_file(self, audio_path: Path, content_type=None, filename=None):
            assert audio_path.exists()
            assert content_type == "audio/webm"
            assert filename == "voice.webm"
            return TranscriptionResult(
                transcript="Ago Bay High Court",
                backend="fake_asr",
                status="ok",
                language="en",
                metadata={
                    "filename": filename,
                    "content_type": content_type,
                },
            )

    set_asr_provider_for_testing(FakeASRProvider())
    try:
        response = client.post(
            "/transcribe",
            files={
                "audio": ("voice.webm", b"fake audio bytes", "audio/webm"),
            },
        )
    finally:
        set_asr_provider_for_testing(None)

    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "Ago Bay High Court"
    assert body["raw_transcript"] == "Ago Bay High Court"
    assert body["suggested_transcript"] == "Ago Bay High Court"
    assert body["accepted_by_user"] is False
    assert body["review"]["raw_transcript"] == "Ago Bay High Court"
    assert body["review"]["accepted_by_user"] is False
    assert body["review"]["metadata"]["review_backend"] == "audit_only"
    assert body["backend"] == "fake_asr"
    assert body["status"] == "ok"
    assert body["language"] == "en"
    assert body["metadata"]["filename"] == "voice.webm"
    assert body["metadata"]["asr_review"]["suggested_transcript"] == body["raw_transcript"]
    assert body["raw_transcript"] != "ego vehicle"
    assert body["suggested_transcript"] != "ego vehicle"


def test_transcribe_endpoint_rejects_empty_audio():
    response = client.post(
        "/transcribe",
        files={
            "audio": ("empty.webm", b"", "audio/webm"),
        },
    )

    assert response.status_code == 400
