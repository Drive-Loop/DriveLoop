import copy
import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field

from driveloop.agents.utils import check_and_mkdirs, sanitize_filename


class GenerationBackendError(RuntimeError):
    pass


@dataclass
class GenerationResult:
    video_path: str
    logging_name: str
    backend_name: str
    prompt: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "video_path": self.video_path,
            "logging_name": self.logging_name,
            "backend_name": self.backend_name,
            "prompt": self.prompt,
            "metadata": self.metadata,
        }


class BaseGenerationBackend:
    def render(self, prompt, attempt_id=None):
        raise NotImplementedError


class NativeChatSimBackend(BaseGenerationBackend):
    def __init__(self, chatsim_cls, base_config, args):
        self.chatsim_cls = chatsim_cls
        self.base_config = copy.deepcopy(base_config)
        self.args = args

    def render(self, prompt, attempt_id=None):
        config = copy.deepcopy(self.base_config)
        if attempt_id is None:
            simulation_name = self.args.simulation_name
        else:
            simulation_name = f"{self.args.simulation_name}_loop{attempt_id:02d}"
        config["scene"]["simulation_name"] = simulation_name

        chatsim = self.chatsim_cls(config)
        chatsim.setup_init_frame()
        chatsim.execute_llms(prompt)
        video_path = chatsim.execute_funcs()
        return GenerationResult(
            video_path=video_path,
            logging_name=chatsim.scene.logging_name,
            backend_name="native_chatsim",
            prompt=prompt,
            metadata={
                "simulation_name": simulation_name,
            },
        )


class ExternalCommandBackend(BaseGenerationBackend):
    """
    Run an external baseline command and expect either:
      1) a video written to {video_path}, or
      2) a JSON manifest written to {output_json} containing a "video_path" field.

    Supported placeholders:
      {prompt}, {attempt_id}, {simulation_name}, {video_path},
      {output_json}, {metadata_json}, {config_yaml}, {backend_name}
    """

    def __init__(self, backend_name, command_template, args):
        if not command_template:
            raise GenerationBackendError(
                f"Backend '{backend_name}' requires a command template. "
                "Provide --backend_command."
            )
        self.backend_name = backend_name
        self.command_template = command_template
        self.args = args
        self.timeout_sec = int(getattr(args, "backend_timeout_sec", 7200))
        self.output_dir = getattr(args, "backend_output_dir", "results/baselines")
        self.workdir = getattr(args, "backend_workdir", None)
        check_and_mkdirs(self.output_dir)

    def render(self, prompt, attempt_id=None):
        if attempt_id is None:
            attempt_id = 1
        simulation_name = (
            self.args.simulation_name
            if attempt_id is None
            else f"{self.args.simulation_name}_loop{attempt_id:02d}"
        )
        stem = sanitize_filename(simulation_name, default=self.backend_name)
        backend_dir = os.path.join(self.output_dir, self.backend_name, stem)
        check_and_mkdirs(backend_dir)
        video_path = os.path.abspath(os.path.join(backend_dir, f"{stem}.mp4"))
        output_json = os.path.abspath(os.path.join(backend_dir, f"{stem}.json"))

        metadata = {
            "backend_name": self.backend_name,
            "attempt_id": attempt_id,
            "simulation_name": simulation_name,
            "prompt": prompt,
            "config_yaml": getattr(self.args, "config_yaml", ""),
            "video_path": video_path,
            "output_json": output_json,
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            metadata_json = f.name

        try:
            command = self._format_command(
                prompt=prompt,
                attempt_id=attempt_id,
                simulation_name=simulation_name,
                video_path=video_path,
                output_json=output_json,
                metadata_json=metadata_json,
                config_yaml=getattr(self.args, "config_yaml", ""),
                backend_name=self.backend_name,
            )
            completed = subprocess.run(
                command,
                shell=True,
                cwd=self.workdir,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_sec,
            )
            if completed.returncode != 0:
                raise GenerationBackendError(
                    f"Backend '{self.backend_name}' failed with code {completed.returncode}\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )

            payload = self._load_payload(output_json, video_path, completed.stdout)
        finally:
            try:
                os.remove(metadata_json)
            except OSError:
                pass

        resolved_video_path = payload.get("video_path", video_path)
        if not os.path.exists(resolved_video_path):
            raise GenerationBackendError(
                f"Backend '{self.backend_name}' did not produce a video. "
                f"Expected '{resolved_video_path}'."
            )

        return GenerationResult(
            video_path=resolved_video_path,
            logging_name=payload.get("logging_name", stem),
            backend_name=self.backend_name,
            prompt=prompt,
            metadata=payload,
        )

    def _format_command(self, **kwargs):
        format_values = {
            key: shlex.quote(str(value)) if key != "attempt_id" else value
            for key, value in kwargs.items()
        }
        command = self.command_template
        for key, value in format_values.items():
            command = command.replace("{" + key + "}", str(value))
        return command

    def _load_payload(self, output_json, video_path, stdout):
        if os.path.exists(output_json):
            with open(output_json, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                return payload

        if os.path.exists(video_path):
            return {"video_path": video_path}

        start = stdout.find("{")
        end = stdout.rfind("}")
        if start != -1 and end != -1 and end >= start:
            payload = json.loads(stdout[start:end + 1])
            if isinstance(payload, dict):
                return payload

        return {}


def build_generation_backend(chatsim_cls, base_config, args):
    backend_name = getattr(args, "generation_backend", "native_chatsim")
    if backend_name == "native_chatsim":
        return NativeChatSimBackend(chatsim_cls, base_config, args)

    if backend_name == "magicdrive_v2":
        return ExternalCommandBackend(
            backend_name=backend_name,
            command_template=getattr(args, "backend_command", None),
            args=args,
        )

    raise GenerationBackendError(
        f"Unsupported generation backend '{backend_name}'. "
        "Choose one of native_chatsim or magicdrive_v2."
    )
