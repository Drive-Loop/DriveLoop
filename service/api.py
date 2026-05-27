import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from service.system_check import run_system_check
from service.task_queue import TaskQueueManager


app = FastAPI(title="LoopDrive Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

queue = TaskQueueManager(root_dir=str(ROOT), max_workers=1)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "loopdrive",
        "root_dir": str(ROOT),
        "task_count": len(queue.tasks),
    }


@app.get("/system/check")
def system_check(
    config_yaml: str = "config/3dgs-waymo-1137.yaml",
    generation_backend: str = "native_chatsim",
    backend_workdir: Optional[str] = None,
    backend_command: Optional[str] = None,
    perception_model: str = "yolo11m.pt",
):
    return run_system_check(
        root_dir=str(ROOT),
        config_yaml=_normalize_config_path(config_yaml),
        generation_backend=generation_backend,
        backend_workdir=backend_workdir,
        backend_command=backend_command,
        perception_model=perception_model,
    )


@app.get("/tasks")
def list_tasks():
    tasks = list(queue.list_tasks().values())
    tasks.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"tasks": tasks}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    record = queue.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return record.to_dict()


@app.post("/tasks")
async def submit_task(
    prompt: str = Form(""),
    config_yaml: str = Form("config/3dgs-waymo-1137.yaml"),
    simulation_name: str = Form("api_demo"),
    generation_backend: str = Form("native_chatsim"),
    backend_command: Optional[str] = Form(None),
    backend_workdir: Optional[str] = Form(None),
    closed_loop: bool = Form(False),
    target_score: float = Form(0.8),
    max_attempts: int = Form(3),
    evaluator_type: str = Form("shell"),
    long_tail_scenarios: str = Form(""),
    weather_strength: float = Form(0.45),
    openai_api_key: Optional[str] = Form(None),
    audio_files: Optional[List[UploadFile]] = File(None),
    reference_images: Optional[List[UploadFile]] = File(None),
    reference_videos: Optional[List[UploadFile]] = File(None),
    reference_sketches: Optional[List[UploadFile]] = File(None),
):
    task_id = os.urandom(8).hex()
    audio_paths = await _save_uploaded_list(task_id, "audio", audio_files or [])
    image_paths = await _save_uploaded_list(task_id, "images", reference_images or [])
    video_paths = await _save_uploaded_list(task_id, "videos", reference_videos or [])
    sketch_paths = await _save_uploaded_list(task_id, "sketches", reference_sketches or [])

    request_payload = {
        "prompt": prompt,
        "config_yaml": _normalize_config_path(config_yaml),
        "simulation_name": simulation_name,
        "generation_backend": generation_backend,
        "backend_command": backend_command,
        "backend_workdir": backend_workdir,
        "closed_loop": closed_loop,
        "target_score": target_score,
        "max_attempts": max_attempts,
        "evaluator_type": evaluator_type,
        "long_tail_scenarios": long_tail_scenarios,
        "weather_strength": weather_strength,
        "audio_prompt_paths": audio_paths or None,
        "reference_image_paths": image_paths or None,
        "reference_video_paths": video_paths or None,
        "reference_sketch_paths": sketch_paths or None,
    }

    record = queue.submit(
        request_payload=request_payload,
        openai_api_key=openai_api_key,
        task_id=task_id,
    )
    return record.to_dict()


async def _save_uploaded_list(task_id: str, category: str, files: List[UploadFile]) -> List[str]:
    saved_paths: List[str] = []
    for file_obj in files:
        data = await file_obj.read()
        if not data:
            continue
        saved_paths.append(queue.save_upload(task_id, category, file_obj.filename or f"{category}.bin", data))
    return saved_paths


def _normalize_config_path(config_yaml: str) -> str:
    candidate = Path(config_yaml)
    if candidate.is_absolute():
        return str(candidate)
    return str((ROOT / config_yaml).resolve())
