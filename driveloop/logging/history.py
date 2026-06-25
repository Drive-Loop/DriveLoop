from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from driveloop.schema import Evaluation, Generation


class HistoryLogger:
    def __init__(self, output_dir: str | Path, append: bool = False) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.output_dir / "history.jsonl"
        if not append and self.path.exists():
            self.path.unlink()

    def write(self, generation: Generation, evaluation: Evaluation) -> None:
        record = {
            "generation": asdict(generation),
            "evaluation": asdict(evaluation),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
