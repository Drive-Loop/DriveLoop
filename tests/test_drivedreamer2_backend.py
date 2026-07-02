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
        "target_backend": "drivedreamer2_runtime",
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
        "target_dataset": "drivedreamer2_runtime",
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
    assert snapshot["sample"]["cam_intrinsic_shape"] is None
    assert snapshot["sample"]["cam_intrinsic"] is None
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

def test_drivedreamer2_backend_records_override_candidate_plan(monkeypatch, tmp_path):
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
        "image_hdmap": {
            "source": "runtime_dataset_baseline",
        },
        "image_box": {
            "source": "runtime_dataset_baseline",
        },
        "boxes3d": {
            "source": "runtime_dataset_baseline",
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
    plan = generation.metadata["dd2_override_candidate_plan"]

    assert plan["available"] is True
    assert plan["control_level"] == "tensor_override_runtime"
    assert plan["requires_box_synthesis"] is True
    assert plan["requires_hdmap_override"] is False
    assert plan["scene_description_action"]["type"] == "replace_text_prompt"
    assert plan["scene_description_action"]["target_value"] == structural_input_plan["scene_description"]["value"]
    assert {"type": "add_actor_label", "label": "bicycle"} in plan["actor_label_actions"]
    assert {"type": "add_actor_label", "label": "pedestrian"} in plan["actor_label_actions"]
    assert {"type": "mark_extra_baseline_label", "label": "car"} in plan["actor_label_actions"]
    assert "box_positions_are_draft_until_projection_and_scene_geometry_are_verified" in plan["limitations"]

def test_override_candidate_plan_includes_box_synthesis_plan_for_missing_actor():
    backend = DriveDreamer2Backend()

    structural_input_plan = {
        "image_hdmap": {"source": "runtime_dataset_baseline"},
        "image_box": {"source": "runtime_dataset_baseline"},
        "boxes3d": {"source": "runtime_dataset_baseline"},
    }
    structural_request_diff = {
        "available": True,
        "missing_requested_labels": ["bicycle"],
        "extra_baseline_labels": ["car"],
        "requested_scene_description": "rainy night intersection with a bicycle cut in",
        "baseline_scene_description": "clear road with a car",
        "scene_description_changed": True,
    }

    plan = backend._build_override_candidate_plan(
        structural_input_plan=structural_input_plan,
        structural_request_diff=structural_request_diff,
    )

    box_plan = plan["box_synthesis_plan"]

    assert box_plan["available"] is True
    assert box_plan["control_level"] == "tensor_override_runtime"
    assert box_plan["requires_manual_review"] is True
    assert box_plan["target_tensor"] == "boxes3d"
    assert box_plan["derived_tensor"] == "image_box"
    assert box_plan["placement_policy"] == "front_adjacent_lane_cut_in"
    assert box_plan["box_template_source"] == "class_default_dimensions"
    assert box_plan["actors_to_synthesize"] == [
        {
            "category": "bicycle",
            "source_action": "add_actor_label",
            "confidence": "low",
            "reason": "missing_requested_label",
        }
    ]
    assert "3d_position_uses_audited_draft_policy" in box_plan["limitations"]

def test_box_synthesis_plan_includes_draft_box_for_bicycle():
    backend = DriveDreamer2Backend()

    structural_request_diff = {
        "missing_requested_labels": ["bicycle"],
        "extra_baseline_labels": [],
    }

    box_plan = backend._build_box_synthesis_plan(
        structural_request_diff=structural_request_diff,
        requires_box_synthesis=True,
    )

    draft = box_plan["box_synthesis_draft"]

    assert draft["available"] is True
    assert draft["control_level"] == "draft_only"
    assert draft["coordinate_frame"] == "dd2_dataset_frame_unverified"
    assert draft["coordinate_frame_verified"] is False
    assert draft["units"] == "meters"
    assert draft["boxes3d_format"] == "x_y_z_width_height_depth_rotX_rotY_rotZ"
    assert draft["default_dimensions"]["bicycle"] == {
        "width": 0.6,
        "height": 1.6,
        "depth": 1.8,
    }
    assert draft["draft_boxes3d"] == [
        {
            "category": "bicycle",
            "box3d": [8.0, 1.8, 18.0, 0.6, 1.6, 1.8, 0.0, 0.0, -0.25],
            "placement_policy": "front_adjacent_lane_cut_in",
            "source": "class_default_dimensions",
            "requires_projection": True,
        }
    ]
    validation = draft["validation"]
    assert validation["control_level"] == "validator_only"
    assert validation["all_entries_valid"] is True
    assert validation["entries"] == [
        {
            "category": "bicycle",
            "shape_ok": True,
            "float32_convertible": True,
            "dimensions_positive": True,
            "mean_z_positive": True,
            "projection_finite": None,
            "projected_2d_range": None,
            "requires_projection_validation": True,
            "image_box_canvas_dry_run": {
                "control_level": "validator_only",
                "target_shape": [19, 900, 1600],
                "class_channel": 5,
                "projected_box_drawable": None,
                "projected_2d_range": None,
                "canvas_rendered": False,
                "dataset_written": False,
            },
        }
    ]
    assert validation["projection_control_level"] == "not_run"
    assert "projection_not_run" in validation["limitations"]
    assert "written_to_runtime_sample_only" in draft["limitations"]



def test_box_synthesis_draft_validator_projects_with_baseline_intrinsic():
    backend = DriveDreamer2Backend()

    draft = backend._build_box_synthesis_draft(
        actors_to_synthesize=[
            {
                "category": "bicycle",
                "source_action": "add_actor_label",
                "confidence": "low",
                "reason": "missing_requested_label",
            }
        ],
        placement_policy="front_adjacent_lane_cut_in",
        box_template_source="class_default_dimensions",
        baseline_structural_snapshot={
            "sample": {
                "cam_intrinsic": [
                    [1252.8131, 0.0, 826.5881, 0.0],
                    [0.0, 1252.8131, 469.9846, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ]
            }
        },
    )

    validation = draft["validation"]
    entry = validation["entries"][0]

    assert validation["projection_control_level"] == "validator_only"
    assert validation["all_entries_valid"] is True
    assert entry["projection_finite"] is True
    assert entry["requires_projection_validation"] is False
    assert entry["projected_2d_range"] == {
        "min": [1336.99, 536.27],
        "max": [1434.68, 660.47],
    }
    assert entry["image_box_canvas_dry_run"] == {
        "control_level": "validator_only",
        "target_shape": [19, 900, 1600],
        "class_channel": 5,
        "projected_box_drawable": True,
        "projected_2d_range": {
            "min": [1336.99, 536.27],
            "max": [1434.68, 660.47],
        },
        "canvas_rendered": False,
        "dataset_written": False,
    }
    assert "projection_validator_uses_axis_aligned_corners" in validation["limitations"]
    assert "dataset_not_written" in validation["limitations"]


def test_drivedreamer2_backend_builds_paper_alignment_report_for_plan_only_control():
    from driveloop.backends.drivedreamer2 import DriveDreamer2Backend

    backend = DriveDreamer2Backend()
    report = backend._build_paper_alignment_report(
        dd2_prompt="A delivery van swerves around a fallen traffic barrier.",
        executable_condition={
            "actor_controls": [
                {"category": "car", "source_category": "delivery_van"},
                {"category": "barrier", "source_category": "traffic_barrier"},
            ],
            "environment_controls": {"weather": "snow", "lighting": "dawn"},
            "risk_controls": {"long_tail_tags": ["snow", "road_obstacle"]},
        },
        trace_metadata={
            "tensor_control_ready": False,
            "limitations": ["actor_box_tensor_control_not_connected"],
        },
        structural_input_plan={"control_level": "plan_only"},
        structural_request_diff={"missing_requested_labels": ["barrier"]},
        override_candidate_plan={"requires_box_synthesis": True},
    )

    assert report["schema_version"] == "driveloop_paper_alignment_report.v0"
    assert report["stage_1_multimodal_prompt_grounding"]["dd2_text_prompt_available"] is True
    assert report["stage_2_long_tail_conditioning"]["status"] == "available"
    assert report["stage_3_scene_consistent_generation"]["status"] == "text_and_plan_only"
    assert report["stage_3_scene_consistent_generation"]["tensor_control_ready"] is False
    assert report["experiment_readiness"]["main_experiment_ready"] is False
    assert report["experiment_readiness"]["allowed_use"] == "prototype_trace_and_ablation_only"


def test_drivedreamer2_backend_builds_barrier_box_synthesis_draft():
    from driveloop.backends.drivedreamer2 import DriveDreamer2Backend

    backend = DriveDreamer2Backend()
    draft = backend._build_box_synthesis_draft(
        [{"category": "barrier", "source_action": "add_actor_label"}],
        "front_adjacent_lane_obstacle",
        "class_default_dimensions",
    )

    assert draft["available"] is True
    assert draft["control_level"] == "draft_only"
    assert draft["coordinate_frame_verified"] is False
    assert draft["draft_boxes3d"][0]["category"] == "barrier"
    assert draft["draft_boxes3d"][0]["requires_projection"] is True
    assert draft["validation"]["available"] is True
    assert draft["validation"]["all_entries_valid"] is True
    assert draft["validation"]["entries"][0]["image_box_canvas_dry_run"]["dataset_written"] is False
    assert "dataset_not_written" in draft["validation"]["limitations"]


def test_box_synthesis_plan_includes_draft_box_for_motorcycle():
    from driveloop.backends.drivedreamer2 import DriveDreamer2Backend

    backend = DriveDreamer2Backend()

    box_plan = backend._build_box_synthesis_plan(
        structural_request_diff={
            "missing_requested_labels": ["motorcycle"],
            "extra_baseline_labels": [],
        },
        requires_box_synthesis=True,
    )

    draft = box_plan["box_synthesis_draft"]

    assert draft["available"] is True
    assert draft["default_dimensions"]["motorcycle"] == {
        "width": 0.8,
        "height": 1.5,
        "depth": 2.2,
    }
    assert draft["draft_boxes3d"] == [
        {
            "category": "motorcycle",
            "box3d": [8.0, 1.8, 18.0, 0.8, 1.5, 2.2, 0.0, 0.0, -0.25],
            "placement_policy": "front_adjacent_lane_cut_in",
            "source": "class_default_dimensions",
            "requires_projection": True,
        }
    ]
    assert draft["validation"]["all_entries_valid"] is True
    assert draft["validation"]["entries"][0]["image_box_canvas_dry_run"]["class_channel"] == 6


def test_backend_passes_batch_skip_to_dd2_environment(tmp_path, monkeypatch):
    import json
    import subprocess

    from driveloop.backends.drivedreamer2 import DriveDreamer2Backend
    from driveloop.schema import DriveLoopRequest

    captured = {}

    def fake_run(cmd, cwd, env, check, text, timeout):
        captured["env"] = env
        baseline = tmp_path / "baseline" / "000000.mp4"
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_bytes(b"video")
        audit_path = env.get("DRIVELOOP_DD2_AUDIT_PATH")
        if audit_path:
            Path(audit_path).write_text(
                json.dumps({"schema_version": "dd2_runtime_input_audit.v0"}),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    backend = DriveDreamer2Backend(
        project_root=tmp_path,
        baseline_output_dir=tmp_path / "baseline",
        baseline_dataset_dir=tmp_path / "missing_dataset",
        artifact_dir=tmp_path / "artifacts",
        batch_skip=3,
    )

    generation = backend.generate(
        DriveLoopRequest(
            prompt="daytime urban multi-lane road with a motorcycle lane change",
            scenario_id="case",
            condition={},
        ),
        iteration=0,
    )

    assert captured["env"]["DRIVELOOP_DD2_BATCH_SKIP"] == "3"
    assert generation.metadata["dd2_batch_skip"] == 3


def test_drivedreamer2_runner_exposes_audit_only_and_batch_skip():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/run_driveloop_drivedreamer2.py", "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "--audit-only" in result.stdout
    assert "--dd2-batch-skip" in result.stdout


def test_drivedreamer2_runner_passes_audit_only_and_batch_skip_to_backend():
    script = Path("scripts/run_driveloop_drivedreamer2.py").read_text(encoding="utf-8")

    assert "audit_only=args.audit_only" in script
    assert "batch_skip=args.dd2_batch_skip" in script


def test_dd2_tester_batch_skip_uses_targeted_subset_before_gpu_transfer():
    script = Path("dreamer-train/projects/DriveDreamer2/drivedreamer2/drivedreamer2_tester.py").read_text(
        encoding="utf-8"
    )

    assert "def _driveloop_selected_video_indices" in script
    assert '"DRIVELOOP_DD2_BATCH_SKIP" in os.environ' in script
    assert "selected_dataset = torch.utils.data.Subset(dataset, selected_indices)" in script
    assert "self.dd2_sampler_selected_batch_index = target_batch_skip" in script
    assert "batch_skip = 0 if sampler_selected_batch_index is not None else" in script
    assert '"selected_batch_index": sampler_selected_batch_index if sampler_selected_batch_index is not None else batch_i' in script
    assert "if batch_i < batch_skip:" in script



def test_drivedreamer2_runner_exposes_baseline_dataset_dir():
    script = Path("scripts/run_driveloop_drivedreamer2.py").read_text(encoding="utf-8")

    assert 'parser.add_argument("--baseline-dataset-dir", default=None)' in script
    assert "baseline_dataset_dir=args.baseline_dataset_dir or" in script


def test_drivedreamer2_runner_exposes_baseline_output_dir():
    script = Path("scripts/run_driveloop_drivedreamer2.py").read_text(encoding="utf-8")

    assert 'parser.add_argument("--baseline-output-dir", default=None)' in script
    assert "baseline_output_dir=args.baseline_output_dir or" in script
