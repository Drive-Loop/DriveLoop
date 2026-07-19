#!/usr/bin/env python
"""Summarize a closed-loop experiment run: per case, attempt 0 (the open-loop
single pass) versus the best attempt (the closed loop's kept result).

Reads each case's attempts.jsonl and reports S_perc and J (the task-utility
score) for the open-loop attempt and the best attempt, with the uplift. Best is
chosen by S_perc. This is analysis only; it renders nothing and changes no state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _rows_from_attempts(attempts_path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line in attempts_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        attempt = json.loads(line)
        evaluation = attempt.get("evaluation", {}) or {}
        metrics = evaluation.get("metrics", {}) or {}
        rows.append({
            "iteration": attempt.get("iteration"),
            "J": evaluation.get("score"),
            "S_perc": metrics.get("S_perc"),
            "S_ctrl": metrics.get("S_ctrl"),
        })
    return rows


def summarize_case(attempts_path: Path) -> Optional[Dict[str, Any]]:
    if not attempts_path.exists():
        return None
    rows = _rows_from_attempts(attempts_path)
    if not rows:
        return None
    open_row = rows[0]  # attempt 0 is the open-loop single pass
    best_row = max(rows, key=lambda r: (r["S_perc"] if r["S_perc"] is not None else -1.0))
    return {"open": open_row, "best": best_row, "n_attempts": len(rows), "rows": rows}


def build_report(run_dir: Path, cases: List[str]) -> Dict[str, Any]:
    case_reports = {}
    for case in cases:
        case_reports[case] = summarize_case(run_dir / case / "attempts.jsonl")
    return {"run_dir": str(run_dir), "cases": case_reports}


def _fmt(value: Any) -> float:
    return float(value) if value is not None else 0.0


def print_report(report: Dict[str, Any]) -> None:
    print("run_dir=%s" % report["run_dir"])
    print("  %-30s %8s %8s %9s   %8s %8s %6s"
          % ("case", "open_Sp", "best_Sp", "dSp", "open_J", "best_J", "best@"))
    deltas = []
    for case, summary in report["cases"].items():
        if summary is None:
            print("  %-30s (no attempts)" % case)
            continue
        open_row, best_row = summary["open"], summary["best"]
        open_sp, best_sp = _fmt(open_row["S_perc"]), _fmt(best_row["S_perc"])
        deltas.append(best_sp - open_sp)
        print("  %-30s %8.4f %8.4f %+9.4f   %8.4f %8.4f  %d/%d"
              % (case, open_sp, best_sp, best_sp - open_sp,
                 _fmt(open_row["J"]), _fmt(best_row["J"]),
                 best_row["iteration"], summary["n_attempts"]))
    if deltas:
        print("  mean S_perc uplift over %d cases: %+.4f" % (len(deltas), sum(deltas) / len(deltas)))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a closed-loop run: open loop vs best attempt.")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--cases", nargs="+", required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    report = build_report(args.run_dir, args.cases)
    print_report(report)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
