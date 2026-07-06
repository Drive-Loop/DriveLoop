from __future__ import annotations

import os
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


@dataclass(frozen=True)
class TranscriptionReview:
    raw_transcript: str
    suggested_transcript: str
    review_reason: str
    accepted_by_user: bool = False
    confidence: float | None = None
    flags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_transcript": self.raw_transcript,
            "suggested_transcript": self.suggested_transcript,
            "review_reason": self.review_reason,
            "accepted_by_user": self.accepted_by_user,
            "confidence": self.confidence,
            "flags": list(self.flags),
            "metadata": dict(self.metadata),
        }


class AudioTranscriptionProvider(Protocol):
    def transcribe_file(
        self,
        audio_path: Path,
        content_type: str | None = None,
        filename: str | None = None,
    ) -> TranscriptionResult:
        ...


class ASRReviewAgent(Protocol):
    def review(self, result: TranscriptionResult) -> TranscriptionReview:
        ...


class AuditOnlyASRReviewAgent:
    """Preserve raw ASR output and emit review metadata without rewriting text."""

    def review(self, result: TranscriptionResult) -> TranscriptionReview:
        raw_transcript = result.transcript.strip()
        flags: List[str] = []
        confidence = self._extract_confidence(result.metadata)

        if not raw_transcript:
            flags.append("empty_transcript")
            reason = "No ASR text was detected; provide or edit the transcript before generation."
        else:
            reason = "Audit-only ASR review retained the raw transcript; no automatic correction was applied."

        return TranscriptionReview(
            raw_transcript=raw_transcript,
            suggested_transcript=raw_transcript,
            review_reason=reason,
            accepted_by_user=False,
            confidence=confidence,
            flags=flags,
            metadata={
                "review_backend": "audit_only",
                "source_backend": result.backend,
                "source_status": result.status,
            },
        )

    def _extract_confidence(self, metadata: Dict[str, Any]) -> float | None:
        for key in ("confidence", "language_probability"):
            value = metadata.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None



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
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
            return TranscriptionResult(
                transcript=transcript,
                backend="faster_whisper",
                status="ok",
                language=getattr(info, "language", None),
                metadata={
                    "model": self.model_name,
                    "vad_filter": self.vad_filter,
                    "initial_prompt_enabled": bool(self.initial_prompt),
                    "language_probability": getattr(info, "language_probability", None),
                    "filename": filename,
                    "content_type": content_type,
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
                "asr": voice.get("asr"),
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

        sketch = metadata.get("sketch")
        if isinstance(sketch, dict):
            sketch_evidence = self.image_provider.describe({**sketch, "type": "sketch"})
            if sketch_evidence is not None:
                evidence.append(sketch_evidence)

        video = metadata.get("video")
        if isinstance(video, dict):
            video_evidence = self._describe_video_middle_frame(video)
            if video_evidence is not None:
                evidence.append(video_evidence)

        return evidence

    def _describe_video_middle_frame(self, video: Dict[str, Any]) -> ModalityEvidence | None:
        path = video.get("path") or video.get("file_path")
        if not path or not Path(str(path)).exists():
            return None
        try:
            import cv2
            import tempfile
        except ImportError:
            return None
        capture = cv2.VideoCapture(str(path))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if frame_count > 1:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
        ok, frame = capture.read()
        capture.release()
        if not ok:
            return None
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            cv2.imwrite(handle.name, frame)
            frame_path = handle.name
        try:
            return self.image_provider.describe({
                "path": frame_path,
                "filename": video.get("filename") or Path(str(path)).name,
                "type": "video_frame",
            })
        finally:
            Path(frame_path).unlink(missing_ok=True)


class BlipImageUnderstandingProvider:
    """Real image captioning via BLIP (Sec. 3.3 psi_i / psi_k).

    Lazily loads Salesforce/blip-image-captioning-base (override with
    DRIVELOOP_BLIP_MODEL). Falls back to None when the image path is missing.
    """

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        self.model_name = model_name or os.environ.get(
            "DRIVELOOP_BLIP_MODEL", "Salesforce/blip-image-captioning-base"
        )
        self.device = device or os.environ.get("DRIVELOOP_BLIP_DEVICE", "cpu")
        self._model = None
        self._processor = None

    def _load(self) -> None:
        if self._model is not None:
            return
        from transformers import BlipForConditionalGeneration, BlipProcessor
        self._processor = BlipProcessor.from_pretrained(self.model_name)
        self._model = BlipForConditionalGeneration.from_pretrained(self.model_name).to(self.device)

    def describe(self, image: Dict[str, Any]) -> ModalityEvidence | None:
        path = image.get("path") or image.get("file_path")
        if not path or not Path(path).exists():
            return None
        self._load()
        from PIL import Image as PILImage
        pil_image = PILImage.open(path).convert("RGB")
        inputs = self._processor(pil_image, return_tensors="pt").to(self.device)
        output = self._model.generate(**inputs, max_new_tokens=40)
        caption = self._processor.decode(output[0], skip_special_tokens=True).strip()
        if not caption:
            return None
        return ModalityEvidence(
            modality=str(image.get("type") or "image"),
            text=caption,
            metadata={
                "filename": image.get("filename") or Path(str(path)).name,
                "model": self.model_name,
            },
            status="measured_blip_caption",
        )
