from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Protocol


@dataclass(frozen=True)
class ModalityEvidence:
    modality: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "placeholder"


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    backend: str
    status: str
    language: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AudioTranscriptionProvider(Protocol):
    def transcribe_file(
        self,
        audio_path: Path,
        content_type: str | None = None,
        filename: str | None = None,
    ) -> TranscriptionResult:
        ...


_DRIVING_ASR_NORMALIZATION_RULES = [
    (re.compile(r"\b4\s*g\s+night\b", re.IGNORECASE), "foggy night"),
    (re.compile(r"\bfor\s+g\s+night\b", re.IGNORECASE), "foggy night"),
    (re.compile(r"\bfour\s+g\s+night\b", re.IGNORECASE), "foggy night"),
    (re.compile(r"\bago\s+bay\s+high\s+court\b", re.IGNORECASE), "ego vehicle"),
    (re.compile(r"\baegean\s+(?:high\s+court|vehicle|car)\b", re.IGNORECASE), "ego vehicle"),
    (re.compile(r"\bego\s+bay\s+high\s+court\b", re.IGNORECASE), "ego vehicle"),
]


def normalize_driving_asr_transcript(transcript: str):
    normalized = transcript
    applied = []
    for pattern, replacement in _DRIVING_ASR_NORMALIZATION_RULES:
        updated, count = pattern.subn(replacement, normalized)
        if count:
            applied.append(
                {
                    "pattern": pattern.pattern,
                    "replacement": replacement,
                    "count": count,
                }
            )
            normalized = updated
    return normalized, applied


class WhisperAudioTranscriptionProvider:
    """Local ASR provider for uploaded or recorded voice prompts.

    It prefers faster-whisper when installed, then falls back to openai-whisper.
    Unit tests should inject a fake provider instead of loading a model.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or os.environ.get("DRIVELOOP_ASR_MODEL", "small")
        self.language = os.environ.get("DRIVELOOP_ASR_LANGUAGE", "en")
        self.initial_prompt = os.environ.get("DRIVELOOP_ASR_INITIAL_PROMPT", "").strip() or None
        self.vad_filter = os.environ.get("DRIVELOOP_ASR_VAD_FILTER", "0") == "1"

    def transcribe_file(
        self,
        audio_path: Path,
        content_type: str | None = None,
        filename: str | None = None,
    ) -> TranscriptionResult:
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except ImportError:
            WhisperModel = None

        if WhisperModel is not None:
            model = WhisperModel(self.model_name, device=os.environ.get("DRIVELOOP_ASR_DEVICE", "cpu"))
            language = None if self.language == "auto" else self.language
            segments, info = model.transcribe(
                str(audio_path),
                language=language,
                initial_prompt=self.initial_prompt,
                vad_filter=self.vad_filter,
                beam_size=5,
            )
            raw_transcript = " ".join(segment.text.strip() for segment in segments).strip()
            transcript, normalization_rules = normalize_driving_asr_transcript(
                raw_transcript
            )
            return TranscriptionResult(
                transcript=transcript,
                backend="faster_whisper",
                status="ok",
                language=getattr(info, "language", None),
                metadata={
                    "model": self.model_name,
                "vad_filter": self.vad_filter,
                "initial_prompt_enabled": bool(self.initial_prompt),
                    "filename": filename,
                    "content_type": content_type,
                    "raw_transcript": raw_transcript,
                    "normalization_rules": normalization_rules,
                    "normalized": transcript != raw_transcript,
                },
            )

        try:
            import whisper  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "No ASR backend is installed. Install faster-whisper or openai-whisper."
            ) from exc

        model = whisper.load_model(self.model_name)
        language = None if self.language == "auto" else self.language
        result = model.transcribe(
            str(audio_path),
            language=language,
            initial_prompt=self.initial_prompt,
        )
        return TranscriptionResult(
            transcript=str(result.get("text", "")).strip(),
            backend="openai_whisper",
            status="ok",
            language=result.get("language"),
            metadata={
                "model": self.model_name,
                "filename": filename,
                "content_type": content_type,
            },
        )



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
