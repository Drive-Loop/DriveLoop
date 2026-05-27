import json
import os
from dataclasses import asdict, dataclass, field

import imageio.v2 as imageio
import numpy as np
import openai
from PIL import Image


@dataclass
class PromptConditioningResult:
    raw_prompt: str
    fused_prompt: str
    audio_transcripts: list = field(default_factory=list)
    image_descriptions: list = field(default_factory=list)
    video_descriptions: list = field(default_factory=list)
    sketch_descriptions: list = field(default_factory=list)
    fusion_notes: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class MultimodalConditioner:
    """
    Convert optional multimodal references into a single text prompt for ChatSim.

    The current ChatSim backend is text-driven, so multimodal inputs are grounded
    into structured textual constraints before scene generation begins.
    """

    def __init__(
        self,
        caption_model="Salesforce/blip-image-captioning-base",
        fusion_model="gpt-4",
        max_video_frames=4,
    ):
        self.caption_model = caption_model
        self.fusion_model = fusion_model
        self.max_video_frames = max(1, int(max_video_frames))
        self._captioner = None

    def prepare_prompt(
        self,
        raw_prompt,
        audio_paths=None,
        image_paths=None,
        video_paths=None,
        sketch_paths=None,
    ):
        raw_prompt = (raw_prompt or "").strip()
        audio_paths = self._normalize_paths(audio_paths)
        image_paths = self._normalize_paths(image_paths)
        video_paths = self._normalize_paths(video_paths)
        sketch_paths = self._normalize_paths(sketch_paths)

        audio_transcripts = [
            {"path": path, "text": self._transcribe_audio(path)}
            for path in audio_paths
        ]
        image_descriptions = [
            {"path": path, "description": self._caption_image(path, hint="reference image")}
            for path in image_paths
        ]
        sketch_descriptions = [
            {"path": path, "description": self._caption_image(path, hint="hand-drawn sketch")}
            for path in sketch_paths
        ]
        video_descriptions = [
            {"path": path, "description": self._describe_video(path)}
            for path in video_paths
        ]

        fused_prompt, fusion_notes = self._fuse_prompt(
            raw_prompt=raw_prompt,
            audio_transcripts=audio_transcripts,
            image_descriptions=image_descriptions,
            video_descriptions=video_descriptions,
            sketch_descriptions=sketch_descriptions,
        )
        return PromptConditioningResult(
            raw_prompt=raw_prompt,
            fused_prompt=fused_prompt,
            audio_transcripts=audio_transcripts,
            image_descriptions=image_descriptions,
            video_descriptions=video_descriptions,
            sketch_descriptions=sketch_descriptions,
            fusion_notes=fusion_notes,
        )

    def _normalize_paths(self, paths):
        if not paths:
            return []
        if isinstance(paths, str):
            paths = [paths]
        normalized = []
        for path in paths:
            if not path:
                continue
            absolute_path = os.path.abspath(path)
            if not os.path.exists(absolute_path):
                raise FileNotFoundError(f"Conditioning input not found: {absolute_path}")
            normalized.append(absolute_path)
        return normalized

    def _transcribe_audio(self, path):
        try:
            with open(path, "rb") as f:
                response = openai.Audio.transcribe("whisper-1", f)
            text = response["text"] if isinstance(response, dict) else str(response)
            return text.strip()
        except Exception:
            stem = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
            return f"Audio instruction from file '{stem}' could not be transcribed automatically."

    def _get_captioner(self):
        if self._captioner is not None:
            return self._captioner

        from transformers import pipeline

        self._captioner = pipeline(
            "image-to-text",
            model=self.caption_model,
        )
        return self._captioner

    def _caption_image(self, path, hint="reference image"):
        try:
            image = Image.open(path).convert("RGB")
            captioner = self._get_captioner()
            result = captioner(image, max_new_tokens=48)
            if result and isinstance(result, list):
                text = result[0].get("generated_text", "").strip()
                if text:
                    return f"{hint}: {text}"
        except Exception:
            pass

        stem = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
        return f"{hint}: visual reference from file '{stem}'."

    def _describe_video(self, path):
        frame_descriptions = []
        try:
            reader = imageio.get_reader(path)
            meta = reader.get_meta_data()
            frame_count = meta.get("nframes")
            if not isinstance(frame_count, int) or frame_count <= 0:
                frame_count = self.max_video_frames
            sample_indices = np.linspace(
                0,
                max(0, frame_count - 1),
                num=min(self.max_video_frames, frame_count),
                dtype=int,
            )
            unique_indices = []
            for index in sample_indices.tolist():
                if index not in unique_indices:
                    unique_indices.append(index)

            for index in unique_indices:
                try:
                    frame = reader.get_data(index)
                except Exception:
                    continue
                image = Image.fromarray(frame.astype("uint8")).convert("RGB")
                captioner = self._get_captioner()
                result = captioner(image, max_new_tokens=40)
                if result and isinstance(result, list):
                    text = result[0].get("generated_text", "").strip()
                    if text:
                        frame_descriptions.append(f"frame {index}: {text}")
            reader.close()
        except Exception:
            frame_descriptions = []

        if frame_descriptions:
            return "reference video cues: " + "; ".join(frame_descriptions)

        stem = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
        return f"reference video cues from file '{stem}'."

    def _fuse_prompt(
        self,
        raw_prompt,
        audio_transcripts,
        image_descriptions,
        video_descriptions,
        sketch_descriptions,
    ):
        has_auxiliary_inputs = any(
            [audio_transcripts, image_descriptions, video_descriptions, sketch_descriptions]
        )
        if not has_auxiliary_inputs:
            return raw_prompt, []

        payload = {
            "raw_prompt": raw_prompt,
            "audio_transcripts": audio_transcripts,
            "image_descriptions": image_descriptions,
            "video_descriptions": video_descriptions,
            "sketch_descriptions": sketch_descriptions,
        }

        try:
            result = openai.ChatCompletion.create(
                model=self.fusion_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You merge multimodal driving-scene references into one concise prompt "
                            "for a text-driven autonomous-driving scene simulator."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Preserve the user's intent. Convert auxiliary references into explicit "
                            "scene constraints about object category, layout, color, motion, and weather. "
                            "Return valid JSON with keys 'fused_prompt' and 'fusion_notes'."
                        ),
                    },
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
                ],
            )
            answer = result["choices"][0]["message"]["content"]
            start = answer.find("{")
            end = answer.rfind("}")
            parsed = json.loads(answer[start:end + 1])
            fused_prompt = str(parsed.get("fused_prompt", "")).strip()
            if fused_prompt:
                return fused_prompt, list(parsed.get("fusion_notes", []))
        except Exception:
            pass

        notes = []
        parts = [raw_prompt] if raw_prompt else []
        if audio_transcripts:
            transcript_text = " ".join(item["text"] for item in audio_transcripts if item["text"])
            if transcript_text:
                parts.append(f"Speech guidance: {transcript_text}")
                notes.append("Merged speech guidance into the final prompt.")
        if image_descriptions:
            description_text = " ".join(item["description"] for item in image_descriptions)
            parts.append(f"Reference image cues: {description_text}")
            notes.append("Merged image reference cues into the final prompt.")
        if sketch_descriptions:
            description_text = " ".join(item["description"] for item in sketch_descriptions)
            parts.append(f"Sketch cues: {description_text}")
            notes.append("Merged sketch cues into the final prompt.")
        if video_descriptions:
            description_text = " ".join(item["description"] for item in video_descriptions)
            parts.append(f"Reference video cues: {description_text}")
            notes.append("Merged video reference cues into the final prompt.")

        fused_prompt = " ".join(part.strip() for part in parts if part and part.strip())
        return fused_prompt, notes
