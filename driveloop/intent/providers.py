from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass(frozen=True)
class ModalityEvidence:
    modality: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "placeholder"


class ImageUnderstandingProvider(Protocol):
    def describe(self, image: Dict[str, Any]) -> ModalityEvidence | None:
        ...


class VoiceUnderstandingProvider(Protocol):
    def transcribe(self, voice: Dict[str, Any]) -> ModalityEvidence | None:
        ...


class PlaceholderImageUnderstandingProvider:
    def describe(self, image: Dict[str, Any]) -> ModalityEvidence | None:
        filename = image.get("filename")
        if not filename:
            return None

        visual_hint = str(filename).replace("_", " ").replace("-", " ")
        return ModalityEvidence(
            modality="image",
            text=visual_hint,
            metadata={
                "filename": filename,
                "type": image.get("type"),
                "size": image.get("size"),
            },
            status=image.get("status", "placeholder"),
        )


class PlaceholderVoiceUnderstandingProvider:
    def transcribe(self, voice: Dict[str, Any]) -> ModalityEvidence | None:
        transcript = voice.get("transcript")
        if not transcript:
            return None

        return ModalityEvidence(
            modality="voice",
            text=str(transcript),
            metadata={
                "transcript": transcript,
            },
            status=voice.get("status", "placeholder"),
        )


@dataclass
class MultimodalPreprocessor:
    image_provider: ImageUnderstandingProvider = field(default_factory=PlaceholderImageUnderstandingProvider)
    voice_provider: VoiceUnderstandingProvider = field(default_factory=PlaceholderVoiceUnderstandingProvider)

    def collect_evidence(self, metadata: Dict[str, Any]) -> List[ModalityEvidence]:
        evidence: List[ModalityEvidence] = []

        image = metadata.get("image")
        if isinstance(image, dict):
            image_evidence = self.image_provider.describe(image)
            if image_evidence is not None:
                evidence.append(image_evidence)

        voice = metadata.get("voice")
        if isinstance(voice, dict):
            voice_evidence = self.voice_provider.transcribe(voice)
            if voice_evidence is not None:
                evidence.append(voice_evidence)

        return evidence
