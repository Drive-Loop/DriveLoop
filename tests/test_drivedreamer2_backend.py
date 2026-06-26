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

def test_drivedreamer2_backend_records_executable_condition_metadata(monkeypatch, tmp_path):
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    baseline_video = baseline_output_dir / "000000.mp4"

    def fake_run(cmd, cwd, env, check, text, timeout):
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
    executable_condition = {
        "schema_version": "dd2_executable_condition.v0",
        "target_backend": "drivedreamer2_mini",
        "trace_metadata": {
            "structural_control_level": "schema_only",
            "tensor_control_ready": False,
        },
    }
    request = DriveLoopRequest(
        prompt="base prompt",
        condition={
            "dd2_condition": {
                "text_prompt": "foggy night autonomous driving scene with cyclist cut in.",
                "executable_condition": executable_condition,
            }
        },
    )

    generation = backend.generate(request, iteration=0)

    assert generation.metadata["dd2_prompt"] == "foggy night autonomous driving scene with cyclist cut in."
    assert generation.metadata["dd2_executable_condition"] == executable_condition
    assert generation.metadata["dd2_condition_schema_version"] == "dd2_executable_condition.v0"
    assert generation.metadata["dd2_tensor_control_ready"] is False

def test_drivedreamer2_backend_records_structural_input_plan_metadata(monkeypatch, tmp_path):
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    baseline_video = baseline_output_dir / "000000.mp4"

    def fake_run(cmd, cwd, env, check, text, timeout):
        baseline_video.write_bytes(b"fake video")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)

    structural_input_plan = {
        "target_dataset": "drivedreamer2_mini",
        "control_level": "plan_only",
        "labels": {
            "source": "actor_controls.category",
            "values": ["car", "pedestrian"],
        },
    }
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
                "text_prompt": "rainy night autonomous driving scene.",
                "executable_condition": {
                    "schema_version": "dd2_executable_condition.v0",
                    "structural_input_plan": structural_input_plan,
                    "trace_metadata": {
                        "tensor_control_ready": False,
                    },
                },
            }
        },
    )

    generation = backend.generate(request, iteration=0)

    assert generation.metadata["dd2_structural_input_plan"] == structural_input_plan
    assert generation.metadata["dd2_structural_control_level"] == "plan_only"

def test_drivedreamer2_backend_records_baseline_structural_snapshot(monkeypatch, tmp_path):
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    baseline_video = baseline_output_dir / "000000.mp4"

    dataset_root = tmp_path / "mini_dataset"
    labels_dir = dataset_root / "labels"
    images_dir = dataset_root / "images"
    hdmaps_dir = dataset_root / "hdmaps"
    labels_dir.mkdir(parents=True)
    images_dir.mkdir()
    hdmaps_dir.mkdir()

    (dataset_root / "config.json").write_text(
        '{"_class_name": "Dataset", "config_paths": ["labels/config.json", "images/config.json", "hdmaps/config.json"]}',
        encoding="utf-8",
    )
    (labels_dir / "config.json").write_text(
        '{"_class_name": "PklDataset", "_key_names": ["boxes3d", "ori_labels3d", "scene_description"], "data_size": 1}',
        encoding="utf-8",
    )
    (images_dir / "config.json").write_text(
        '{"_class_name": "LmdbDataset", "_key_names": ["image"], "data_size": 1, "data_type": "image", "data_name": "image"}',
        encoding="utf-8",
    )
    (hdmaps_dir / "config.json").write_text(
        '{"_class_name": "LmdbDataset", "_key_names": ["image_hdmap"], "data_size": 1, "data_type": "image", "data_name": "image_hdmap"}',
        encoding="utf-8",
    )

    import pickle
    import numpy as np

    with (labels_dir / "data.pkl").open("wb") as f:
        pickle.dump(
            [
                {
                    "scene_description": "Many peds right, cyclist",
                    "boxes3d": np.zeros((2, 9), dtype=np.float32),
                    "ori_labels3d": ["human.pedestrian.adult", "vehicle.bicycle"],
                    "labels3d": [["pedestrian", "adult"], ["vehicle", "bicycle"]],
                }
            ],
            f,
        )

    def fake_run(cmd, cwd, env, check, text, timeout):
        baseline_video.write_bytes(b"fake video")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)

    backend = DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=baseline_output_dir,
        baseline_dataset_dir=dataset_root,
        artifact_dir=tmp_path / "artifacts",
        python_executable="python",
        timeout_seconds=123,
    )

    generation = backend.generate(DriveLoopRequest(prompt="base prompt"), iteration=0)
    snapshot = generation.metadata["dd2_baseline_structural_snapshot"]

    assert snapshot["dataset_dir"] == str(dataset_root)
    assert snapshot["dataset_config"]["class_name"] == "Dataset"
    assert snapshot["labels_config"]["data_size"] == 1
    assert snapshot["images_config"]["data_name"] == "image"
    assert snapshot["hdmaps_config"]["data_name"] == "image_hdmap"
    assert snapshot["sample"]["scene_description"] == "Many peds right, cyclist"
    assert snapshot["sample"]["boxes3d_shape"] == [2, 9]
    assert snapshot["sample"]["boxes3d_dtype"] == "float32"
    assert snapshot["sample"]["ori_labels3d_count"] == 2
    assert snapshot["sample"]["ori_labels3d_preview"] == ["human.pedestrian.adult", "vehicle.bicycle"]

def test_drivedreamer2_backend_records_requested_vs_baseline_structural_diff(monkeypatch, tmp_path):
    baseline_output_dir = tmp_path / "baseline"
    baseline_output_dir.mkdir()
    baseline_video = baseline_output_dir / "000000.mp4"

    dataset_root = tmp_path / "mini_dataset"
    labels_dir = dataset_root / "labels"
    images_dir = dataset_root / "images"
    hdmaps_dir = dataset_root / "hdmaps"
    labels_dir.mkdir(parents=True)
    images_dir.mkdir()
    hdmaps_dir.mkdir()

    (dataset_root / "config.json").write_text(
        '{"_class_name": "Dataset", "config_paths": ["labels/config.json", "images/config.json", "hdmaps/config.json"]}',
        encoding="utf-8",
    )
    (labels_dir / "config.json").write_text(
        '{"_class_name": "PklDataset", "_key_names": ["boxes3d", "ori_labels3d", "scene_description"], "data_size": 1}',
        encoding="utf-8",
    )
    (images_dir / "config.json").write_text(
        '{"_class_name": "LmdbDataset", "_key_names": ["image"], "data_size": 1, "data_type": "image", "data_name": "image"}',
        encoding="utf-8",
    )
    (hdmaps_dir / "config.json").write_text(
        '{"_class_name": "LmdbDataset", "_key_names": ["image_hdmap"], "data_size": 1, "data_type": "image", "data_name": "image_hdmap"}',
        encoding="utf-8",
    )

    import pickle
    import numpy as np

    with (labels_dir / "data.pkl").open("wb") as f:
        pickle.dump(
            [
                {
                    "scene_description": "clear daytime road with a car",
                    "boxes3d": np.zeros((1, 9), dtype=np.float32),
                    "ori_labels3d": ["vehicle.car"],
                    "labels3d": [["vehicle", "car"]],
                }
            ],
            f,
        )

    def fake_run(cmd, cwd, env, check, text, timeout):
        baseline_video.write_bytes(b"fake video")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("driveloop.backends.drivedreamer2.subprocess.run", fake_run)

    structural_input_plan = {
        "scene_description": {
            "value": "rainy night intersection with a pedestrian crossing and a bicycle cut in"
        },
        "labels": {
            "values": ["pedestrian", "bicycle"],
        },
    }

    backend = DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=baseline_output_dir,
        baseline_dataset_dir=dataset_root,
        artifact_dir=tmp_path / "artifacts",
        python_executable="python",
        timeout_seconds=123,
    )
    request = DriveLoopRequest(
        prompt="base prompt",
        condition={
            "dd2_condition": {
                "text_prompt": "rainy night intersection with a pedestrian crossing and a bicycle cut in",
                "executable_condition": {
                    "schema_version": "dd2_executable_condition.v0",
                    "structural_input_plan": structural_input_plan,
                    "trace_metadata": {"tensor_control_ready": False},
                },
            }
        },
    )

    generation = backend.generate(request, iteration=0)
    diff = generation.metadata["dd2_structural_request_diff"]

    assert diff["available"] is True
    assert diff["requested_labels"] == ["pedestrian", "bicycle"]
    assert diff["baseline_labels"] == ["car"]
    assert diff["missing_requested_labels"] == ["bicycle", "pedestrian"]
    assert diff["extra_baseline_labels"] == ["car"]
    assert diff["requested_scene_description"] == structural_input_plan["scene_description"]["value"]
    assert diff["baseline_scene_description"] == "clear daytime road with a car"
    assert diff["scene_description_changed"] is True
    assert diff["tensor_override_ready"] is False

