import cv2
import numpy as np

from driveloop.grounding import RuleBasedGrounder
from driveloop.intent.providers import ModalityEvidence, MultimodalPreprocessor
from driveloop.schema import DriveLoopRequest


class FakeCaptioner:
    def __init__(self):
        self.calls = []

    def describe(self, image):
        self.calls.append(dict(image))
        return ModalityEvidence(
            modality=str(image.get("type") or "image"),
            text="a motorcycle rides at night in the rain",
            status="measured_fake",
        )


def test_sketch_routes_through_image_provider(tmp_path):
    captioner = FakeCaptioner()
    pre = MultimodalPreprocessor(image_provider=captioner)
    evidence = pre.collect_evidence({"sketch": {"path": "x.png", "filename": "x.png"}})
    assert len(evidence) == 1
    assert captioner.calls[0]["type"] == "sketch"


def test_video_middle_frame_routes_through_image_provider(tmp_path):
    video_path = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 4, (64, 64))
    for _ in range(6):
        writer.write(np.zeros((64, 64, 3), dtype=np.uint8))
    writer.release()

    captioner = FakeCaptioner()
    pre = MultimodalPreprocessor(image_provider=captioner)
    evidence = pre.collect_evidence({"video": {"path": str(video_path)}})
    assert len(evidence) == 1
    assert captioner.calls[0]["type"] == "video_frame"


def test_grounder_absorbs_caption_evidence():
    captioner = FakeCaptioner()
    grounder = RuleBasedGrounder(multimodal_preprocessor=MultimodalPreprocessor(image_provider=captioner))
    spec = grounder.ground(DriveLoopRequest(
        prompt="generate a driving scene like this image",
        metadata={"image": {"path": "ref.jpg", "filename": "ref.jpg"}},
    ))
    categories = [o.category for o in spec.objects]
    assert "motorcycle" in categories
    assert spec.environment["weather"] == "rain"
    assert spec.environment["lighting"] == "night"


def test_grounder_without_preprocessor_unchanged():
    spec = RuleBasedGrounder().ground(DriveLoopRequest(prompt="a car at daytime"))
    assert [o.category for o in spec.objects] == ["car"]
