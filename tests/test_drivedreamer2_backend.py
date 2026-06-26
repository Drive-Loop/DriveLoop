from pathlib import Path
from types import SimpleNamespace

from driveloop.backends.drivedreamer2 import DriveDreamer2Backend
from driveloop.schema import DriveLoopRequest


def test_drivedreamer2_backend_passes_condition_prompt_to_subprocess_env(monkeypatch, tmp_path):
    captured = {}

    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    baseline_video = baseline_output_dir / "000000.mp4"

    def fake_run(cmd, cwd, env, check, text, timeout):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["env"] = env
        baseline_video.write_bytes(b"fake video")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)

    backend = DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=baseline_output_dir,
        artifact_dir=tmp_path / "artifacts",
        python_executable="python",
        timeout_seconds=123,
    )
    request = DriveLoopRequest(
        prompt="base prompt",
        condition={
            "dd2_condition": {
                "text_prompt": "foggy night autonomous driving scene with cyclist cut in."
            }
        },
    )

    generation = backend.generate(request, iteration=0)

    assert captured["env"]["DRIVELOOP_DD2_PROMPT"] == (
        "foggy night autonomous driving scene with cyclist cut in."
    )
    assert captured["env"]["PYTORCH_CUDA_ALLOC_CONF"] == "expandable_segments:True"
    assert generation.artifacts["video"].endswith("iteration_00.mp4")
    assert Path(generation.artifacts["video"]).exists()
    assert generation.metadata["returncode"] == 0
