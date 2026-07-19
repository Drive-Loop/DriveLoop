"""Tests for summarize_closed_loop (open loop vs best attempt). No GPU."""

from __future__ import annotations

import json

import scripts.summarize_closed_loop as summ


def _write_attempts(path, attempts):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(a) for a in attempts) + "\n", encoding="utf-8")


def test_summarize_case_open_vs_best(tmp_path):
    ap = tmp_path / "m1" / "attempts.jsonl"
    _write_attempts(ap, [
        {"iteration": 0, "evaluation": {"score": 0.50, "metrics": {"S_perc": 0.40}}},
        {"iteration": 1, "evaluation": {"score": 0.59, "metrics": {"S_perc": 0.46}}},
        {"iteration": 2, "evaluation": {"score": 0.57, "metrics": {"S_perc": 0.44}}},
    ])
    summary = summ.summarize_case(ap)
    assert summary["open"]["S_perc"] == 0.40
    assert summary["best"]["S_perc"] == 0.46
    assert summary["best"]["iteration"] == 1
    assert summary["n_attempts"] == 3


def test_summarize_case_missing(tmp_path):
    assert summ.summarize_case(tmp_path / "nope" / "attempts.jsonl") is None


def test_build_report_and_mean_uplift(tmp_path, capsys):
    _write_attempts(tmp_path / "m1" / "attempts.jsonl", [
        {"iteration": 0, "evaluation": {"score": 0.5, "metrics": {"S_perc": 0.40}}},
        {"iteration": 1, "evaluation": {"score": 0.6, "metrics": {"S_perc": 0.50}}},
    ])
    _write_attempts(tmp_path / "m2" / "attempts.jsonl", [
        {"iteration": 0, "evaluation": {"score": 0.2, "metrics": {"S_perc": 0.10}}},
        {"iteration": 1, "evaluation": {"score": 0.2, "metrics": {"S_perc": 0.10}}},
    ])
    report = summ.build_report(tmp_path, ["m1", "m2"])
    summ.print_report(report)
    out = capsys.readouterr().out
    assert "mean S_perc uplift over 2 cases: +0.0500" in out
