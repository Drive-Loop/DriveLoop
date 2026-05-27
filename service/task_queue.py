import contextlib
import copy
import datetime as dt
import io
import json
import os
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import openai

from main import make_args, run_pipeline


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


@dataclass
class TaskRecord:
    task_id: str
    status: str
    created_at: str
    request: Dict[str, Any]
    updated_at: str = field(default_factory=_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    traceback_text: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    logs: str = ""
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "request": self.request,
            "error": self.error,
            "traceback": self.traceback_text,
            "result": self.result,
            "logs": self.logs,
            "artifacts": self.artifacts,
        }


class TaskQueueManager:
    """
    Simple in-process task queue for GPU-bound generation jobs.

    We keep max_workers=1 by default so a single GPU server does not try to run
    multiple heavy rendering jobs at once.
    """

    def __init__(self, root_dir: str, max_workers: int = 1):
        self.root_dir = Path(root_dir).resolve()
        self.state_dir = self.root_dir / "results" / "service_tasks"
        self.upload_dir = self.root_dir / "results" / "service_uploads"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()
        self.tasks: Dict[str, TaskRecord] = {}
        self._load_existing_tasks()

    def submit(
        self,
        request_payload: Dict[str, Any],
        openai_api_key: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> TaskRecord:
        task_id = task_id or uuid.uuid4().hex
        record = TaskRecord(
            task_id=task_id,
            status="queued",
            created_at=_now_iso(),
            request=copy.deepcopy(request_payload),
        )
        with self.lock:
            self.tasks[task_id] = record
            self._persist(record)
        self.executor.submit(self._run_task, task_id, copy.deepcopy(request_payload), openai_api_key)
        return copy.deepcopy(record)

    def get(self, task_id: str) -> Optional[TaskRecord]:
        with self.lock:
            record = self.tasks.get(task_id)
            return copy.deepcopy(record) if record else None

    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        with self.lock:
            return {task_id: copy.deepcopy(record).to_dict() for task_id, record in self.tasks.items()}

    def save_upload(self, task_id: str, category: str, filename: str, data: bytes) -> str:
        target_dir = self.upload_dir / task_id / category
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename or f"{category}.bin").name
        path = target_dir / safe_name
        with open(path, "wb") as f:
            f.write(data)
        return str(path.resolve())

    def _run_task(self, task_id: str, request_payload: Dict[str, Any], openai_api_key: Optional[str]) -> None:
        self._update(task_id, status="running", started_at=_now_iso())
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        try:
            if openai_api_key:
                openai.api_key = openai_api_key
            args = make_args(request_payload)
            with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
                result = run_pipeline(args)
            logs = stdout_buffer.getvalue()
            if stderr_buffer.getvalue().strip():
                logs = logs + "\n" + stderr_buffer.getvalue()
            artifacts = self._collect_artifacts(result)
            self._update(
                task_id,
                status="succeeded",
                completed_at=_now_iso(),
                result=result,
                logs=logs,
                artifacts=artifacts,
            )
        except Exception as exc:
            logs = stdout_buffer.getvalue()
            if stderr_buffer.getvalue().strip():
                logs = logs + "\n" + stderr_buffer.getvalue()
            self._update(
                task_id,
                status="failed",
                completed_at=_now_iso(),
                error=str(exc),
                traceback_text="".join(traceback.format_exception(exc)),
                logs=logs,
            )

    def _collect_artifacts(self, result: Dict[str, Any]) -> Dict[str, Any]:
        artifacts = {}
        for key in ["video_path", "manifest_path"]:
            value = result.get(key)
            if value:
                artifacts[key] = value
        prompt_conditioning = result.get("prompt_conditioning") or {}
        transcripts = prompt_conditioning.get("audio_transcripts") or []
        if transcripts:
            artifacts["audio_transcripts"] = transcripts
        return artifacts

    def _update(self, task_id: str, **fields: Any) -> None:
        with self.lock:
            record = self.tasks[task_id]
            for key, value in fields.items():
                setattr(record, key, value)
            record.updated_at = _now_iso()
            self._persist(record)

    def _persist(self, record: TaskRecord) -> None:
        path = self.state_dir / f"{record.task_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_existing_tasks(self) -> None:
        for path in sorted(self.state_dir.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                record = TaskRecord(
                    task_id=payload["task_id"],
                    status=payload["status"],
                    created_at=payload["created_at"],
                    updated_at=payload.get("updated_at", payload["created_at"]),
                    started_at=payload.get("started_at"),
                    completed_at=payload.get("completed_at"),
                    request=payload.get("request", {}),
                    error=payload.get("error"),
                    traceback_text=payload.get("traceback"),
                    result=payload.get("result"),
                    logs=payload.get("logs", ""),
                    artifacts=payload.get("artifacts", {}),
                )
                self.tasks[record.task_id] = record
            except Exception:
                continue
