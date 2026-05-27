import importlib.util
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml


def run_system_check(
    root_dir: str,
    config_yaml: Optional[str] = None,
    generation_backend: str = "native_chatsim",
    backend_workdir: Optional[str] = None,
    backend_command: Optional[str] = None,
    perception_model: Optional[str] = None,
) -> Dict[str, object]:
    root = Path(root_dir).resolve()
    checks: List[Dict[str, str]] = []

    def add(name: str, status: str, detail: str, path: Optional[Path] = None):
        item = {
            "name": name,
            "status": status,
            "detail": detail,
        }
        if path is not None:
            item["path"] = str(path)
        checks.append(item)

    add("service_root", "pass", "Project root is available.", root)
    _check_import("openai", "OpenAI Python package", add)
    _check_import("streamlit", "Streamlit package", add)
    _check_import("fastapi", "FastAPI package", add)
    _check_import("ultralytics", "Ultralytics package", add)

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        add("openai_key", "pass", "OPENAI_API_KEY is present in the environment.")
    else:
        add("openai_key", "warn", "OPENAI_API_KEY is not set. Users will need to provide a key per request.")

    for rel in ["results", "results/service_tasks", "results/service_uploads", "results/frontend_history"]:
        target = root / rel
        try:
            target.mkdir(parents=True, exist_ok=True)
            add(f"writable:{rel}", "pass", "Directory is writable.", target)
        except Exception as exc:
            add(f"writable:{rel}", "fail", f"Directory is not writable: {exc}", target)

    config_path = _normalize_config_path(root, config_yaml or "config/3dgs-waymo-1137.yaml")
    if not config_path.exists():
        add("config_file", "fail", "Config YAML file does not exist.", config_path)
        return _finalize(checks)

    add("config_file", "pass", "Config YAML file found.", config_path)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        add("config_parse", "pass", "Config YAML parsed successfully.", config_path)
    except Exception as exc:
        add("config_parse", "fail", f"Config YAML could not be parsed: {exc}", config_path)
        return _finalize(checks)

    _check_scene_assets(root, config, add)
    _check_backend(root, generation_backend, backend_workdir, backend_command, add)
    _check_perception_model(root, perception_model or "yolo11m.pt", add)

    return _finalize(checks)


def _normalize_config_path(root: Path, config_yaml: str) -> Path:
    candidate = Path(config_yaml)
    if candidate.is_absolute():
        return candidate
    return (root / candidate).resolve()


def _check_import(module_name: str, label: str, add):
    if importlib.util.find_spec(module_name) is not None:
        add(f"import:{module_name}", "pass", f"{label} is importable.")
    else:
        add(f"import:{module_name}", "fail", f"{label} is missing from the environment.")


def _check_scene_assets(root: Path, config: Dict[str, object], add):
    scene = (config or {}).get("scene") or {}
    agents = (config or {}).get("agents") or {}
    scene_name = scene.get("scene_name")
    data_root = scene.get("data_root")

    if not scene_name or not data_root:
        add("scene_config", "fail", "Config is missing scene.scene_name or scene.data_root.")
        return

    scene_dir = (root / str(data_root) / str(scene_name)).resolve()
    if scene_dir.exists():
        add("scene_dir", "pass", "Scene directory found.", scene_dir)
    else:
        add("scene_dir", "fail", "Scene directory is missing.", scene_dir)

    required_scene_files = {
        "ext_int_file": scene.get("ext_int_file"),
        "bbox_file": scene.get("bbox_file"),
        "map_file": scene.get("map_file"),
        "pcd_file": scene.get("pcd_file"),
    }
    for key, relative in required_scene_files.items():
        if not relative:
            add(f"scene_file:{key}", "warn", f"{key} is not configured.")
            continue
        path = scene_dir / str(relative)
        if path.exists():
            add(f"scene_file:{key}", "pass", f"{key} found.", path)
        else:
            add(f"scene_file:{key}", "fail", f"{key} is missing.", path)

    init_img = scene.get("init_img_file")
    if init_img:
        init_img_path = scene_dir / str(init_img)
        if init_img_path.exists():
            add("scene_file:init_img", "pass", "Initial image found.", init_img_path)
        else:
            add("scene_file:init_img", "warn", "Initial image is missing. The pipeline may regenerate it.", init_img_path)

    asset_cfg = agents.get("asset_select_agent") or {}
    assets_dir = root / str(asset_cfg.get("assets_dir", ""))
    if assets_dir.exists():
        add("assets_dir", "pass", "Blender assets directory found.", assets_dir)
    else:
        add("assets_dir", "fail", "Blender assets directory is missing.", assets_dir)

    fg_cfg = agents.get("foreground_rendering_agent") or {}
    skydome_dir = root / str(fg_cfg.get("skydome_hdri_dir", ""))
    if skydome_dir.exists():
        add("skydome_dir", "pass", "Skydome HDRI directory found.", skydome_dir)
        scene_hdri_dir = skydome_dir / str(scene_name)
        if scene_hdri_dir.exists():
            add("skydome_scene_dir", "pass", "Scene-specific HDRI directory found.", scene_hdri_dir)
        else:
            add("skydome_scene_dir", "warn", "Scene-specific HDRI directory is missing.", scene_hdri_dir)
    else:
        add("skydome_dir", "fail", "Skydome HDRI directory is missing.", skydome_dir)

    blender_dir = root / str(fg_cfg.get("blender_dir", ""))
    if blender_dir.exists():
        if os.access(blender_dir, os.X_OK):
            add("blender_bin", "pass", "Blender executable found.", blender_dir)
        else:
            add("blender_bin", "warn", "Blender path exists but is not executable.", blender_dir)
    else:
        add("blender_bin", "fail", "Blender executable is missing.", blender_dir)

    blender_utils_dir = root / str(fg_cfg.get("blender_utils_dir", ""))
    if blender_utils_dir.exists():
        add("blender_utils", "pass", "Blender utils directory found.", blender_utils_dir)
    else:
        add("blender_utils", "fail", "Blender utils directory is missing.", blender_utils_dir)

    bg_cfg = agents.get("background_rendering_agent") or {}
    scene_representation = str(bg_cfg.get("scene_representation", "")).lower()
    if scene_representation == "3dgs":
        gs_cfg = bg_cfg.get("gs_config") or {}
        gs_dir = root / str(gs_cfg.get("gs_dir", ""))
        if gs_dir.exists():
            add("3dgs_code", "pass", "3DGS code directory found.", gs_dir)
        else:
            add("3dgs_code", "fail", "3DGS code directory is missing.", gs_dir)

        output_folder = gs_cfg.get("output_folder")
        gs_model_name = gs_cfg.get("gs_model_name")
        if output_folder and gs_model_name:
            model_dir = gs_dir / str(output_folder) / str(gs_model_name)
            if model_dir.exists():
                add("3dgs_model", "pass", "3DGS model directory found.", model_dir)
            else:
                add("3dgs_model", "warn", "3DGS model directory is missing. Inference may fail until it is prepared.", model_dir)
    else:
        nerf_cfg = bg_cfg.get("nerf_config") or {}
        f2nerf_dir = root / str(nerf_cfg.get("f2nerf_dir", ""))
        if f2nerf_dir.exists():
            add("mcnerf_code", "pass", "McNeRF/F2NeRF directory found.", f2nerf_dir)
        else:
            add("mcnerf_code", "fail", "McNeRF/F2NeRF directory is missing.", f2nerf_dir)


def _check_backend(root: Path, generation_backend: str, backend_workdir: Optional[str], backend_command: Optional[str], add):
    if generation_backend == "magicdrive_v2":
        if backend_command:
            add("magicdrive_command", "pass", "MagicDrive-V2 command template provided.")
        else:
            add("magicdrive_command", "warn", "MagicDrive-V2 command template is empty.")

        if backend_workdir:
            workdir = Path(backend_workdir)
            if not workdir.is_absolute():
                workdir = (root / workdir).resolve()
            if workdir.exists():
                add("magicdrive_workdir", "pass", "MagicDrive-V2 workdir found.", workdir)
            else:
                add("magicdrive_workdir", "fail", "MagicDrive-V2 workdir is missing.", workdir)
        else:
            add("magicdrive_workdir", "warn", "MagicDrive-V2 workdir is not set.")
    else:
        add("generation_backend", "pass", f"Using {generation_backend} backend.")


def _check_perception_model(root: Path, perception_model: str, add):
    model_path = Path(perception_model)
    if model_path.is_absolute() or len(model_path.parts) > 1:
        resolved = model_path if model_path.is_absolute() else (root / model_path).resolve()
        if resolved.exists():
            add("perception_model", "pass", "Perception model file found.", resolved)
        else:
            add("perception_model", "warn", "Perception model file is missing. Ultralytics may try to download it on first use.", resolved)
    else:
        add(
            "perception_model",
            "warn",
            f"Perception model '{perception_model}' is referenced by name only. Make sure the server can download it or provide a local path.",
        )


def _finalize(checks: List[Dict[str, str]]) -> Dict[str, object]:
    summary = {"passed": 0, "warnings": 0, "failed": 0}
    for item in checks:
        if item["status"] == "pass":
            summary["passed"] += 1
        elif item["status"] == "warn":
            summary["warnings"] += 1
        else:
            summary["failed"] += 1

    if summary["failed"] > 0:
        status = "fail"
    elif summary["warnings"] > 0:
        status = "warn"
    else:
        status = "ok"

    return {
        "status": status,
        "summary": summary,
        "checks": checks,
    }
