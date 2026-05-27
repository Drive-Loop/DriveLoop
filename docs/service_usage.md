# LoopDrive Service API

The project now includes a lightweight FastAPI service layer with an in-process task queue.

## What it provides

- asynchronous task submission
- single-worker GPU-safe queue by default
- task status lookup
- task result lookup
- backend health endpoint for frontend connectivity checks
- file upload support for audio, reference images, reference videos, and sketches

## Run

From the project root:

```bash
uvicorn service.api:app --host 0.0.0.0 --port 8000
```

## Endpoints

### Health

```text
GET /health
```

### Environment check

```text
GET /system/check
```

Useful query parameters:

- `config_yaml`
- `generation_backend`
- `backend_workdir`
- `backend_command`
- `perception_model`

### List tasks

```text
GET /tasks
```

### Get task status

```text
GET /tasks/{task_id}
```

### Submit a task

```text
POST /tasks
```

This endpoint accepts multipart form data. Useful fields include:

- `prompt`
- `config_yaml`
- `simulation_name`
- `generation_backend`
- `backend_command`
- `backend_workdir`
- `closed_loop`
- `target_score`
- `max_attempts`
- `evaluator_type`
- `long_tail_scenarios`
- `weather_strength`
- `openai_api_key`
- `audio_files`
- `reference_images`
- `reference_videos`
- `reference_sketches`

## Notes

- The queue runs one task at a time by default, which is safer for a single GPU deployment.
- Uploaded files are stored under `results/service_uploads`.
- Task states are persisted under `results/service_tasks`.
