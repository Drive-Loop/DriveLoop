import importlib
import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field


class EvaluationError(RuntimeError):
    pass


@dataclass
class EvaluationResult:
    score: float
    passed: bool
    threshold: float
    summary: str = ""
    metrics: dict = field(default_factory=dict)
    failure_reasons: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload, threshold, score_key="score", pass_key="passed"):
        if score_key not in payload:
            raise EvaluationError(f"Evaluator output missing score key: {score_key}")

        score = float(payload[score_key])
        passed = bool(payload.get(pass_key, score >= threshold))
        failure_reasons = payload.get("failure_reasons", payload.get("reasons", []))
        suggestions = payload.get("suggestions", [])

        if isinstance(failure_reasons, str):
            failure_reasons = [failure_reasons]
        if isinstance(suggestions, str):
            suggestions = [suggestions]

        return cls(
            score=score,
            passed=passed,
            threshold=threshold,
            summary=str(payload.get("summary", payload.get("message", ""))),
            metrics=dict(payload.get("metrics", {})),
            failure_reasons=list(failure_reasons),
            suggestions=list(suggestions),
            raw=dict(payload),
        )

    def to_dict(self):
        return {
            "score": self.score,
            "passed": self.passed,
            "threshold": self.threshold,
            "summary": self.summary,
            "metrics": self.metrics,
            "failure_reasons": self.failure_reasons,
            "suggestions": self.suggestions,
            "raw": self.raw,
        }


class BaseEvaluator:
    def evaluate(self, video_path, prompt, metadata):
        raise NotImplementedError


class JsonFileEvaluator(BaseEvaluator):
    """Read a precomputed JSON result. Useful for tests and offline debugging."""

    def __init__(self, json_path, threshold, score_key="score", pass_key="passed"):
        if not json_path:
            raise EvaluationError("JSON evaluator requires --evaluator_json.")
        self.json_path = json_path
        self.threshold = threshold
        self.score_key = score_key
        self.pass_key = pass_key

    def evaluate(self, video_path, prompt, metadata):
        with open(self.json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return EvaluationResult.from_mapping(
            payload,
            threshold=self.threshold,
            score_key=self.score_key,
            pass_key=self.pass_key,
        )


class ShellEvaluator(BaseEvaluator):
    """
    Execute an external autonomous-driving evaluator.

    The command is formatted with:
      {video_path}, {prompt}, {attempt_id}, {output_json}, {metadata_json}

    The evaluator may either write JSON to {output_json} or print JSON to stdout.
    """

    def __init__(
        self,
        command_template,
        threshold,
        output_dir,
        timeout_sec=3600,
        score_key="score",
        pass_key="passed",
    ):
        if not command_template:
            raise EvaluationError("Shell evaluator requires --evaluator_command.")
        self.command_template = command_template
        self.threshold = threshold
        self.output_dir = output_dir
        self.timeout_sec = timeout_sec
        self.score_key = score_key
        self.pass_key = pass_key

    def evaluate(self, video_path, prompt, metadata):
        os.makedirs(self.output_dir, exist_ok=True)
        attempt_id = metadata.get("attempt_id", 0)
        output_json = os.path.abspath(
            os.path.join(self.output_dir, f"attempt_{attempt_id:02d}_evaluation.json")
        )

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            metadata_json = f.name

        try:
            format_values = {
                "video_path": shlex.quote(os.path.abspath(video_path)),
                "prompt": shlex.quote(prompt),
                "attempt_id": attempt_id,
                "output_json": shlex.quote(output_json),
                "metadata_json": shlex.quote(metadata_json),
            }
            command = self._format_command(format_values)

            completed = subprocess.run(
                command,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_sec,
            )

            if completed.returncode != 0:
                raise EvaluationError(
                    "Evaluator command failed with code "
                    f"{completed.returncode}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )

            payload = self._load_payload(output_json, completed.stdout)
        finally:
            try:
                os.remove(metadata_json)
            except OSError:
                pass

        return EvaluationResult.from_mapping(
            payload,
            threshold=self.threshold,
            score_key=self.score_key,
            pass_key=self.pass_key,
        )

    def _load_payload(self, output_json, stdout):
        if os.path.exists(output_json):
            with open(output_json, "r", encoding="utf-8") as f:
                return json.load(f)

        start = stdout.find("{")
        end = stdout.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise EvaluationError(
                "Evaluator did not create output_json and stdout does not contain JSON."
            )
        return json.loads(stdout[start:end + 1])

    def _format_command(self, format_values):
        command = self.command_template
        for key, value in format_values.items():
            command = command.replace("{" + key + "}", str(value))
        return command


class PythonEvaluator(BaseEvaluator):
    """
    Call a Python function as evaluator.

    The callable should return a dict with at least a score field:
      evaluate(video_path: str, prompt: str, metadata: dict) -> dict
    """

    def __init__(self, callable_path, threshold, score_key="score", pass_key="passed"):
        if not callable_path:
            raise EvaluationError("Python evaluator requires --evaluator_python.")
        if ":" not in callable_path:
            raise EvaluationError("Python evaluator path must be 'module.submodule:function'.")
        module_name, function_name = callable_path.split(":", 1)
        module = importlib.import_module(module_name)
        self.func = getattr(module, function_name)
        self.threshold = threshold
        self.score_key = score_key
        self.pass_key = pass_key

    def evaluate(self, video_path, prompt, metadata):
        payload = self.func(video_path=video_path, prompt=prompt, metadata=metadata)
        return EvaluationResult.from_mapping(
            payload,
            threshold=self.threshold,
            score_key=self.score_key,
            pass_key=self.pass_key,
        )


def build_evaluator(args):
    evaluator_type = getattr(args, "evaluator_type", "shell")
    threshold = getattr(args, "target_score", 0.8)
    score_key = getattr(args, "evaluator_score_key", "score")
    pass_key = getattr(args, "evaluator_pass_key", "passed")

    if evaluator_type == "shell":
        return ShellEvaluator(
            command_template=getattr(args, "evaluator_command", None),
            threshold=threshold,
            output_dir=getattr(args, "evaluation_output_dir", "results/evaluations"),
            timeout_sec=getattr(args, "evaluator_timeout_sec", 3600),
            score_key=score_key,
            pass_key=pass_key,
        )
    if evaluator_type == "python":
        return PythonEvaluator(
            callable_path=getattr(args, "evaluator_python", None),
            threshold=threshold,
            score_key=score_key,
            pass_key=pass_key,
        )
    if evaluator_type == "json":
        return JsonFileEvaluator(
            json_path=getattr(args, "evaluator_json", None),
            threshold=threshold,
            score_key=score_key,
            pass_key=pass_key,
        )
    if evaluator_type == "perception":
        from driveloop.evaluation.perception_evaluator import PerceptionEvaluator

        return PerceptionEvaluator(
            threshold=threshold,
            output_dir=getattr(args, "evaluation_output_dir", "results/evaluations"),
            model_name=getattr(args, "perception_model", "yolo11m.pt"),
            tracker=getattr(args, "perception_tracker", "botsort.yaml"),
            class_ids=getattr(args, "perception_classes", "0,1,2,3,5,7,9,11"),
            confidence=getattr(args, "perception_conf", 0.25),
            iou=getattr(args, "perception_iou", 0.50),
            image_size=getattr(args, "perception_imgsz", 1280),
            device=getattr(args, "perception_device", None),
        )
    raise EvaluationError(f"Unsupported evaluator_type: {evaluator_type}")
