import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from driveloop.backends.drivedreamer2 import DriveDreamer2Backend
from driveloop.backends.mock import MockGenerationBackend
from driveloop.evaluators import RuleBasedEvaluator
from driveloop.intent.adapter import MultimodalInputBundle, RuleBasedIntentAdapter
from driveloop.intent.providers import AudioTranscriptionProvider, WhisperAudioTranscriptionProvider
from driveloop.runner import DriveLoopConfig, DriveLoopRequest, DriveLoopRunner


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    scenario_id: Optional[str] = None
    max_iterations: int = Field(default=2, ge=1, le=5)
    target_score: float = Field(default=0.9, ge=0.0, le=1.0)
    backend: str = Field(default="mock", pattern="^(mock|drivedreamer2)$")
    intent_backend: str = Field(default="rule_based", pattern="^rule_based$")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HistoryRecord(BaseModel):
    iteration: int
    generation: Dict[str, Any]
    evaluation: Dict[str, Any]


class GenerateResponse(BaseModel):
    scenario_id: str
    accepted: bool
    best_score: float
    iterations: int
    output_dir: str
    best_generation: Dict[str, Any]
    best_evaluation: Dict[str, Any]
    history: List[HistoryRecord]


class TranscribeResponse(BaseModel):
    transcript: str
    backend: str
    status: str
    language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


_asr_provider_override: Optional[AudioTranscriptionProvider] = None


def set_asr_provider_for_testing(provider: Optional[AudioTranscriptionProvider]) -> None:
    global _asr_provider_override
    _asr_provider_override = provider


def _get_asr_provider() -> AudioTranscriptionProvider:
    return _asr_provider_override or WhisperAudioTranscriptionProvider()



app = FastAPI(title="DriveLoop API", version="0.1.0")


def _to_dict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {"value": obj}


def _history_path(scenario_id: str) -> Path:
    return Path("outputs/driveloop/api") / scenario_id / "history.jsonl"


def _read_history_records(scenario_id: str) -> List[Dict[str, Any]]:
    history_path = _history_path(scenario_id)
    if not history_path.exists():
        raise HTTPException(status_code=404, detail=f"History not found for scenario_id: {scenario_id}")

    records = [
        json.loads(line)
        for line in history_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise HTTPException(status_code=404, detail=f"History is empty for scenario_id: {scenario_id}")
    return records


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "driveloop-api",
    }


@app.get("/history/{scenario_id}")
def get_history(scenario_id: str):
    records = _read_history_records(scenario_id)
    history_path = _history_path(scenario_id)

    return {
        "scenario_id": scenario_id,
        "history_path": str(history_path),
        "iterations": len(records),
        "history": records,
    }


@app.get("/artifacts/{scenario_id}/{filename}")
def get_artifact(scenario_id: str, filename: str):
    records = _read_history_records(scenario_id)

    for record in records:
        artifacts = record.get("generation", {}).get("artifacts", {})
        for artifact_path in artifacts.values():
            path = Path(artifact_path)
            if path.name == filename and path.exists():
                return FileResponse(path)

    raise HTTPException(status_code=404, detail=f"Artifact not found: {filename}")


@app.get("/summary/{scenario_id}")
def get_summary(scenario_id: str):
    records = _read_history_records(scenario_id)
    best_record = max(
        records,
        key=lambda record: record.get("evaluation", {}).get("score", 0.0),
    )

    generation = best_record.get("generation", {})
    evaluation = best_record.get("evaluation", {})
    metadata = generation.get("metadata", {})
    artifacts = generation.get("artifacts", {})

    artifact_urls = {
        name: f"/artifacts/{scenario_id}/{Path(artifact_path).name}"
        for name, artifact_path in artifacts.items()
    }

    condition_trace = {
        "scene_specification": metadata.get("scene_specification"),
        "long_tail_condition_plan": metadata.get("long_tail_condition_plan"),
        "dd2_condition": metadata.get("dd2_condition"),
    }

    request_path = Path("outputs/driveloop/api") / scenario_id / "request.json"
    request_record = {}
    if request_path.exists():
        request_record = json.loads(request_path.read_text(encoding="utf-8"))

    return {
        "scenario_id": scenario_id,
        "iterations": len(records),
        "best_score": evaluation.get("score", 0.0),
        "accepted": evaluation.get("diagnosis", {}).get("passed", False),
        "backend": metadata.get("backend"),
        "intent_backend": request_record.get("intent_backend", "rule_based"),
        "prompt": generation.get("prompt"),
        "artifacts": artifact_urls,
        "condition_trace": condition_trace,
        "diagnosis": evaluation.get("diagnosis", {}),
        "multimodal_inputs": request_record.get("metadata", {}),
        "structured_intent": request_record.get("structured_intent", {}),
    }


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_voice(audio: UploadFile = File(...)):
    suffix = Path(audio.filename or "voice_prompt.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(prefix="driveloop_voice_", suffix=suffix, delete=True) as tmp:
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded audio is empty")
        tmp.write(content)
        tmp.flush()

        try:
            result = _get_asr_provider().transcribe_file(
                Path(tmp.name),
                content_type=audio.content_type,
                filename=audio.filename,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return TranscribeResponse(
        transcript=result.transcript,
        backend=result.backend,
        status=result.status,
        language=result.language,
        metadata=result.metadata,
    )



@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    scenario_id = request.scenario_id or f"api_{uuid4().hex[:8]}"
    output_dir = Path("outputs/driveloop/api") / scenario_id
    output_dir.mkdir(parents=True, exist_ok=True)

    structured_intent = RuleBasedIntentAdapter().parse_bundle(
        MultimodalInputBundle(
            text=request.prompt,
            metadata=request.metadata,
        )
    ).to_dict()

    request_record = {
        "scenario_id": scenario_id,
        "prompt": request.prompt,
        "backend": request.backend,
        "intent_backend": request.intent_backend,
        "metadata": request.metadata,
        "structured_intent": structured_intent,
    }
    (output_dir / "request.json").write_text(
        json.dumps(request_record, indent=2),
        encoding="utf-8",
    )

    config = DriveLoopConfig(
        max_iterations=request.max_iterations,
        target_score=request.target_score,
        output_dir=output_dir,
    )

    if request.backend == "mock":
        backend = MockGenerationBackend()
    elif request.backend == "drivedreamer2":
        backend = DriveDreamer2Backend(timeout_seconds=1800)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported backend: {request.backend}")

    runner = DriveLoopRunner(
        backend=backend,
        evaluator=RuleBasedEvaluator(),
        config=config,
    )

    runner_metadata = {
        **request.metadata,
        "intent_backend": request.intent_backend,
        "structured_intent": structured_intent,
    }

    result = runner.run(
        DriveLoopRequest(
            prompt=request.prompt,
            scenario_id=scenario_id,
            metadata=runner_metadata,
        )
    )

    best_evaluation = _to_dict(result.best_evaluation)
    history = [
        HistoryRecord(
            iteration=index,
            generation=_to_dict(generation),
            evaluation=_to_dict(evaluation),
        )
        for index, (generation, evaluation) in enumerate(result.history)
    ]

    return GenerateResponse(
        scenario_id=scenario_id,
        accepted=best_evaluation.get("score", 0.0) >= request.target_score,
        best_score=best_evaluation.get("score", 0.0),
        iterations=len(result.history),
        output_dir=str(output_dir),
        best_generation=_to_dict(result.best_generation),
        best_evaluation=best_evaluation,
        history=history,
    )
