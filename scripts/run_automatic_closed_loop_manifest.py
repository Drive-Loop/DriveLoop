from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from driveloop.automatic_closed_loop_manifest import build_automatic_closed_loop_manifest, load_history_jsonl


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a DriveLoop automatic closed-loop manifest.")
    parser.add_argument("--history-jsonl", type=Path, default=None)
    parser.add_argument("--case-summary", type=Path, default=None)
    parser.add_argument("--target-score", type=float, default=0.8)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    if args.history_jsonl:
        payload = load_history_jsonl(args.history_jsonl)
        source = str(args.history_jsonl)
    elif args.case_summary:
        payload = load_json(args.case_summary)
        source = str(args.case_summary)
    else:
        raise SystemExit("provide --history-jsonl or --case-summary")

    manifest = build_automatic_closed_loop_manifest(payload, target_score=args.target_score, source=source)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
