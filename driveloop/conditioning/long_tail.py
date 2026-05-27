import json
import math
import os
import re
from dataclasses import asdict, dataclass, field

import cv2
import imageio.v2 as imageio
import numpy as np


LONG_TAIL_SYNONYMS = {
    "animal_crossing": ["animal crossing", "deer crossing", "dog crossing", "animal"],
    "traffic_accident": ["traffic accident", "car crash", "collision", "accident"],
    "heavy_rain": ["heavy rain", "rainstorm", "rainy"],
    "fog": ["fog", "foggy", "dense fog", "mist"],
    "snow": ["snow", "snowy", "blizzard"],
}


def _check_and_mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


def _sanitize_filename(text, default="simulation", max_length=80):
    text = str(text).strip().replace(os.sep, "_")
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^0-9A-Za-z._\-]+", "_", text)
    text = text.strip("._-")
    if len(text) == 0:
        text = default
    return text[:max_length]


@dataclass
class LongTailPlan:
    tags: list = field(default_factory=list)
    prompt_suffixes: list = field(default_factory=list)
    postprocess_effects: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class LongTailScenarioController:
    """
    Add explicit long-tail scenario control to the LoopDrive pipeline.

    Supported tags:
      - animal_crossing
      - traffic_accident
      - heavy_rain
      - fog
      - snow
    """

    def __init__(self, output_dir="results/conditioning", weather_strength=0.45):
        self.output_dir = output_dir
        self.weather_strength = float(weather_strength)

    def build_plan(self, prompt, requested_tags=None):
        tags = self._resolve_tags(prompt, requested_tags)
        prompt_suffixes = []
        postprocess_effects = []
        notes = []

        if "traffic_accident" in tags:
            prompt_suffixes.append(
                "Add a roadside accident scene with stopped vehicles, traffic cones, and a warning fence while preserving the original request."
            )
            notes.append("Enabled prompt-level accident composition using existing vehicle and obstacle assets.")
        if "heavy_rain" in tags:
            prompt_suffixes.append("The scene takes place under heavy rain with reduced visibility.")
            postprocess_effects.append("heavy_rain")
        if "fog" in tags:
            prompt_suffixes.append("The scene takes place under dense fog with low contrast and limited visibility.")
            postprocess_effects.append("fog")
        if "snow" in tags:
            prompt_suffixes.append("The scene takes place during snowfall with reduced visibility.")
            postprocess_effects.append("snow")
        if "animal_crossing" in tags:
            notes.append("Enabled animated animal-crossing overlay during video post-processing.")
            postprocess_effects.append("animal_crossing")

        return LongTailPlan(
            tags=tags,
            prompt_suffixes=prompt_suffixes,
            postprocess_effects=postprocess_effects,
            notes=notes,
        )

    def augment_prompt(self, prompt, plan):
        prompt = (prompt or "").strip()
        if not plan.prompt_suffixes:
            return prompt
        suffix = " ".join(plan.prompt_suffixes)
        if not prompt:
            return suffix
        return f"{prompt} {suffix}"

    def apply_postprocess(self, video_path, plan, attempt_id=None):
        if not plan.postprocess_effects:
            return video_path

        frames = imageio.mimread(video_path)
        if not frames:
            return video_path

        processed_frames = []
        fps = 5
        try:
            reader = imageio.get_reader(video_path)
            fps = float(reader.get_meta_data().get("fps", fps))
            reader.close()
        except Exception:
            fps = 5
        for frame_index, frame in enumerate(frames):
            image = np.array(frame).astype(np.uint8)
            for effect in plan.postprocess_effects:
                if effect == "fog":
                    image = self._apply_fog(image, frame_index, len(frames))
                elif effect == "heavy_rain":
                    image = self._apply_rain(image, frame_index)
                elif effect == "snow":
                    image = self._apply_snow(image, frame_index)
                elif effect == "animal_crossing":
                    image = self._apply_animal_crossing(image, frame_index, len(frames))
            processed_frames.append(image)

        output_path = self._build_output_path(video_path, attempt_id, plan)
        _check_and_mkdirs(os.path.dirname(output_path))
        writer = imageio.get_writer(output_path, fps=fps)
        for frame in processed_frames:
            writer.append_data(frame)
        writer.close()

        self._write_plan_report(output_path, plan)
        return output_path

    def _resolve_tags(self, prompt, requested_tags):
        prompt_text = (prompt or "").lower()
        tags = set()
        if requested_tags:
            if isinstance(requested_tags, str):
                requested_tags = [item.strip() for item in requested_tags.split(",")]
            for tag in requested_tags:
                normalized = str(tag).strip().lower()
                if normalized:
                    tags.add(normalized)

        for canonical_tag, phrases in LONG_TAIL_SYNONYMS.items():
            for phrase in phrases:
                if phrase in prompt_text:
                    tags.add(canonical_tag)
                    break
        return sorted(tags)

    def _build_output_path(self, video_path, attempt_id, plan):
        base_dir = os.path.dirname(video_path)
        stem = _sanitize_filename(os.path.splitext(os.path.basename(video_path))[0])
        effect_suffix = "_".join(plan.postprocess_effects)
        if attempt_id is None:
            filename = f"{stem}_{effect_suffix}.mp4"
        else:
            filename = f"{stem}_attempt_{int(attempt_id):02d}_{effect_suffix}.mp4"
        return os.path.join(base_dir, filename)

    def _write_plan_report(self, video_path, plan):
        report_path = os.path.splitext(video_path)[0] + "_long_tail.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)

    def _apply_fog(self, frame, frame_index, total_frames):
        image = frame.astype(np.float32)
        height, width = image.shape[:2]
        fog_color = np.full_like(image, 220.0)
        vertical = np.linspace(0.35, 0.95, height, dtype=np.float32).reshape(height, 1, 1)
        temporal = 0.9 + 0.1 * math.sin((frame_index + 1) / max(1, total_frames) * math.pi)
        alpha = np.clip(self.weather_strength * vertical * temporal, 0.0, 0.8)
        blended = image * (1.0 - alpha) + fog_color * alpha
        return np.clip(blended, 0, 255).astype(np.uint8)

    def _apply_rain(self, frame, frame_index):
        image = frame.astype(np.float32)
        height, width = image.shape[:2]
        overlay = np.zeros_like(image)
        rng = np.random.default_rng(seed=frame_index + 13)
        streak_count = max(180, width // 8)
        for _ in range(streak_count):
            x = int(rng.integers(0, width))
            y = int(rng.integers(0, height))
            length = int(rng.integers(height // 20, height // 10))
            thickness = int(rng.integers(1, 3))
            dx = int(rng.integers(-6, 4))
            color = int(rng.integers(170, 235))
            cv2.line(
                overlay,
                (x, y),
                (min(width - 1, x + dx), min(height - 1, y + length)),
                (color, color, color),
                thickness,
                lineType=cv2.LINE_AA,
            )
        overlay = cv2.GaussianBlur(overlay, (3, 3), 0)
        blended = image * 0.82 + overlay * 0.42
        return np.clip(blended, 0, 255).astype(np.uint8)

    def _apply_snow(self, frame, frame_index):
        image = frame.astype(np.float32)
        height, width = image.shape[:2]
        overlay = np.zeros_like(image)
        rng = np.random.default_rng(seed=frame_index + 97)
        flake_count = max(120, width // 10)
        for _ in range(flake_count):
            x = int(rng.integers(0, width))
            y = int(rng.integers(0, height))
            radius = int(rng.integers(1, 4))
            brightness = int(rng.integers(215, 255))
            cv2.circle(overlay, (x, y), radius, (brightness, brightness, brightness), -1, lineType=cv2.LINE_AA)
        overlay = cv2.GaussianBlur(overlay, (5, 5), 0)
        blended = image * 0.90 + overlay * 0.65
        return np.clip(blended, 0, 255).astype(np.uint8)

    def _apply_animal_crossing(self, frame, frame_index, total_frames):
        start_frame = max(0, total_frames // 3)
        end_frame = max(start_frame + 1, total_frames * 2 // 3)
        if frame_index < start_frame or frame_index > end_frame:
            return frame

        image = frame.copy()
        height, width = image.shape[:2]
        progress = (frame_index - start_frame) / max(1, end_frame - start_frame)
        center_x = int(width * (0.72 - 0.44 * progress))
        center_y = int(height * 0.78)
        scale = max(18, int(min(height, width) * 0.025))

        color = (40, 35, 30)
        cv2.ellipse(image, (center_x, center_y), (scale, scale // 2), 0, 0, 360, color, -1)
        cv2.circle(image, (center_x + scale, center_y - scale // 3), scale // 3, color, -1)
        cv2.line(image, (center_x - scale // 2, center_y + scale // 2), (center_x - scale // 2, center_y + scale), color, 3)
        cv2.line(image, (center_x, center_y + scale // 2), (center_x, center_y + scale), color, 3)
        cv2.line(image, (center_x + scale // 2, center_y + scale // 2), (center_x + scale // 2, center_y + scale), color, 3)
        cv2.line(image, (center_x + scale, center_y + scale // 2), (center_x + scale, center_y + scale), color, 3)
        cv2.line(image, (center_x - scale, center_y - scale // 6), (center_x - int(scale * 1.4), center_y - scale // 2), color, 2)
        cv2.line(image, (center_x + scale + scale // 6, center_y - scale // 2), (center_x + scale + scale // 2, center_y - scale), color, 2)
        cv2.line(image, (center_x + scale + scale // 3, center_y - scale // 2), (center_x + scale + int(scale * 0.9), center_y - scale), color, 2)
        return image
