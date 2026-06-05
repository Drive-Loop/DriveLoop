from dataclasses import dataclass
import os
import subprocess
import time


@dataclass
class RecordedAudioPrompt:
    path: str
    backend: str = "ffmpeg"


class MicrophoneRecorder:
    """Record a local microphone prompt into a WAV file."""

    def __init__(
        self,
        output_dir,
        duration_sec=None,
        device=None,
        backend="auto",
        output_path=None,
    ):
        self.output_dir = output_dir
        self.duration_sec = duration_sec
        self.device = device
        self.backend = backend
        self.output_path = output_path

    def record(self):
        os.makedirs(self.output_dir, exist_ok=True)
        path = self.output_path or os.path.join(
            self.output_dir, f"microphone_prompt_{int(time.time())}.wav"
        )

        if self.backend not in {"auto", "ffmpeg"}:
            raise RuntimeError(f"Unsupported audio recording backend: {self.backend}")

        cmd = ["ffmpeg", "-y"]
        if self.duration_sec:
            cmd.extend(["-t", str(self.duration_sec)])

        if self.device:
            cmd.extend(["-f", "alsa", "-i", self.device])
        else:
            cmd.extend(["-f", "alsa", "-i", "default"])

        cmd.extend(["-ac", "1", "-ar", "16000", path])
        subprocess.run(cmd, check=True)
        return RecordedAudioPrompt(path=path, backend="ffmpeg")
